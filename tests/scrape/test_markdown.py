import aiohttp
import pytest

from cfn_lsp_extra.aws_data import AWSPropertyName
from cfn_lsp_extra.aws_data import AWSResourceName
from cfn_lsp_extra.scrape.markdown import BASE_URL
from cfn_lsp_extra.scrape.markdown import CfnPropertyDocParser
from cfn_lsp_extra.scrape.markdown import CfnResourceDocParser


async def test_github_parse():
    url = "https://raw.githubusercontent.com/awsdocs/aws-cloudformation-user-guide/main/doc_source/aws-properties-ec2-instance.md"
    gh_parser = CfnResourceDocParser(BASE_URL)
    async with aiohttp.ClientSession() as session:
        resource = await gh_parser.parse(session, url)
    assert resource["name"] == "AWS::EC2::Instance"


async def test_property_parse():
    url = "https://raw.githubusercontent.com/awsdocs/aws-cloudformation-user-guide/main/doc_source/aws-properties-dynamodb-keyschema.md"
    gh_parser = CfnPropertyDocParser(
        base_url=BASE_URL,
        name=AWSResourceName(value="AWS::DynamoDB::Table") / "KeySchema",
    )
    async with aiohttp.ClientSession() as session:
        prop = await gh_parser.parse(session, url)
