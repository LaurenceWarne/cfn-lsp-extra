"""
Static completions, e.g. at the top level we can only complete 'AWSTemplateFormatVersion', 'Resources',
etc.
"""
from typing import Optional

from lsprotocol.types import CompletionItem, CompletionList, Position
from pygls.workspace import Document

from ..aws_data import AWSContext, Tree
from ..cursor import text_edit, word_before_after_position
from ..decode.extractors import StaticExtractor, StaticPath

# https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-anatomy.html
TOP_LEVEL_ATTRIBUTES = [
    "AWSTemplateFormatVersion",
    "Description",
    "Metadata",
    "Parameters",
    "Rules",
    "Mappings",
    "Conditions",
    "Transform",
    "Resources",
    "Outputs"
]

TOP_LEVEL_PATH = StaticPath.root(StaticPath.MatchAny)

# https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/parameters-section-structure.html
PARAMETER_ATTRIBUTES = [
    "Type",
    "Default",
    "AllowedValues",
    "Description"
]

PARAMETER_PATH = StaticPath.root("Parameters") / StaticPath.MatchAny / StaticPath.MatchAny

RESOURCE_ATTRIBUTES = [
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

RESOURCE_PATH = StaticPath.root("Resources") / StaticPath.MatchAny / StaticPath.MatchAny

# https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/outputs-section-structure.html
OUTPUT_ATTRIBUTES = [
    "Description",
    "Value",
    "Export"
]

OUTPUT_PATH = StaticPath.root("Outputs") / StaticPath.MatchAny / StaticPath.MatchAny

STATIC_LOOKUP = {
    TOP_LEVEL_PATH: TOP_LEVEL_ATTRIBUTES,
    PARAMETER_PATH: PARAMETER_ATTRIBUTES,
    RESOURCE_PATH: RESOURCE_ATTRIBUTES,
    OUTPUT_PATH: OUTPUT_ATTRIBUTES
}
STATIC_EXTRACTOR = StaticExtractor(paths=set(STATIC_LOOKUP.keys()))


def static_completions(
    template_data: Tree,
    aws_context: AWSContext,
    document: Document,
    position: Position,
) -> Optional[CompletionList]:
    position_lookup = STATIC_EXTRACTOR.extract(template_data)
    span = position_lookup.at(position.line, position.character)
    if span and span.value in STATIC_LOOKUP:
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
                for s in STATIC_LOOKUP[span.value]
            ],
        )
    return None


