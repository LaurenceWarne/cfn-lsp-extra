from __future__ import annotations

from typing import Dict
from typing import Generic
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple
from typing import TypeVar

from pydantic.generics import GenericModel
from pydantic.types import NonNegativeInt


E = TypeVar("E")


class Spanning(GenericModel, Generic[E], arbitrary_types_allowed=True):
    """Enrichment of some object with a location span in a document.

    Attributes
    ----------
    value : E
        The value this span wraps
    line : NonNegativeInt
        Line position marking the start of the span.
    char : NonNegativeInt
        Character position marking the start of the span.
    span : NonNegativeInt
        The length of the span"""

    value: E
    line: NonNegativeInt
    char: NonNegativeInt
    span: NonNegativeInt


T = TypeVar("T")
PositionList = List[Tuple[int, int, int]]


class PositionLookup(Dict[T, PositionList]):
    """A thin wrapper around Dict[T, List[Tuple[int, int, int]]]."""

    def __missing__(self, key: T) -> PositionList:
        self[key] = []
        return self[key]

    def at(self, line: int, char: int) -> Optional[Spanning[T]]:
        for item, positions in self.items():
            for item_line, char_min, item_span in positions:
                char_max = char_min + item_span
                within_col = char_min <= char <= char_max
                if line == item_line and within_col:
                    return Spanning[T](
                        value=item, line=item_line, char=char_min, span=item_span
                    )
        return None

    def extend_with_appends(self, other: PositionLookup[T]) -> None:
        for key, value in other.items():
            self[key].extend(value)

    @classmethod
    def from_iterable(cls, iterable: Iterable[Spanning[T]]) -> PositionLookup[T]:
        lookup: PositionLookup[T] = cls()
        for span in iterable:
            lookup[span.value].append((span.line, span.char, span.span))
        return lookup


ST = TypeVar("ST")
TT = TypeVar("TT")


class PositionLink(GenericModel, Generic[ST, TT], arbitrary_types_allowed=True):
    """The linking of a source object and a target object in a document.

    Attributes
    ----------
    source_span : Spanning[ST]
        The source object
    target_span : Spanning[TT]
        The target object"""

    source_span: Spanning[ST]
    target_span: Spanning[TT]
