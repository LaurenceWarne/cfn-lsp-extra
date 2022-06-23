"""
Integration tests for hovers.
"""
import pytest
from pygls.lsp.methods import HOVER
from pygls.lsp.types import CompletionItem
from pygls.lsp.types import Hover
from pygls.lsp.types import HoverParams
from pygls.lsp.types import Position
from pygls.lsp.types import TextDocumentIdentifier


# See
# https://docs.pytest.org/en/latest/example/markers.html#marking-whole-classes-or-modules
pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "file_name,line,character",
    [
        ("template.yaml", 57, 8),
        ("template.json", 69, 17),
    ],
)
@pytest.mark.asyncio
async def test_property_hover(client, file_name, line, character):
    test_uri = client.root_uri + "/" + file_name
    result = await client.hover_request(
        uri=test_uri,
        position=Position(line=line, character=character),
    )
    assert "Bucket" in result.contents.value


@pytest.mark.parametrize(
    "file_name,line,character",
    [
        ("template.yaml", 54, 10),
        ("template.json", 66, 21),
    ],
)
@pytest.mark.asyncio
async def test_resource_hover(client, file_name, line, character):
    test_uri = client.root_uri + "/" + file_name
    result = await client.hover_request(
        uri=test_uri,
        position=Position(line=line, character=character),
    )
    assert "AWS::S3::BucketPolicy" in result.contents.value


@pytest.mark.parametrize(
    "file_name,line,character",
    [
        ("template.yaml", 46, 8),
        ("template.json", 48, 21),
    ],
)
@pytest.mark.asyncio
async def test_nested_property_hover(client, file_name, line, character):
    test_uri = client.root_uri + "/" + file_name
    result = await client.hover_request(
        uri=test_uri,
        position=Position(line=line, character=character),
    )
    assert "DestinationBucketName" in result.contents.value
