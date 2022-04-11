"""
Utilities for parsing Github markdown files, specifically files from
https://github.com/awsdocs/aws-cloudformation-user-guide.

Example: https://raw.githubusercontent.com/awsdocs/aws-cloudformation-user-guide/main/doc_source/aws-properties-ec2-instance.md
"""


import asyncio
import re
from dataclasses import dataclass
from itertools import dropwhile
from itertools import takewhile
from typing import Dict
from typing import List

import aiohttp
from aiohttp import ClientSession
from aiohttp import StreamReader

from ..properties import AWSResource


class GithubCfnMarkdownParser:
    """Class for parsing cfn github content."""

    HEADER_REGEX = re.compile("^`([a-zA-Z0-9]+)`.*<a*.a>")
    PROPERTY_LINE_PREFIX = "## Properties"
    PROPERTY_END_PREFIX = "## Return values"

    async def parse(self, session: ClientSession, url: str) -> AWSResource:
        async with session.get(url) as response:
            status = response.status
            assert response.status == 200
            return await self.parse_response(response.content)

    async def parse_response(self, content: StreamReader) -> AWSResource:
        first_line = await content.readline()
        name = takewhile(
            lambda c: c != "<",
            dropwhile(lambda c: not c.isalpha(), first_line.decode("utf-8")),
        )
        async for line in content:
            if line.decode("utf-8").startswith(self.PROPERTY_LINE_PREFIX):
                break
        result, prop, desc = {}, None, ""
        async for line in content:
            line = line.decode("utf-8")
            match = re.match(self.HEADER_REGEX, line)
            if match:
                if prop:
                    result[prop] = desc
                prop, desc = match.group(1), f"`{match.group(1)}`\n"
            elif line.startswith(self.PROPERTY_END_PREFIX):
                break
            else:
                desc += line
        result[prop] = desc
        return AWSResource("".join(name), result)


async def parse_urls(urls: List[str]) -> List[AWSResource]:
    parser = GithubCfnMarkdownParser()
    async with aiohttp.ClientSession() as session:
        resources = await asyncio.gather(*[parser.parse(session, url) for url in urls])
        return {res.name: res for res in resources}
