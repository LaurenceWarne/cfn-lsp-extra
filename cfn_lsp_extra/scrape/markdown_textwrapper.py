from __future__ import annotations

import re
from textwrap import TextWrapper
from typing import List
from typing import Pattern


class MarkdownLink(str):
    def __new__(cls, url: str, description: str) -> MarkdownLink:
        obj = str.__new__(cls, f"[{description}]({url})")
        obj.url = url  # type: ignore[attr-defined]
        obj.description = description  # type: ignore[attr-defined]
        return obj

    def __len__(self) -> int:
        return len(self.description)  # type: ignore[attr-defined]


class MarkdownTextWrapper(TextWrapper):
    """A TextWrapper which handles markdown links."""

    LINK_REGEX: Pattern[str] = re.compile(r"(\[.*?\]\(\S+\))")
    LINK_PARTS_REGEX: Pattern[str] = re.compile(r"^\[(.*?)\]\((\S+)\)$")

    def _split(self, text: str) -> List[str]:
        split = re.split(self.LINK_REGEX, text)
        chunks: List[str] = []
        for item in split:
            match = re.match(self.LINK_PARTS_REGEX, item)
            if match:
                chunks.append(MarkdownLink(match.group(2), match.group(1)))
            else:
                chunks.extend(super()._split(item))
        return chunks
