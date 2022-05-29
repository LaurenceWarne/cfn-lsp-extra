"""
Utilities for parsing Github markdown files, specifically files from
https://github.com/awsdocs/aws-cloudformation-user-guide.

Example: https://raw.githubusercontent.com/awsdocs/aws-cloudformation-user-guide/main/doc_source/aws-properties-ec2-instance.md

Markdown files for a resource are expected to be in the format:

# resource_name

resource_description

# ...
.
.
.

# Properties

`property1`

property1 description

`property2`
.
.
.
# ... 
"""  # noqa
from __future__ import annotations

import logging
import re
import textwrap
from abc import ABC
from abc import abstractmethod
from itertools import dropwhile
from itertools import takewhile
from typing import Callable
from typing import List
from typing import Optional
from typing import Pattern
from typing import Tuple
from typing import TypeVar

import aiohttp
from aiohttp import ClientSession
from aiohttp import StreamReader
from aiohttp.client import ClientTimeout
from aiohttp.client import ServerTimeoutError
from tqdm.asyncio import tqdm_asyncio  # type: ignore[import]

from cfn_lsp_extra.aws_data import AWSResourceName

from ..aws_data import AWSContext
from ..aws_data import AWSName
from ..aws_data import AWSPropertyName
from ..aws_data import Tree
from .markdown_textwrapper import MarkdownTextWrapper


logger = logging.getLogger(__name__)
T = TypeVar("T")


class BaseCfnDocParser(ABC):

    HEADER_REGEX: Pattern[str] = re.compile(r"^`([a-zA-Z0-9]+)`.*<a*.a>")
    SUB_PROP_REGEX: Pattern[str] = re.compile(r"^\*Type\*:.*\[(.*)\]\((.*\.md)\)")
    PROPERTY_LINE_PREFIX = "## Properties"
    PROPERTY_END_PREFIX = "## Return values"
    TEXT_WRAPPER = MarkdownTextWrapper(
        width=79,
        break_long_words=True,
        replace_whitespace=False,
    )

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.ignore_condition: Callable[[AWSPropertyName], bool] = (
            lambda prop_name: "Condition" in prop_name or "Rules" in prop_name
        )

    @abstractmethod
    def subproperty_parser(self, base_url: str, name: AWSName) -> BaseCfnDocParser:
        ...

    @abstractmethod
    async def parse_name(self, content: StreamReader) -> Optional[AWSName]:
        ...

    @abstractmethod
    def build_object(
        self,
        name: AWSName,
        description: str,
        properties: Tree,
    ) -> Optional[Tree]:
        ...

    async def parse(
        self, session: ClientSession, url: str, retry: bool = True
    ) -> Optional[Tree]:
        try:
            async with session.get(
                url, timeout=ClientTimeout(total=None, sock_connect=5, sock_read=5)
            ) as response:
                assert response.status == 200
                raw = await self.parse_response_raw(response.content, url, session)
                if raw:
                    name, description, properties = raw
                    return self.build_object(name, description, properties)
                else:
                    return None
        except ServerTimeoutError as e:
            if retry:
                logger.info(f"Timeout for {url}, retrying")
                return await self.parse(session, url, False)
            else:
                raise e

    async def parse_response_raw(
        self, content: StreamReader, url: str, session: ClientSession
    ) -> Optional[Tuple[AWSName, str, Tree]]:
        name = await self.parse_name(content)
        if not name:
            return None
        description = await self.parse_description(content, name)
        async for line_b in content:
            if line_b.decode("utf-8").startswith(self.PROPERTY_LINE_PREFIX):
                break

        # Parse all properties
        subprop: Tree
        properties, prop_name, desc, subprop, required = {}, None, "", {}, False
        async for line_b in content:
            line = re.sub(r"[ \t]+(\n|\Z)", r"\1", line_b.decode("utf-8"))
            match = re.match(self.HEADER_REGEX, line)
            if match:
                if prop_name:
                    properties[prop_name.property_] = {  # type: ignore[unreachable]
                        "description": self.format_description(desc),
                        "required": required,
                        "properties": subprop["properties"] if subprop else {},
                    }
                prop_name, desc = name / match.group(1), f"`{match.group(1)}`\n"
                subprop, required = {}, False
            elif line.startswith(self.PROPERTY_END_PREFIX):
                break
            else:
                subprop_match = re.match(self.SUB_PROP_REGEX, line)
                if subprop_match:
                    sub_url = f"{self.base_url}/{subprop_match.group(2)}"
                    subprop = await self.parse_subproperty(
                        session, prop_name, sub_url  # type: ignore[arg-type]
                    )
                required |= line.startswith("*Required*: Yes")
                desc += line

        if prop_name is None:
            logger.info(f"Skipping {name} since no properties were found")
            return None
        properties[prop_name.property_] = {
            "description": self.format_description(desc),
            "required": required,
            "properties": subprop["properties"] if subprop else {},
        }
        return name, self.format_description(description), properties

    async def parse_subproperty(
        self, session: ClientSession, property_name: AWSPropertyName, url: str
    ) -> Optional[Tree]:
        logger.info(f"parsing {property_name}")
        if self.ignore_condition(property_name):
            return None
        else:
            parser = self.subproperty_parser(self.base_url, property_name)
            return await parser.parse(session, url)

    async def parse_description(self, content: StreamReader, name: AWSName) -> str:
        description = f"# {name}\n"
        async for line_b in content:
            line = line_b.decode("utf-8")
            if line.startswith("#"):
                break
            else:
                description += line
        return description

    def format_description(self, description: str) -> str:
        first_line, *rest = description.splitlines()
        body = ""
        for line in filter(lambda l: l.strip(), rest):
            if line.startswith("*Allowed"):
                line = textwrap.shorten(line, width=200)
                line += "`" if line.count("`") == 1 else ""
            body += "\n".join(self.TEXT_WRAPPER.wrap(line)) + "\n"
        return f"{first_line}\n{body}\n"


class CfnResourceDocParser(BaseCfnDocParser):
    """Class for parsing cfn github content."""

    def subproperty_parser(self, base_url: str, name: AWSName) -> BaseCfnDocParser:
        return CfnPropertyDocParser(base_url, name)

    async def parse_name(self, content: StreamReader) -> Optional[AWSName]:
        first_line = await content.readline()
        init = dropwhile(lambda c: not c.isalpha(), first_line.decode("utf-8"))
        name = "".join(takewhile(lambda c: c != "<", init)).rstrip()
        if " " in name:
            return None  # It's a property (= "myresource myproperty")
        return AWSResourceName(value=name)

    def build_object(
        self,
        name: AWSName,
        description: str,
        properties: Tree,
    ) -> Optional[Tree]:
        return {"name": str(name), "description": description, "properties": properties}


class CfnPropertyDocParser(BaseCfnDocParser):
    """Class for parsing cfn github content."""

    def __init__(self, base_url: str, name: AWSName, max_depth: int = 8):
        super().__init__(base_url)
        self.name = name
        self.max_depth = max_depth

    def subproperty_parser(self, base_url: str, name: AWSName) -> BaseCfnDocParser:
        return CfnPropertyDocParser(base_url, name, self.max_depth - 1)

    async def parse_name(self, content: StreamReader) -> Optional[AWSName]:
        await content.readline()
        return self.name

    async def parse_subproperty(
        self, session: ClientSession, property_name: AWSPropertyName, url: str
    ) -> Optional[Tree]:
        if self.max_depth > 0:
            return await super().parse_subproperty(session, property_name, url)
        else:
            return None

    def build_object(
        self,
        name: AWSName,
        description: str,
        properties: Tree,
    ) -> Optional[Tree]:
        return {"description": description, "properties": properties}


BASE_URL = "https://raw.githubusercontent.com/awsdocs/aws-cloudformation-user-guide/main/doc_source/"  # noqa


async def parse_urls(urls: List[str], base_url: str = BASE_URL) -> AWSContext:
    parser = CfnResourceDocParser(base_url)
    async with aiohttp.ClientSession() as session:
        resources = await tqdm_asyncio.gather(
            *[parser.parse(session, url) for url in urls]
        )
        return AWSContext(
            resources={
                res["name"]: {
                    "description": res["description"],
                    "properties": res["properties"],
                }
                for res in resources
                if res
            }
        )
