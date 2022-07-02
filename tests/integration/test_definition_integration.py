"""
Integration tests for textDocument/definition.
"""

import pytest
from pygls.lsp.types import Position


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
    test_uri = client.root_uri + "/" + file_name
    result = await client.definition_request(
        uri=test_uri,
        position=Position(line=ref_line, character=ref_character),
    )
    assert result.range.start.line == param_line
    assert result.range.start.character == param_character
