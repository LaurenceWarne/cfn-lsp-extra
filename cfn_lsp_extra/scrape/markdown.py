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
from itertools import dropwhile
from itertools import takewhile
from typing import List
from typing import Optional
from typing import Pattern
from typing import Tuple

import aiohttp
from aiohttp import ClientSession
from aiohttp import StreamReader
from aiohttp.client import ClientTimeout
from aiohttp.client import ServerTimeoutError
from tqdm.asyncio import tqdm_asyncio  # type: ignore[import]

from ..aws_data import AWSContext
from ..aws_data import AWSResource


logger = logging.getLogger(__name__)


class GithubCfnMarkdownParser:
    """Class for parsing cfn github content."""

    HEADER_REGEX: Pattern[str] = re.compile("^`([a-zA-Z0-9]+)`.*<a*.a>")
    PROPERTY_LINE_PREFIX = "## Properties"
    PROPERTY_END_PREFIX = "## Return values"

    async def parse(
        self, session: ClientSession, url: str, retry: bool = True
    ) -> Optional[AWSResource]:
        try:
            async with session.get(
                url, timeout=ClientTimeout(total=None, sock_connect=5, sock_read=5)
            ) as response:
                assert response.status == 200
                return await self.parse_response(response.content, url)
        except ServerTimeoutError as e:
            if retry:
                logger.info(f"Timeout for {url}, retrying")
                return await self.parse(session, url, False)
            else:
                raise e

    async def parse_response(
        self, content: StreamReader, url: str
    ) -> Optional[AWSResource]:
        maybe_resource = await self.parse_heading(content)
        if maybe_resource:
            name, description = maybe_resource
        else:
            logger.debug(f"{url} appears to point to a property, skipping")
            return None
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
        if prop is None:
            logger.info(f"Skipping {name} since no properties were found")
            return None
        result[prop] = desc
        return AWSResource(
            name=name, description=description, property_descriptions=result
        )

    async def parse_heading(self, content: StreamReader) -> Optional[Tuple[str, str]]:
        first_line = await content.readline()
        init = dropwhile(lambda c: not c.isalpha(), first_line.decode("utf-8"))
        name = "".join(takewhile(lambda c: c != "<", init)).rstrip()
        if " " in name:
            return None  # It's a property (= "myresource myproperty")
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
        return AWSContext(resources={res.name: res for res in resources if res})
