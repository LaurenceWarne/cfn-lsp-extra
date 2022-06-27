import pytest
from pygls.lsp.types import Position

from cfn_lsp_extra.aws_data import AWSRefName
from cfn_lsp_extra.ref import resolve_ref

from .decode.test_extractors import document_mapping


@pytest.mark.parametrize(
    "position",
    [
        Position(line=13, character=18),
        Position(line=20, character=13),
        Position(line=23, character=34),
    ],
)
def test_ref_extracts_correct_source_and_target(document_mapping, position):
    result = resolve_ref(position, document_mapping)
    assert result.target_span.value == AWSRefName(value="DefaultVpcId")
    assert result.source_span.value.logical_name == "DefaultVpcId"


def test_ref_extracts_nothing_when_position_not_at_ref(document_mapping):
    position = Position(line=13, character=31)
    result = resolve_ref(position, document_mapping)
    assert result is None
