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


@pytest.mark.asyncio
async def test_property_hover(client):
    test_uri = client.root_uri + "/template.yaml"
    result = await client.hover_request(
        uri=test_uri,
        position=Position(line=57, character=8),
    )
    assert "Bucket" in result.contents.value


@pytest.mark.asyncio
async def test_resource_hover(client):
    test_uri = client.root_uri + "/template.yaml"
    result = await client.hover_request(
        uri=test_uri,
        position=Position(line=54, character=10),
    )
    assert "AWS::S3::BucketPolicy" in result.contents.value


@pytest.mark.asyncio
async def test_nested_property_hover(client):
    test_uri = client.root_uri + "/template.yaml"
    result = await client.hover_request(
        uri=test_uri,
        position=Position(line=47, character=8),
    )
    assert "DestinationBucketName" in result.contents.value
