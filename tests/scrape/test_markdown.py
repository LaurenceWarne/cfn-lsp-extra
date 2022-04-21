import aiohttp
import pytest

from cfn_lsp_extra.scrape.markdown import GithubCfnMarkdownParser


async def test_github_parse():
    url = "https://raw.githubusercontent.com/awsdocs/aws-cloudformation-user-guide/main/doc_source/aws-resource-ec2-subnet.md"
    gh_parser = GithubCfnMarkdownParser()
    async with aiohttp.ClientSession() as session:
        resource = await gh_parser.parse(session, url)
    assert resource.name == "AWS::EC2::Subnet"
