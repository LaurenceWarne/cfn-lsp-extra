"""

"""
import logging
from typing import Optional
from typing import Union

from lsprotocol.types import Hover
from lsprotocol.types import MarkupContent
from lsprotocol.types import MarkupKind
from lsprotocol.types import Position
from lsprotocol.types import Range
from pygls.workspace import Document

from ..aws_data import AWSContext
from ..aws_data import AWSPropertyName
from ..aws_data import AWSResourceName
from ..aws_data import Tree
from ..decode.position import PositionLookup
from ..ref import resolve_ref
from .attributes import attribute_hover


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
            return None
        else:
            char, length = span.char, span.span
            return Hover(
                range=Range(
                    start=Position(line=line_at, character=char),
                    end=Position(line=line_at, character=char + length),
                ),
                contents=MarkupContent(kind=MarkupKind.Markdown, value=documentation),
            )
    # Attempt to resolve it as a Ref
    link = resolve_ref(position, template_data)
    if link:
        documentation = link.source_span.value.as_documentation(aws_context)
        char, length = link.target_span.char, link.target_span.span
        return Hover(
            range=Range(
                start=Position(line=line_at, character=char),
                end=Position(line=line_at, character=char + length),
            ),
            contents=MarkupContent(kind=MarkupKind.Markdown, value=documentation),
        )
    attribute = attribute_hover(template_data, aws_context, document, position)
    if attribute:
        return attribute

    return None
