"""
Definitions for !Refs.
"""

from typing import Optional

from lsprotocol.types import Location, Position, Range
from pygls.workspace import Document

from ..aws_data import AWSContext, Tree
from ..ref import resolve_ref


def ref_definition(
    template_data: Tree,
    document: Document,
    position: Position,
    aws_context: AWSContext,
) -> Optional[Location]:
    link = resolve_ref(position, template_data)
    if link:
        return Location(
            uri=document.uri,
            range=Range(
                start=Position(
                    line=link.source_span.line, character=link.source_span.char
                ),
                end=Position(
                    line=link.source_span.line,
                    character=link.source_span.char + link.source_span.span,
                ),
            ),
        )
    return None
