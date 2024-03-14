import re
from typing import Pattern, Tuple

from lsprotocol.types import Position, Range, TextEdit
from pygls.workspace import Document

RE_END_WORD = re.compile("^[A-Za-z_0-9!:]*")
RE_START_WORD = re.compile("[A-Za-z_0-9!:]*$")

def text_edit(position: Position, before: str, after: str, text: str) -> TextEdit:
    """Return a TextEdit for position given text before and after the cursor."""
    start = Position(line=position.line, character=position.character - len(before))
    end = Position(line=position.line, character=position.character + len(after))
    return TextEdit(range=Range(start=start, end=end), new_text=text)


def word_before_after_position(
    document: Document,
    position: Position,
    re_start_word: Pattern[str] = RE_START_WORD,
    re_end_word: Pattern[str] = RE_END_WORD,
) -> Tuple[str, str]:
    lines = document.lines
    if position.line >= len(lines):
        return "", ""

    pos = document.position_codec.position_from_client_units(lines, position)
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
    document: Document,
    position: Position,
    re_start_word: Pattern[str] = RE_START_WORD,
    re_end_word: Pattern[str] = RE_END_WORD,
) -> Tuple[int, int]:
    before, after = word_before_after_position(
        document, position, re_start_word, re_end_word
    )
    char = position.character
    return char - len(before), char + len(after)
