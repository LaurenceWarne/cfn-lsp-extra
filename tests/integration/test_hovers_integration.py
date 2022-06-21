"""
Integration tests for hovers.
"""
import pytest
from pygls.lsp.methods import HOVER
from pygls.lsp.types import HoverParams
from pygls.lsp.types.basic_structures import Position
from pygls.lsp.types.basic_structures import TextDocumentIdentifier
from pygls.lsp.types.language_features.hover import Hover


# See
# https://docs.pytest.org/en/latest/example/markers.html#marking-whole-classes-or-modules
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_property_hover(client):
    test_uri = client.root_uri + "/template.yaml"
    result = await client.lsp.send_request_async(
        HOVER,
        HoverParams(
            text_document=TextDocumentIdentifier(uri=test_uri),
            position=Position(line=57, character=8),
        ),
    )
    assert "Bucket" in Hover(**result).contents.value


@pytest.mark.asyncio
async def test_resource_hover(client):
    test_uri = client.root_uri + "/template.yaml"
    result = await client.lsp.send_request_async(
        HOVER,
        HoverParams(
            text_document=TextDocumentIdentifier(uri=test_uri),
            position=Position(line=54, character=10),
        ),
    )
    assert "AWS::S3::BucketPolicy" in Hover(**result).contents.value


@pytest.mark.asyncio
async def test_nested_property_hover(client):
    test_uri = client.root_uri + "/template.yaml"
    result = await client.lsp.send_request_async(
        HOVER,
        HoverParams(
            text_document=TextDocumentIdentifier(uri=test_uri),
            position=Position(line=47, character=8),
        ),
    )
    assert "DestinationBucketName" in Hover(**result).contents.value
