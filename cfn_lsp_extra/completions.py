"""
Completion logic.
"""
from typing import Callable
from typing import List

from pygls.lsp.types.language_features.completion import CompletionItem
from pygls.lsp.types.language_features.completion import CompletionList
from pygls.lsp.types.language_features.completion import InsertTextFormat

from .aws_data import AWSContext
from .aws_data import AWSName
from .aws_data import AWSPropertyName
from .aws_data import AWSResourceName


def completions_for(
    name: AWSName, aws_context: AWSContext, document_lines: List[str], current_line: int
) -> CompletionList:
    """Return a list of completion items for name."""
    if isinstance(name, AWSPropertyName):
        return property_completions(name, aws_context)
    else:
        return resource_completions(name, aws_context, document_lines, current_line)


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
    name: AWSResourceName,
    aws_context: AWSContext,
    document_lines: List[str],
    current_line: int,
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
        if (
            current_line == len(document_lines) - 1
            or not document_lines[current_line + 1].strip()
        ):
            insert_text_format = InsertTextFormat.Snippet
        else:
            insert_text_format = None
        items = [
            CompletionItem(
                label=s,
                documentation=get_desc(s),
                insert_text=s.split("::")[-1]
                + (
                    "\n" + resource_snippet(AWSResourceName(value=s), aws_context)
                    if insert_text_format
                    else ""
                ),
                insert_text_format=insert_text_format,
            )
            for s in aws_context.same_level(name)
            if s.startswith("::".join(split[:-1]))
        ]
    return CompletionList(is_incomplete=False, items=items)


def resource_snippet(name: AWSResourceName, aws_context: AWSContext) -> str:
    props = "Properties:\n"
    required_props = (
        p for p, v in aws_context[name]["properties"].items() if v["required"]
    )
    for idx, prop in enumerate(required_props):
        props += f"\t{prop}: ${idx + 1}\n"
    # $0 defines the final tab stop
    props += "\t$0"
    return props
