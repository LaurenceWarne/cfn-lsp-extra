"""
Intrinsic function hovers, see:
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference.html
For more information.
"""
from typing import List, Optional

from lsprotocol.types import Hover, MarkupContent, MarkupKind, Position, Range
from pygls.workspace import Document

from ..cursor import word_before_after_position
from ..intrinsic_functions import INTRINSIC_FUNCTIONS, IntrinsicFunction


def intrinsic_function_hover(
    document: Document,
    position: Position,
    intrinsic_functions: List[IntrinsicFunction] = INTRINSIC_FUNCTIONS,
) -> Optional[Hover]:
    before, after = word_before_after_position(document, position)
    word = before + after

    if word.startswith(("Fn", "fn")):
        fn = next(
            (
                f
                for f in INTRINSIC_FUNCTIONS
                if f.full_name() == word or word.startswith(f.full_name() + ":")
            ),
            None,
        )
    elif word.startswith("!"):
        fn = next((f for f in INTRINSIC_FUNCTIONS if f.short_form() == word), None)
    else:
        return None

    if fn:
        char_start = position.character - len(before)
        return Hover(
            range=Range(
                start=Position(line=position.line, character=char_start),
                end=Position(line=position.line, character=char_start + len(word)),
            ),
            contents=MarkupContent(kind=MarkupKind.Markdown, value=fn.documentation),
        )
    return None
