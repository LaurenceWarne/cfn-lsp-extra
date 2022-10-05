"""
Completion logic.
"""
import re

from pygls.lsp.types import CompletionItem
from pygls.lsp.types import CompletionList
from pygls.lsp.types import Position
from pygls.workspace import Document

from ..aws_data import AWSContext
from ..aws_data import AWSPropertyName
from ..aws_data import Tree
from ..decode.extractors import ResourceExtractor
from ..decode.extractors import ResourcePropertyExtractor
from .attributes import attribute_completions
from .cursor import text_edit
from .cursor import word_before_after_position
from .functions import intrinsic_function_completions
from .ref import ref_completions
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
        return resource_completions(res_span.value, aws_context, document, position)
    prop_lookup = ResourcePropertyExtractor().extract(template_data)
    prop_span = prop_lookup.at(line, char)
    if prop_span:
        return property_completions(prop_span.value, aws_context, document, position)
    ref_completions_result = ref_completions(template_data, document, position)
    if ref_completions_result:
        return ref_completions_result
    att_completions_result = attribute_completions(
        template_data, aws_context, document, position
    )
    if att_completions_result:
        return att_completions_result
    return intrinsic_function_completions(document, position)


def property_completions(
    name: AWSPropertyName,
    aws_context: AWSContext,
    document: Document,
    position: Position,
) -> CompletionList:
    if name.parent in aws_context:
        before, after = word_before_after_position(document.lines, position)
        suffix = (
            ": "
            if not re.match(r".*:.*", document.lines[position.line])
            and not document.filename.endswith("json")
            else ""
        )
        return CompletionList(
            is_incomplete=False,
            items=[
                CompletionItem(
                    label=s.short_form(),
                    documentation=aws_context.description(s),
                    text_edit=text_edit(
                        position, before, after, s.short_form() + suffix
                    ),
                )
                for s in aws_context.same_level(name)
            ],
        )
    else:
        return CompletionList(is_incomplete=False, items=[])
