"""
Utilities for parsing Github markdown files, specifically files from
https://github.com/awsdocs/aws-cloudformation-user-guide.

Examples (raw):
https://raw.githubusercontent.com/awsdocs/aws-cloudformation-user-guide/main/doc_source/aws-properties-ec2-instance.md
https://raw.githubusercontent.com/awsdocs/aws-cloudformation-user-guide/main/doc_source/aws-properties-rds-database-instance.md

Examples (rendered):
https://github.com/awsdocs/aws-cloudformation-user-guide/blob/main/doc_source/aws-properties-ec2-instance.md
https://github.com/awsdocs/aws-cloudformation-user-guide/blob/main/doc_source/aws-properties-rds-database-instance.md

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
from typing import Awaitable
from typing import Callable
from typing import Dict
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

from cfn_lsp_extra.aws_data import AWSContextMap

from ..aws_data import AWSName
from ..aws_data import AWSPropertyName
from ..aws_data import AWSResourceName
from ..aws_data import Tree
from .markdown_textwrapper import MarkdownTextWrapper


logger = logging.getLogger(__name__)
T = TypeVar("T")


class PropertyIterator:
    def __init__(
        self,
        content: StreamReader,
        property_start_regex: Pattern[str],
        sub_prop_regex: Pattern[str],
        end_line_prefix: str,
        name: AWSName,
        recurse_fn: Optional[
            Callable[[Optional[AWSName], str], Awaitable[Tree]]
        ] = None,
    ):
        self.content = content
        self.property_start_regex = property_start_regex
        self.sub_prop_regex = sub_prop_regex
        self.end_line_prefix = end_line_prefix
        self.name = name
        self.recurse_fn = recurse_fn
        self._exhausted = False
        self._prop_name: AWSPropertyName = None  # type: ignore[assignment]
        self._desc = ""

    def __aiter__(self) -> PropertyIterator:
        return self

    async def __anext__(self) -> Tuple[AWSPropertyName, str, bool, Tree]:
        if self._exhausted:
            raise StopAsyncIteration
        sub_prop: Tree
        sub_prop, required = {}, False
        async for line_b in self.content:
            line = re.sub(r"[ \t]+(\n|\Z)", r"\1", line_b.decode("utf-8"))
            match = re.match(self.property_start_regex, line)
            if match:
                finished_prop, finished_desc = self._prop_name, self._desc
                self._prop_name = self.name / match.group(1)
                self._desc = f"`{match.group(1)}`\n"
                if finished_prop:
                    return (
                        finished_prop,
                        finished_desc,
                        required,
                        sub_prop["properties"] if sub_prop else {},
                    )
            elif line.startswith(self.end_line_prefix):
                break
            else:
                sub_prop_match = re.match(self.sub_prop_regex, line)
                if sub_prop_match and self.recurse_fn:
                    sub_prop_name = sub_prop_match.group(2)
                    sub_prop = await self.recurse_fn(self._prop_name, sub_prop_name)
                required |= line.startswith("*Required*: Yes")
                self._desc += line

        self._exhausted = True
        if self._prop_name:
            return (
                self._prop_name,
                self._desc,
                required,
                sub_prop["properties"] if sub_prop else {},
            )
        else:
            raise StopAsyncIteration


class BaseCfnDocParser(ABC):

    HEADER_REGEX: Pattern[str] = re.compile(r"^\s*`([a-zA-Z0-9\.]+)`.*<a*.a>")
    SUB_PROP_REGEX: Pattern[str] = re.compile(r"^\*Type\*:.*\[(.*)\]\((.*\.md)\)")
    PROPERTY_LINE_PREFIX = "## Properties"
    PROPERTY_END_PREFIX = "##"
    REF_LINE_PREFIX = "### Ref"
    GETATT_LINE_PREFIX = '#### <a name="aws-properties'
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
    def sub_property_parser(self, base_url: str, name: AWSName) -> BaseCfnDocParser:
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
        return_values: Dict[str, str],
    ) -> Optional[Tree]:
        ...

    async def parse(
        self, session: ClientSession, url: str, retry: bool = True
    ) -> Optional[Tree]:
        try:
            async with session.get(
                url, timeout=ClientTimeout(total=None, sock_connect=5, sock_read=5)
            ) as response:
                response.raise_for_status()
                raw = await self.parse_response_raw(response.content, url, session)
                if raw:
                    name, description, properties, return_values = raw
                    return self.build_object(
                        name, description, properties, return_values
                    )
                else:
                    return None
        except ServerTimeoutError as e:
            if retry:
                logger.debug("Timeout for %s, retrying", url)
                return await self.parse(session, url, False)
            else:
                raise e

    async def parse_response_raw(
        self, content: StreamReader, url: str, session: ClientSession
    ) -> Optional[Tuple[AWSName, str, Tree, Dict[str, str]]]:
        # TODO parse result of intrinsic !Ref
        name = await self.parse_name(content)
        if not name:
            return None
        description = await self.parse_description(content, name)
        async for line_b in content:
            if line_b.decode("utf-8").startswith(self.PROPERTY_LINE_PREFIX):
                break

        prop_it = PropertyIterator(
            content,
            self.HEADER_REGEX,
            self.SUB_PROP_REGEX,
            self.PROPERTY_END_PREFIX,
            name,
            lambda prop_name, sub_prop_name: self.parse_sub_property(
                session,
                prop_name,  # type: ignore[arg-type]
                f"{self.base_url}/{sub_prop_name}",
            ),
        )
        properties = {}
        async for prop_name, desc, required, sub_props in prop_it:
            properties[prop_name.property_] = {
                "description": self.format_description(desc),
                "required": required,
                "properties": sub_props,
            }

        async for line_b in content:
            if line_b.decode("utf-8").startswith(self.GETATT_LINE_PREFIX):
                break
        attr_it = PropertyIterator(
            content,
            self.HEADER_REGEX,
            re.compile("(?!)"),
            self.PROPERTY_END_PREFIX,
            name,
        )
        return_values = {}
        async for prop_name, desc, required, _ in attr_it:
            return_values[prop_name.property_] = self.format_description(desc)

        return name, self.format_description(description), properties, return_values

    async def parse_sub_property(
        self, session: ClientSession, property_name: AWSPropertyName, url: str
    ) -> Optional[Tree]:
        logger.debug("parsing %s", property_name)
        if self.ignore_condition(property_name):
            return None
        else:
            parser = self.sub_property_parser(self.base_url, property_name)
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
        description = re.sub(r"`\[(.*?)\]\((\S+)\)`", r"[`\1`](\2)", description)
        first_line, *rest = description.splitlines()
        body = ""
        for line in filter(lambda l: l.strip(), rest):
            if line.startswith("*Allowed"):
                line = textwrap.shorten(line, width=200)
                line += "`" if line.count("`") == 1 else ""
            body += "\n".join(self.TEXT_WRAPPER.wrap(line)) + "\n"
        return f"{first_line}\n{body}\n"


class CfnResourceDocParser(BaseCfnDocParser):
    """Class for parsing cfn resources from Github content."""

    def sub_property_parser(self, base_url: str, name: AWSName) -> BaseCfnDocParser:
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
        return_values: Dict[str, str],
    ) -> Optional[Tree]:
        return {
            "name": str(name),
            "description": description,
            "properties": properties,
            "return_values": return_values,
        }


class CfnPropertyDocParser(BaseCfnDocParser):
    """Class for parsing cfn properties from Github content."""

    def __init__(self, base_url: str, name: AWSName, max_depth: int = 8):
        super().__init__(base_url)
        self.name = name
        self.max_depth = max_depth

    def sub_property_parser(self, base_url: str, name: AWSName) -> BaseCfnDocParser:
        return CfnPropertyDocParser(base_url, name, self.max_depth - 1)

    async def parse_name(self, content: StreamReader) -> Optional[AWSName]:
        await content.readline()
        return self.name

    async def parse_sub_property(
        self, session: ClientSession, property_name: AWSPropertyName, url: str
    ) -> Optional[Tree]:
        if self.max_depth > 0:
            return await super().parse_sub_property(session, property_name, url)
        else:
            return None

    def build_object(
        self,
        name: AWSName,
        description: str,
        properties: Tree,
        return_values: Dict[str, str],
    ) -> Optional[Tree]:
        return {"description": description, "properties": properties}


BASE_URL = "https://raw.githubusercontent.com/awsdocs/aws-cloudformation-user-guide/main/doc_source"  # noqa
SAM_BASE_URL = "https://raw.githubusercontent.com/awsdocs/aws-sam-developer-guide/main/doc_source"  # noqa


async def parse_urls(urls: List[str], base_url: str = BASE_URL) -> AWSContextMap:
    parser = CfnResourceDocParser(base_url)
    async with aiohttp.ClientSession() as session:
        resources = await tqdm_asyncio.gather(
            *[parser.parse(session, url) for url in urls]
        )
        return AWSContextMap(
            {
                res["name"]: {
                    "description": res["description"],
                    "properties": res["properties"],
                    "return_values": res["return_values"],
                }
                for res in resources
                if res
            }
        )
