"""
Completions for !Refs
"""
from typing import Optional

from lsprotocol.types import CompletionItem
from lsprotocol.types import CompletionList
from lsprotocol.types import Position
from pygls.workspace import Document

from ..aws_data import AWSContext
from ..aws_data import AWSRefName
from ..aws_data import AWSRefSource
from ..aws_data import Tree
from ..cursor import text_edit
from ..cursor import word_before_after_position
from ..decode.extractors import Extractor
from ..ref import REF_EXTRACTOR
from ..ref import REF_SRC_EXTRACTOR


def ref_completions(
    template_data: Tree,
    document: Document,
    position: Position,
    aws_context: AWSContext,
    ref_extractor: Extractor[AWSRefName] = REF_EXTRACTOR,
    ref_src_extractor: Extractor[AWSRefSource] = REF_SRC_EXTRACTOR,
) -> Optional[CompletionList]:
    ref_lookup = ref_extractor.extract(template_data)
    ref_span = ref_lookup.at(position.line, position.character)
    if ref_span:
        before, after = word_before_after_position(document.lines, position)
        ref_src_lookup = ref_src_extractor.extract(template_data)
        items = [
            CompletionItem(
                label=ref_src.logical_name,
                documentation=ref_src.as_documentation(aws_context),
                text_edit=text_edit(position, before, after, ref_src.logical_name),
            )
            for ref_src, _ in ref_src_lookup.items()
        ]
        return CompletionList(is_incomplete=False, items=items)
    return None
