"""
Completion logic.
"""
from pygls.lsp.types import CompletionItem
from pygls.lsp.types import CompletionList
from pygls.lsp.types import Position
from pygls.workspace import Document

from ..aws_data import AWSContext
from ..aws_data import AWSPropertyName
from ..aws_data import Tree
from ..decode.extractors import ResourceExtractor
from ..decode.extractors import ResourcePropertyExtractor
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
        return property_completions(prop_span.value, aws_context)
    return intrinsic_function_completions(document, position)


def property_completions(
    name: AWSPropertyName, aws_context: AWSContext
) -> CompletionList:
    return CompletionList(
        is_incomplete=False,
        items=[
            CompletionItem(
                label=s, documentation=aws_context.description(name.parent / s)
            )
            for s in aws_context.same_level(name)
        ],
    )
