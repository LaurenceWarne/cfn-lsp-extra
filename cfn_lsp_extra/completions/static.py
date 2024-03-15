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

TOP_LEVEL_SAM_ATTRIBUTES = [
    "Transform",
    "Globals",
    "Description",
    "Metadata",
    "Parameters",
    "Mappings",
    "Conditions",
    "Resources",
    "Outputs"
]

TOP_LEVEL_SAM_PATH = StaticPath.root(StaticPath.MatchAny)

COMMON_STATIC_LOOKUP = {
    PARAMETER_PATH: PARAMETER_ATTRIBUTES,
    RESOURCE_PATH: RESOURCE_ATTRIBUTES,
    OUTPUT_PATH: OUTPUT_ATTRIBUTES,
    TOP_LEVEL_SAM_PATH: TOP_LEVEL_SAM_ATTRIBUTES,
}
CFN_STATIC_LOOKUP = {**COMMON_STATIC_LOOKUP, TOP_LEVEL_PATH: TOP_LEVEL_ATTRIBUTES}
SAM_STATIC_LOOKUP = {**COMMON_STATIC_LOOKUP, TOP_LEVEL_SAM_PATH: TOP_LEVEL_SAM_ATTRIBUTES}
CFN_EXTRACTOR = StaticExtractor(paths=set(CFN_STATIC_LOOKUP.keys()))
SAM_EXTRACTOR = StaticExtractor(paths=set(SAM_STATIC_LOOKUP.keys()))


def static_completions(
    template_data: Tree,
    aws_context: AWSContext,
    document: Document,
    position: Position,
    use_sam: bool
) -> Optional[CompletionList]:
    lookup, extractor = (SAM_STATIC_LOOKUP, SAM_EXTRACTOR) if use_sam else (CFN_STATIC_LOOKUP, CFN_EXTRACTOR)
    position_lookup = extractor.extract(template_data)
    span = position_lookup.at(position.line, position.character)
    if span and span.value in lookup:
        before, after = word_before_after_position(document, position)
        suffix = "" if (document.filename is not None and document.filename.endswith("json")) else ": "
        return CompletionList(
            is_incomplete=False,
            items=[
                CompletionItem(
                    label=s,
                    text_edit=text_edit(position, before, after, s + suffix)
                )
                for s in lookup[span.value]
            ],
        )
    return None
