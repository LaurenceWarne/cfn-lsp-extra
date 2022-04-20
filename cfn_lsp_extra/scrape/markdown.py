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


import asyncio
import re
from dataclasses import dataclass
from itertools import dropwhile
from itertools import takewhile
from typing import Dict
from typing import List
from typing import Pattern
from typing import Tuple

import aiohttp
from aiohttp import ClientSession
from aiohttp import StreamReader
from tqdm.asyncio import tqdm_asyncio  # type: ignore[import]

from ..aws_data import AWSContext
from ..aws_data import AWSResource


class GithubCfnMarkdownParser:
    """Class for parsing cfn github content."""

    HEADER_REGEX: Pattern[str] = re.compile("^`([a-zA-Z0-9]+)`.*<a*.a>")
    PROPERTY_LINE_PREFIX = "## Properties"
    PROPERTY_END_PREFIX = "## Return values"

    async def parse(self, session: ClientSession, url: str) -> AWSResource:
        async with session.get(url) as response:
            assert response.status == 200
            return await self.parse_response(response.content)

    async def parse_response(self, content: StreamReader) -> AWSResource:
        name, description = await self.parse_heading(content)
        async for line_b in content:
            if line_b.decode("utf-8").startswith(self.PROPERTY_LINE_PREFIX):
                break
        result, prop, desc = {}, None, ""
        async for line_b in content:
            line = line_b.decode("utf-8")
            match = re.match(self.HEADER_REGEX, line)
            if match:
                if prop:
                    result[prop] = desc  # type: ignore[unreachable]
                prop, desc = match.group(1), f"`{match.group(1)}`\n"
            elif line.startswith(self.PROPERTY_END_PREFIX):
                break
            else:
                desc += line
        result[prop] = desc
        return AWSResource(
            name=name, description=description, property_descriptions=result
        )

    async def parse_heading(self, content: StreamReader) -> Tuple[str, str]:
        first_line = await content.readline()
        name = "".join(
            takewhile(
                lambda c: c != "<",
                dropwhile(lambda c: not c.isalpha(), first_line.decode("utf-8")),
            )
        )
        description = f"# {name}\n"
        async for line_b in content:
            line = line_b.decode("utf-8")
            if line.startswith("#"):
                break
            else:
                description += line
        return name, description


async def parse_urls(urls: List[str]) -> AWSContext:
    parser = GithubCfnMarkdownParser()
    async with aiohttp.ClientSession() as session:
        resources = await tqdm_asyncio.gather(
            *[parser.parse(session, url) for url in urls]
        )
        return AWSContext(resources={res.name: res for res in resources})
