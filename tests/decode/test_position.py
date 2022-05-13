import pytest


from cfn_lsp_extra.decode.position import PositionLookup
from cfn_lsp_extra.decode.position import Spanning


def test_lookup_at():
    lookup = PositionLookup[str]()
    item = "foo"
    line, char, span = [1, 10, 3]
    lookup[item].append([line, char, span])
    assert lookup.at(1, 11) == Spanning[str](
        value=item, line=line, char=char, span=span
    )


def test_lookup_at_empty_position():
    lookup = PositionLookup[str]()
    assert lookup.at(1, 1) is None


def test_lookup_extend_with_appends():
    lookup1 = PositionLookup[str]()
    lookup2 = PositionLookup[str]()
    item = "foo"
    line, char, span = [1, 10, 3]
    lookup1[item].append([line, char, span])
    lookup2[item].append([line + 1, char, span])
    lookup1.extend_with_appends(lookup2)
    assert lookup1.at(1, 11) == Spanning[str](
        value=item, line=line, char=char, span=span
    )
    assert lookup1.at(2, 11) == Spanning[str](
        value=item, line=line + 1, char=char, span=span
    )
