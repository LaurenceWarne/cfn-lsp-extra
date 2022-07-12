"""
Logic for handling resource completions.

There are 899 resources in total, which empircally is ok to send to a
client as long as we don't send send the documentation along with the
labels and snippets.
"""
from pygls.lsp.types import CompletionItem
from pygls.lsp.types import CompletionList
from pygls.lsp.types import InsertTextFormat
from pygls.lsp.types import Position
from pygls.workspace import Document

from ..aws_data import AWSContext
from ..aws_data import AWSResourceName
from .cursor import text_edit
from .cursor import word_before_after_position


def resource_completions(
    name: AWSResourceName,
    aws_context: AWSContext,
    document: Document,
    position: Position,
) -> CompletionList:
    """Return a list of all resources, without documentation."""
    use_snippet = not document.filename.endswith("json") and (
        position.line == len(document.lines) - 1
        or not document.lines[position.line + 1].strip()
    )
    before, after = word_before_after_position(document.lines, position)
    items = []
    for r in map(lambda r: r.short_form(), aws_context.same_level(name)):
        if use_snippet:
            insert = r + "\n" + resource_snippet(AWSResourceName(value=r), aws_context)
        else:
            insert = r
        items.append(
            CompletionItem(
                label=r,
                text_edit=text_edit(position, before, after, insert),
                insert_text_format=InsertTextFormat.Snippet if use_snippet else None,
            )
        )
    return CompletionList(is_incomplete=False, items=items)


def resolve_resource_completion_item(
    completion_item: CompletionItem, aws_context: AWSContext
) -> CompletionItem:
    """Enrich a completion_item with documentation."""
    resource_name = AWSResourceName(value=completion_item.label)
    completion_item.documentation = aws_context.description(resource_name)
    return completion_item


def resource_snippet(name: AWSResourceName, aws_context: AWSContext) -> str:
    """Return a snippet appropriate for the resource name using aws_context."""
    props = "Properties:\n"
    required_props = (
        p for p, v in aws_context[name]["properties"].items() if v["required"]
    )
    for idx, prop in enumerate(required_props):
        props += f"\t{prop}: ${idx + 1}\n"
    # $0 defines the final tab stop
    return props + "\t$0"
