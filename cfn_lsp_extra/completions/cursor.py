import re
from typing import List
from typing import Pattern
from typing import Tuple

from pygls.lsp.types.basic_structures import Position
from pygls.lsp.types.basic_structures import Range
from pygls.lsp.types.basic_structures import TextEdit
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
