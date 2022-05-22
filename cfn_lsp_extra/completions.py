"""
Completion logic.
"""
from typing import Callable

from pygls.lsp.types.language_features.completion import CompletionItem
from pygls.lsp.types.language_features.completion import CompletionList

from .aws_data import AWSContext
from .aws_data import AWSName
from .aws_data import AWSPropertyName
from .aws_data import AWSResourceName


def completions_for(name: AWSName, aws_context: AWSContext) -> CompletionList:
    """Return a list of completion items for name."""
    if isinstance(name, AWSPropertyName):
        return property_completions(name, aws_context)
    else:
        return resource_completions(name, aws_context)


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


def resource_completions(
    name: AWSResourceName, aws_context: AWSContext
) -> CompletionList:
    split = name.value.split("::")
    if len(split) <= 1:
        items = [
            CompletionItem(
                label=res,
                insert_text=res + "::",
            )
            for res in aws_context.resource_prefixes()
        ]
    else:
        get_desc: Callable[[str], str] = lambda s: aws_context.description(
            name.parent / s
        )
        items = [
            CompletionItem(
                label=s, documentation=get_desc(s), insert_text=s.split("::")[-1]
            )
            for s in aws_context.same_level(name)
            if s.startswith("::".join(split[:-1]))
        ]
    return CompletionList(is_incomplete=False, items=items)
