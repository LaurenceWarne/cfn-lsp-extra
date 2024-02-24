"""
Hovers for !Refs.
"""
from typing import Optional, Union

from lsprotocol.types import Hover, MarkupContent, MarkupKind, Position, Range

from ..aws_data import AWSContext, AWSPropertyName, AWSResourceName, Tree
from ..decode.position import PositionLookup
from ..ref import resolve_ref


def ref_hover(
    template_data: Tree,
    position: Position,
    aws_context: AWSContext,
    position_lookup: PositionLookup[Union[AWSResourceName, AWSPropertyName]],
) -> Optional[Hover]:
    # Attempt to resolve it as a Ref
    link = resolve_ref(position, template_data)
    if link:
        documentation = link.source_span.value.as_documentation(aws_context)
        char, length = link.target_span.char, link.target_span.span
        line_at = position.line
        return Hover(
            range=Range(
                start=Position(line=line_at, character=char),
                end=Position(line=line_at, character=char + length),
            ),
            contents=MarkupContent(kind=MarkupKind.Markdown, value=documentation),
        )
    return None
