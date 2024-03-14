"""
Integration tests for textDocument/completion.
"""
import pytest
from lsprotocol.types import COMPLETION_ITEM_RESOLVE
from lsprotocol.types import CompletionItem
from lsprotocol.types import CompletionParams
from lsprotocol.types import Position
from lsprotocol.types import TextDocumentIdentifier

from .conftest import root_path


# See
# https://docs.pytest.org/en/latest/example/markers.html#marking-whole-classes-or-modules
pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "file_name,line,character",
    [
        ("template.yaml", 149, 10),
        ("template.json", 275, 21),
    ],
)
@pytest.mark.asyncio
async def test_resource_completion(client, file_name, line, character):
    text_document = TextDocumentIdentifier(uri=str(root_path / file_name))

    result = await client.text_document_completion_async(
        CompletionParams(text_document, Position(line=line, character=character))
    )

    labels = [c.label for c in result.items]
    assert "AWS::ACMPCA::Certificate" in labels


@pytest.mark.asyncio
async def test_property_completion(client):
    text_document = TextDocumentIdentifier(uri=str(root_path / "template.yaml"))
    result = await client.text_document_completion_async(
        CompletionParams(text_document, Position(line=57, character=6))
    )

    labels = [c.label for c in result.items]
    assert "Bucket" in labels
    assert "PolicyDocument" in labels

    inserts = [c.text_edit.new_text for c in result.items]
    assert "Bucket: " in inserts
    assert "PolicyDocument: " in inserts 


@pytest.mark.asyncio
async def test_nested_property_completion(client):
    text_document = TextDocumentIdentifier(uri=str(root_path / "template.yaml"))
    result = await client.text_document_completion_async(
        CompletionParams(text_document, Position(line=51, character=8))
    )

    labels = [c.label for c in result.items]
    assert "LogFilePrefix" in labels
    assert "DestinationBucketName" in labels

    inserts = [c.text_edit.new_text for c in result.items]
    assert "LogFilePrefix: " in inserts
    assert "DestinationBucketName: " in inserts


@pytest.mark.asyncio
async def test_start_of_list_property_completion(client):
    text_document = TextDocumentIdentifier(uri=str(root_path / "template.yaml"))
    result = await client.text_document_completion_async(
        CompletionParams(text_document, Position(line=177, character=14))
    )

    labels = [c.label for c in result.items]
    assert "AppProtocol" in labels


@pytest.mark.asyncio
async def test_start_of_item_property_completion(client):
    text_document = TextDocumentIdentifier(uri=str(root_path / "template.yaml"))
    result = await client.text_document_completion_async(
        CompletionParams(text_document, Position(line=182, character=14))
    )

    labels = [c.label for c in result.items]
    assert "ContainerPath" in labels


@pytest.mark.asyncio
async def test_completion_item_resolve_adds_documentation_for_resource(client):
    resource = "AWS::S3::Bucket"
    item = CompletionItem(label=resource)

    result = await client.completion_item_resolve_async(item)
    assert resource in result.documentation.value


@pytest.mark.asyncio
async def test_ref_completion(client):
    text_document = TextDocumentIdentifier(uri=str(root_path / "template.yaml"))
    result = await client.text_document_completion_async(
        CompletionParams(text_document, Position(line=151, character=24))
    )

    labels = [c.label for c in result.items]
    assert "CertificateArn" in labels  # A parameter
    assert "LogBucket" in labels  # A logical id


@pytest.mark.asyncio
async def test_getatt_ref_completion(client):
    text_document = TextDocumentIdentifier(uri=str(root_path / "template.yaml"))
    result = await client.text_document_completion_async(
        CompletionParams(text_document, Position(line=172, character=52))
    )

    labels = [c.label for c in result.items]
    assert "ECSTaskExecutionRole" in labels


@pytest.mark.asyncio
async def test_getatt_attribute_completion(client):
    text_document = TextDocumentIdentifier(uri=str(root_path / "template.yaml"))
    result = await client.text_document_completion_async(
        CompletionParams(text_document, Position(line=172, character=54))
    )

    labels = [c.label for c in result.items]
    assert "Arn" in labels


@pytest.mark.parametrize(
    "file_name,line,character",
    [
        ("template.yaml", 7, 0),
        ("template.json", 3, 5),
    ],
)
@pytest.mark.asyncio
async def test_top_level_completion(client, file_name, line, character):
    text_document = TextDocumentIdentifier(uri=str(root_path / file_name))

    result = await client.text_document_completion_async(
        CompletionParams(text_document, Position(line=line, character=character))
    )

    labels = [c.label for c in result.items]
    assert "Parameters" in labels


@pytest.mark.parametrize(
    "file_name,line,character",
    [
        ("template.yaml", 11, 4),
        ("template.json", 5, 13),
    ],
)
@pytest.mark.asyncio
async def test_parameter_key_completion(client, file_name, line, character):
    text_document = TextDocumentIdentifier(uri=str(root_path / file_name))

    result = await client.text_document_completion_async(
        CompletionParams(text_document, Position(line=line, character=character))
    )

    labels = [c.label for c in result.items]
    assert "Default" in labels


@pytest.mark.parametrize(
    "file_name,line,character",
    [
        ("template.yaml", 131, 4),
        ("template.json", 66, 13),
    ],
)
@pytest.mark.asyncio
async def test_resource_key_completion(client, file_name, line, character):
    text_document = TextDocumentIdentifier(uri=str(root_path / file_name))

    result = await client.text_document_completion_async(
        CompletionParams(text_document, Position(line=line, character=character))
    )

    labels = [c.label for c in result.items]
    assert "CreationPolicy" in labels


@pytest.mark.parametrize(
    "file_name,line,character",
    [
        ("template.yaml", 198, 4),
        ("template.json", 305, 13),
    ],
)
@pytest.mark.asyncio
async def test_output_key_completion(client, file_name, line, character):
    text_document = TextDocumentIdentifier(uri=str(root_path / file_name))

    result = await client.text_document_completion_async(
        CompletionParams(text_document, Position(line=line, character=character))
    )

    labels = [c.label for c in result.items]
    assert "Export" in labels


@pytest.mark.parametrize(
    "file_name,line,character",
    [
        ("template.yaml", 135, 21),
        ("template.json", 244, 38),
    ],
)
@pytest.mark.asyncio
async def test_allowed_value_completion(client, file_name, line, character):
    text_document = TextDocumentIdentifier(uri=str(root_path / file_name))

    result = await client.text_document_completion_async(
        CompletionParams(text_document, Position(line=line, character=character))
    )
    assert "Suspended" in [c.label for c in result.items]


@pytest.mark.parametrize(
    "file_name,line,character",
    [
        ("template.yaml", 35, 10),
        ("template.json", 4, 4),
    ],
)
@pytest.mark.asyncio
async def test_no_completion(client, file_name, line, character):
    text_document = TextDocumentIdentifier(uri=str(root_path / file_name))

    result = await client.text_document_completion_async(
        CompletionParams(text_document, Position(line=line, character=character))
    )
    assert not result.items
