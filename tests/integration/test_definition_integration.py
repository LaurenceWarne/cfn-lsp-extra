"""
Integration tests for textDocument/definition.
"""

import pytest
from pygls.lsp.types import Position


# See
# https://docs.pytest.org/en/latest/example/markers.html#marking-whole-classes-or-modules
pytestmark = pytest.mark.integration


@pytest.mark.skip
@pytest.mark.parametrize(
    "file_name,line,character",
    [
        ("template.yaml", 83, 36),
        ("template.json", 123, 44),
    ],
)
@pytest.mark.asyncio
async def test_parameter_definition(client, file_name, line, character):
    test_uri = client.root_uri + "/" + file_name
    result = await client.definition_request(
        uri=test_uri,
        position=Position(line=line, character=character),
    )
