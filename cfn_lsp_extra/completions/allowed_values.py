"""
Completions for property values.
"""
from typing import Optional

from lsprotocol.types import CompletionItem
from lsprotocol.types import CompletionList
from lsprotocol.types import Position
from pygls.workspace import Document

from ..aws_data import AWSContext
from ..aws_data import Tree
from ..cursor import text_edit
from ..cursor import word_before_after_position
from ..decode.extractors import AllowedValuesExtractor


def allowed_values_completions(
    template_data: Tree,
    aws_context: AWSContext,
    document: Document,
    position: Position,
    allowed_values_extractor: AllowedValuesExtractor,
) -> Optional[CompletionList]:
    lookup = allowed_values_extractor.extract(template_data)
    span = lookup.at(position.line, position.character)
    if span and span.value in aws_context:
        allowed_values = aws_context.allowed_values(span.value)
        before, after = word_before_after_position(document.lines, position)
        items = [
            CompletionItem(
                label=value,
                text_edit=text_edit(position, before, after, value),
            )
            for value in allowed_values
        ]
        return CompletionList(is_incomplete=False, items=items)
    return None
