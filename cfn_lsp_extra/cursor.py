import re
from typing import List
from typing import Pattern
from typing import Tuple

from lsprotocol.types import Position
from lsprotocol.types import Range
from lsprotocol.types import TextEdit
from pygls.workspace import position_from_utf16


RE_END_WORD = re.compile("^[A-Za-z_0-9!:]*")
RE_START_WORD = re.compile("[A-Za-z_0-9!:]*$")


def text_edit(position: Position, before: str, after: str, text: str) -> TextEdit:
    """Return a TextEdit for position given text before and after the cursor."""
    start = Position(line=position.line, character=position.character - len(before))
    end = Position(line=position.line, character=position.character + len(after))
    return TextEdit(range=Range(start=start, end=end), new_text=text)


def word_before_after_position(
    lines: List[str],
    position: Position,
    re_start_word: Pattern[str] = RE_START_WORD,
    re_end_word: Pattern[str] = RE_END_WORD,
) -> Tuple[str, str]:
    if position.line >= len(lines):
        return "", ""

    pos = position_from_utf16(lines, position)
    row, col = pos.line, pos.character
    line = lines[row]
    # Split word in two
    start = line[:col]
    end = line[col:]

    # Take end of start and start of end to find word
    # These are guaranteed to match, even if they match the empty string
    m_start = re_start_word.findall(start)
    m_end = re_end_word.findall(end)

    return m_start[0], m_end[-1]


def word_at_position_char_bounds(
    lines: List[str],
    position: Position,
    re_start_word: Pattern[str] = RE_START_WORD,
    re_end_word: Pattern[str] = RE_END_WORD,
) -> Tuple[int, int]:
    before, after = word_before_after_position(
        lines, position, re_start_word, re_end_word
    )
    char = position.character
    return char - len(before), char + len(after)
