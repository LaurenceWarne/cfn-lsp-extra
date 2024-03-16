"""
Tests for intrinsic function hovers.
"""
from lsprotocol.types import Position
from pygls.workspace import Document

from cfn_lsp_extra.hovers.functions import intrinsic_function_hover

from .test_refs import document, document_string


def test_function_short_form_hover(document):
    line, char = 15, 23

    result = intrinsic_function_hover(
        document,
        Position(line=line, character=char),
    )

    assert "ImportValue" in result.contents.value


def test_function_short_form_hover_in_list(document):
    line, char = 25, 12

    result = intrinsic_function_hover(
        document,
        Position(line=line, character=char),
    )

    assert "Ref" in result.contents.value


def test_function_full_name_hover(document):
    line, char = 16, 12

    result = intrinsic_function_hover(
        document,
        Position(line=line, character=char),
    )

    assert "Sub" in result.contents.value
