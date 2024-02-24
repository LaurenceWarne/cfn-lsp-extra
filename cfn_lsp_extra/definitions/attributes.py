"""
Definitions for !GettAtts.
"""

from typing import Optional

from lsprotocol.types import Location, Position, Range
from pygls.workspace import Document

from ..aws_data import AWSContext, AWSRefName, Tree
from ..decode.extractors import KeyExtractor, LogicalIdExtractor
from ..ref import resolve_ref

ATTRIBUTE_EXTRACTOR = KeyExtractor[AWSRefName](
    "Fn::GetAtt", lambda s: AWSRefName(value=s.split(".")[0])
)
ATTRIBUTE_SRC_EXTRACTOR = LogicalIdExtractor()


def attribute_definition(
    template_data: Tree,
    document: Document,
    position: Position,
    aws_context: AWSContext,
) -> Optional[Location]:
    link = resolve_ref(
        position,
        template_data,
        ref_extractor=ATTRIBUTE_EXTRACTOR,
        ref_src_extractor=ATTRIBUTE_SRC_EXTRACTOR,
    )
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
