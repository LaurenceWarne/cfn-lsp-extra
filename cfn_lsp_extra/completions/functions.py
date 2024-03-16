"""
Intrinsic function completions, see:
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference.html
For more information.
"""
from typing import Callable, List

from lsprotocol.types import CompletionItem, CompletionList, Position
from pygls.workspace import Document

from ..cursor import text_edit, word_before_after_position
from ..intrinsic_functions import INTRINSIC_FUNCTIONS, IntrinsicFunction


def intrinsic_function_completions(
    document: Document,
    position: Position,
    intrinsic_functions: List[IntrinsicFunction] = INTRINSIC_FUNCTIONS,
) -> CompletionList:
    before, after = word_before_after_position(document, position)
    word = before + after
    filter_fn: Callable[[IntrinsicFunction], bool]
    label_fn: Callable[[IntrinsicFunction], str]
    if word.startswith(("Fn", "fn")):
        filter_fn = lambda f: f.full_name_prefix == "Fn::"
        label_fn = lambda f: f.full_name()
    elif word.startswith("!"):
        filter_fn = lambda f: f.short_form_prefix == "!"
        label_fn = lambda f: f.short_form()
    else:
        return CompletionList(is_incomplete=False, items=[])

    items = [
        CompletionItem(
            label=label_fn(f),
            text_edit=text_edit(position, before, after, label_fn(f) + " "),
            documentation=f.documentation,
        )
        for f in intrinsic_functions
        if filter_fn(f)
    ]
    return CompletionList(is_incomplete=False, items=items)
