"""

"""
import logging
from typing import Optional, Union

from lsprotocol.types import Hover, MarkupContent, MarkupKind, Position, Range
from pygls.workspace import Document

from ..aws_data import AWSContext, AWSPropertyName, AWSResourceName, Tree
from ..decode.position import PositionLookup
from .attributes import attribute_hover
from .functions import intrinsic_function_hover
from .refs import ref_hover

logger = logging.getLogger(__name__)


def hover(
    template_data: Tree,
    position: Position,
    aws_context: AWSContext,
    document: Document,
    position_lookup: PositionLookup[Union[AWSResourceName, AWSPropertyName]],
) -> Optional[Hover]:
    line_at, char_at = position.line, position.character
    span = position_lookup.at(line_at, char_at)

    if span:
        try:
            documentation = aws_context.description(span.value)
        except KeyError:  # no description for value, e.g. incomplete
            pass
        else:
            char, length = span.char, span.span
            return Hover(
                range=Range(
                    start=Position(line=line_at, character=char),
                    end=Position(line=line_at, character=char + length),
                ),
                contents=MarkupContent(kind=MarkupKind.Markdown, value=documentation),
            )

    for_ref = ref_hover(template_data, position, aws_context, position_lookup)
    if for_ref:
        return for_ref

    for_attribute = attribute_hover(template_data, aws_context, document, position)
    if for_attribute:
        return for_attribute

    for_intrinsic_function = intrinsic_function_hover(document, position)
    if for_intrinsic_function:
        return for_intrinsic_function

    return None
