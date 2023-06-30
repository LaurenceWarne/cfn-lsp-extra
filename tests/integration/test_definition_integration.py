"""
Integration tests for textDocument/definition.
"""

import pytest
from lsprotocol.types import DefinitionParams
from lsprotocol.types import Position
from lsprotocol.types import TextDocumentIdentifier

from .conftest import root_path


# See
# https://docs.pytest.org/en/latest/example/markers.html#marking-whole-classes-or-modules
pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "file_name,ref_line,ref_character,param_line,param_character",
    [
        ("template.yaml", 83, 36, 10, 2),
        ("template.json", 123, 44, 4, 9),
    ],
)
@pytest.mark.asyncio
async def test_parameter_definition(
    client, file_name, ref_line, ref_character, param_line, param_character
):
    text_document = TextDocumentIdentifier(uri=str(root_path / file_name))
    result = await client.text_document_definition_async(
        DefinitionParams(
            text_document=text_document,
            position=Position(line=ref_line, character=ref_character),
        )
    )
    assert result.range.start.line == param_line
    assert result.range.start.character == param_character
