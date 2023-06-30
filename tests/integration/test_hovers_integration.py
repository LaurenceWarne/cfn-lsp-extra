"""
Integration tests for textDocument/Hover.
"""
import pytest
from lsprotocol.types import HoverParams
from lsprotocol.types import Position
from lsprotocol.types import TextDocumentIdentifier

from .conftest import root_path


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
    text_document = TextDocumentIdentifier(uri=str(root_path / file_name))
    result = await client.text_document_hover_async(
        HoverParams(
            text_document=text_document,
            position=Position(line=line, character=character),
        )
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
    text_document = TextDocumentIdentifier(uri=str(root_path / file_name))
    result = await client.text_document_hover_async(
        HoverParams(
            text_document=text_document,
            position=Position(line=line, character=character),
        )
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
    text_document = TextDocumentIdentifier(uri=str(root_path / file_name))
    result = await client.text_document_hover_async(
        HoverParams(
            text_document=text_document,
            position=Position(line=line, character=character),
        )
    )
    assert "DestinationBucketName" in result.contents.value


@pytest.mark.parametrize(
    "file_name,line,character",
    [
        ("template.yaml", 83, 36),
        ("template.json", 123, 44),
    ],
)
@pytest.mark.asyncio
async def test_parameter_ref_hover(client, file_name, line, character):
    text_document = TextDocumentIdentifier(uri=str(root_path / file_name))
    result = await client.text_document_hover_async(
        HoverParams(
            text_document=text_document,
            position=Position(line=line, character=character),
        )
    )
    assert "CertificateArn" in result.contents.value


@pytest.mark.parametrize(
    "file_name,line,character",
    [
        ("template.yaml", 44, 15),
        ("template.json", 33, 18),
    ],
)
@pytest.mark.asyncio
async def test_no_hover(client, file_name, line, character):
    text_document = TextDocumentIdentifier(uri=str(root_path / file_name))
    result = await client.text_document_hover_async(
        HoverParams(
            text_document=text_document,
            position=Position(line=line, character=character),
        )
    )
    assert result is None
