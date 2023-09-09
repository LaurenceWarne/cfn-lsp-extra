"""
Hovers for !Refs.
"""
from typing import Optional
from typing import Union

from lsprotocol.types import Hover
from lsprotocol.types import MarkupContent
from lsprotocol.types import MarkupKind
from lsprotocol.types import Position
from lsprotocol.types import Range

from ..aws_data import AWSContext
from ..aws_data import AWSPropertyName
from ..aws_data import AWSResourceName
from ..aws_data import Tree
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
    else:
        return None
