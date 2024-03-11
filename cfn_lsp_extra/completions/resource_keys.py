"""
Resource key completions
"""
from typing import Optional

from lsprotocol.types import CompletionItem, CompletionList, Position
from pygls.workspace import Document

from ..aws_data import AWSContext, Tree
from ..cursor import text_edit, word_before_after_position
from ..decode.extractors import StaticResourceKeyExtractor

RESOURCE_KEYS = [
    "Type",
    "Properties",
    # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-product-attribute-reference.html
    "CreationPolicy",
    "DeletionPolicy",
    "DependsOn",
    "Metadata",
    "UpdatePolicy",
    "UpdateReplacePolicy"
]
STATIC_RESOURCE_KEY_EXTRACTOR = StaticResourceKeyExtractor()

def resource_key_completions(
    template_data: Tree,
    aws_context: AWSContext,
    document: Document,
    position: Position,
) -> Optional[CompletionList]:
    position_lookup = STATIC_RESOURCE_KEY_EXTRACTOR.extract(template_data)
    span = position_lookup.at(position.line, position.character)
    if span:
        before, after = word_before_after_position(document, position)
        return CompletionList(
            is_incomplete=False,
            items=[
                CompletionItem(
                    label=s,
                    text_edit=text_edit(
                        position, before, after, s
                    ),
                )
                for s in RESOURCE_KEYS
            ],
        )
    return None
