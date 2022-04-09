"""
Utilities for parsing Github markdown files, specifically files from
https://github.com/awsdocs/aws-cloudformation-user-guide.

Example: https://raw.githubusercontent.com/awsdocs/aws-cloudformation-user-guide/main/doc_source/aws-properties-ec2-instance.md
"""


import asyncio
import re

import aiohttp
from aiohttp import ClientSession
from aiohttp import StreamReader


class GithubCfnMarkdownParser:
    """Class for parsing cfn github content."""

    HEADER_REGEX = re.compile("^`[a-zA-Z]+`.*<a*.a>")

    async def parse(self, session: ClientSession, url: str) -> dict[str, str]:
        async with session.get(url) as response:
            status = response.status
            assert response.status == 200
            return await self.parse_response(response.content)

    async def parse_response(self, content: StreamReader) -> dict[str, str]:
        result = {}
        prop, desc = None, ""
        async for line in content:
            line = line.decode("utf-8")
            if re.match(self.HEADER_REGEX, line):
                if prop:
                    result[prop] = desc
                prop, desc = line, ""
            else:
                desc += line
        result[prop] = desc
        return result
