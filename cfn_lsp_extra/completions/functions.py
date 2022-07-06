"""
Intrinsic function completions, see:
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference.html
For more information.
"""
from typing import List

from pydantic import BaseModel
from pydantic.typing import Callable
from pygls.lsp.types import CompletionItem
from pygls.lsp.types import CompletionList
from pygls.lsp.types import Position
from pygls.workspace import Document
from pygls.workspace import position_from_utf16

from .cursor import RE_END_WORD
from .cursor import RE_START_WORD
from .cursor import text_edit
from .cursor import word_before_after_position


class IntrinsicFunction(BaseModel, frozen=True):
    function: str
    full_name_prefix: str = "Fn::"
    short_form_prefix: str = "!"

    def short_form(self) -> str:
        return self.short_form_prefix + self.function

    def full_name(self) -> str:
        return self.full_name_prefix + self.function


# Hard coded temporarily (?)
INTRINSIC_FUNCTIONS = [
    IntrinsicFunction(function="Base64"),
    IntrinsicFunction(function="Cidr"),
    IntrinsicFunction(function="FindInMap"),
    IntrinsicFunction(function="GetAtt"),
    IntrinsicFunction(function="GetAZs"),
    IntrinsicFunction(function="ImportValue"),
    IntrinsicFunction(function="Join"),
    IntrinsicFunction(function="Select"),
    IntrinsicFunction(function="Split"),
    IntrinsicFunction(function="Sub"),
    IntrinsicFunction(function="Transform"),
    IntrinsicFunction(function="And"),
    IntrinsicFunction(function="Equals"),
    IntrinsicFunction(function="If"),
    IntrinsicFunction(function="Not"),
    IntrinsicFunction(function="Or"),
    IntrinsicFunction(function="Ref", full_name_prefix=""),
]


def intrinsic_function_completions(
    document: Document,
    position: Position,
    intrinsic_functions: List[IntrinsicFunction] = INTRINSIC_FUNCTIONS,
) -> CompletionList:
    before, after = word_before_after_position(document.lines, position)
    word = before + after
    filter_fn: Callable[[IntrinsicFunction], bool]
    label_fn: Callable[[IntrinsicFunction], str]
    if word.startswith("Fn") or word.startswith("fn"):
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
        )
        for f in intrinsic_functions
        if filter_fn(f)
    ]
    return CompletionList(is_incomplete=False, items=items)


#  Slighly modified version of document.word_at_position
def word_at_position(lines: List[str], position: Position) -> str:
    """
    Get the word under the cursor returning the start and end positions.
    """
    if position.line >= len(lines):
        return ""

    row, col = position_from_utf16(lines, position)
    line = lines[row]
    # Split word in two
    start = line[:col]
    end = line[col:]

    # Take end of start and start of end to find word
    # These are guaranteed to match, even if they match the empty string
    m_start = RE_START_WORD.findall(start)
    m_end = RE_END_WORD.findall(end)

    return m_start[0] + m_end[-1]  # type: ignore[no-any-return]
