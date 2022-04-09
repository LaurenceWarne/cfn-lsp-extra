import aiohttp
import pytest

from cfn_lsp_extra.scrape.markdown import GithubCfnMarkdownParser


async def test_github_parse():
    url = "https://raw.githubusercontent.com/awsdocs/aws-cloudformation-user-guide/main/doc_source/aws-properties-ec2-instance.md"
    gh_parser = GithubCfnMarkdownParser()
    async with aiohttp.ClientSession() as session:
        result = await gh_parser.parse(session, url)
        print(list(result.values())[0])
    assert False
