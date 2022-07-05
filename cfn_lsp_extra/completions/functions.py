"""
Intrinsic function completions, see:
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference.html
For more information.
"""

import re
from typing import List
from typing import Pattern
from typing import Tuple

from pydantic import BaseModel
from pydantic.typing import Callable
from pygls.lsp.types import CompletionItem
from pygls.lsp.types import CompletionList
from pygls.lsp.types import Position
from pygls.lsp.types.basic_structures import Range
from pygls.lsp.types.basic_structures import TextEdit
from pygls.workspace import Document
from pygls.workspace import position_from_utf16


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
    start = Position(line=position.line, character=position.character - len(before))
    end = Position(line=position.line, character=position.character + len(after))
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
            text_edit=TextEdit(
                range=Range(start=start, end=end), new_text=label_fn(f) + " "
            ),
        )
        for f in intrinsic_functions
        if filter_fn(f)
    ]
    return CompletionList(is_incomplete=False, items=items)


RE_END_WORD = re.compile("^[A-Za-z_0-9!:]*")
RE_START_WORD = re.compile("[A-Za-z_0-9!:]*$")


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


def word_before_after_position(
    lines: List[str],
    position: Position,
    re_start_word: Pattern[str] = RE_START_WORD,
    re_end_word: Pattern[str] = RE_END_WORD,
) -> Tuple[str, str]:
    if position.line >= len(lines):
        return "", ""

    row, col = position_from_utf16(lines, position)
    line = lines[row]
    # Split word in two
    start = line[:col]
    end = line[col:]

    # Take end of start and start of end to find word
    # These are guaranteed to match, even if they match the empty string
    m_start = re_start_word.findall(start)
    m_end = re_end_word.findall(end)

    return m_start[0], m_end[-1]
