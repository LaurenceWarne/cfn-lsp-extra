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


import logging
import re
from abc import ABC
from abc import abstractmethod
from itertools import dropwhile
from itertools import takewhile
from typing import Dict
from typing import Generic
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
from ..aws_data import AWSProperty
from ..aws_data import AWSPropertyName
from ..aws_data import AWSResource


logger = logging.getLogger(__name__)
T = TypeVar("T")


class BaseCfnDocParser(ABC, Generic[T]):

    HEADER_REGEX: Pattern[str] = re.compile(r"^`([a-zA-Z0-9]+)`.*<a*.a>")
    SUB_PROP_REGEX: Pattern[str] = re.compile(r"^\*Type\*:.*\[(.*)\]\((.*\.md)\)")
    PROPERTY_LINE_PREFIX = "## Properties"
    PROPERTY_END_PREFIX = "## Return values"

    def __init__(self, base_url):
        self.base_url = base_url
        self.ignore_condition = (
            lambda prop_name: "Condition" in prop_name or "Rules" in prop_name
        )

    @abstractmethod
    def subproperty_parser(self, base_url: str, name: str):
        ...

    @abstractmethod
    async def parse_name(self, content: StreamReader) -> Optional[AWSName]:
        ...

    @abstractmethod
    def build_object(
        self,
        name: AWSName,
        description: str,
        properties: Dict[str, AWSProperty],
    ) -> Optional[T]:
        ...

    async def parse(
        self, session: ClientSession, url: str, retry: bool = True
    ) -> Optional[T]:
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
    ) -> Optional[Tuple[AWSName, str, Dict[str, AWSProperty]]]:
        name = await self.parse_name(content)
        if not name:
            return None
        description = await self.parse_description(content, name)
        async for line_b in content:
            if line_b.decode("utf-8").startswith(self.PROPERTY_LINE_PREFIX):
                break

        # Parse all properties
        properties, prop_name, desc, subprop = {}, None, "", {}
        async for line_b in content:
            line = line_b.decode("utf-8")
            match = re.match(self.HEADER_REGEX, line)
            if match:
                if prop_name:
                    properties[prop_name.property_] = {
                        "description": desc,
                        "properties": subprop["properties"] if subprop else {},
                    }
                prop_name, desc = name / match.group(1), f"`{match.group(1)}`\n"
                subprop = {}
            elif line.startswith(self.PROPERTY_END_PREFIX):
                break
            else:
                subprop_match = re.match(self.SUB_PROP_REGEX, line)
                if subprop_match:
                    sub_url = f"{self.base_url}/{subprop_match.group(2)}"
                    subprop = await self.parse_subproperty(session, prop_name, sub_url)
                desc += line

        if prop_name is None:
            logger.info(f"Skipping {name} since no properties were found")
            return None
        properties[prop_name.property_] = {
            "description": desc,
            "properties": subprop["properties"] if subprop else {},
        }
        return name, description, properties

    async def parse_subproperty(
        self, session: ClientSession, property_name: AWSPropertyName, url: str
    ) -> Optional[AWSProperty]:
        print(f"parsing {property_name}")
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


class CfnResourceDocParser(BaseCfnDocParser[AWSResource]):
    """Class for parsing cfn github content."""

    def __init__(self, base_url: str):
        super().__init__(base_url)

    def subproperty_parser(self, base_url: str, name: str):
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
        properties: Dict[str, AWSProperty],
    ) -> Optional[AWSResource]:
        return {"name": str(name), "description": description, "properties": properties}


class CfnPropertyDocParser(BaseCfnDocParser[AWSProperty]):
    """Class for parsing cfn github content."""

    def __init__(self, base_url: str, name: AWSName, max_depth: int = 8):
        super().__init__(base_url)
        self.name = name
        self.max_depth = max_depth

    def subproperty_parser(self, base_url: str, name: str):
        return CfnPropertyDocParser(base_url, name, self.max_depth - 1)

    async def parse_name(self, content: StreamReader) -> Optional[AWSName]:
        await content.readline()
        return self.name

    async def parse_subproperty(
        self, session: ClientSession, property_name: AWSPropertyName, url: str
    ) -> Optional[AWSProperty]:
        if self.max_depth > 0:
            return await super().parse_subproperty(session, property_name, url)
        else:
            return None

    def build_object(
        self,
        name: AWSName,
        description: str,
        properties: Dict[str, AWSProperty],
    ) -> Optional[AWSProperty]:
        return {"description": description, "properties": properties}


BASE_URL = "https://raw.githubusercontent.com/awsdocs/aws-cloudformation-user-guide/main/doc_source/"


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
