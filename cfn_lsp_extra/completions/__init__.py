"""
Completion logic.
"""
import re
from typing import Optional

from pygls.lsp.types import CompletionItem
from pygls.lsp.types import CompletionList
from pygls.lsp.types import Position
from pygls.workspace import Document

from ..aws_data import AWSContext
from ..aws_data import AWSPropertyName
from ..aws_data import AWSRefName
from ..aws_data import AWSRefSource
from ..aws_data import Tree
from ..decode.extractors import Extractor
from ..decode.extractors import ResourceExtractor
from ..decode.extractors import ResourcePropertyExtractor
from ..ref import REF_EXTRACTOR
from ..ref import REF_SRC_EXTRACTOR
from .functions import intrinsic_function_completions
from .resources import resource_completions


def completions_for(
    template_data: Tree,
    aws_context: AWSContext,
    document: Document,
    position: Position,
) -> CompletionList:
    """Return a list of completion items for the user's position in document."""
    line, char = position.line, position.character
    resource_lookup = ResourceExtractor().extract(template_data)
    res_span = resource_lookup.at(line, char)
    if res_span:
        return resource_completions(res_span.value, aws_context, document, line)
    prop_lookup = ResourcePropertyExtractor().extract(template_data)
    prop_span = prop_lookup.at(line, char)
    if prop_span:
        return property_completions(prop_span.value, aws_context, document, position)
    ref_completions_result = ref_completions(template_data, position)
    if ref_completions_result:
        return ref_completions_result
    return intrinsic_function_completions(document, position)


def property_completions(
    name: AWSPropertyName,
    aws_context: AWSContext,
    document: Document,
    position: Position,
) -> CompletionList:
    add_colon = not re.match(
        r".*:.*", document.lines[position.line]
    ) and not document.filename.endswith("json")
    return CompletionList(
        is_incomplete=False,
        items=[
            CompletionItem(
                label=s,
                documentation=aws_context.description(name.parent / s),
                insert_text=s + (": " if add_colon else ""),
            )
            for s in aws_context.same_level(name)
        ],
    )


def ref_completions(
    template_data: Tree,
    position: Position,
    ref_extractor: Extractor[AWSRefName] = REF_EXTRACTOR,
    ref_src_extractor: Extractor[AWSRefSource] = REF_SRC_EXTRACTOR,
) -> Optional[CompletionList]:
    ref_lookup = ref_extractor.extract(template_data)
    ref_span = ref_lookup.at(position.line, position.character)
    if ref_span:
        ref_src_lookup = ref_src_extractor.extract(template_data)
        items = [
            CompletionItem(
                label=ref_src.logical_name,
                documentation=ref_src.as_documentation(),
            )
            for ref_src, _ in ref_src_lookup.items()
        ]
        return CompletionList(is_incomplete=False, items=items)
    return None
