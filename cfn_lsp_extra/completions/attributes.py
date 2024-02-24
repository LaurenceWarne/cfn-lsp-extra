"""
Completions for !GetAtt
"""
from typing import Optional

from lsprotocol.types import CompletionItem, CompletionList, Position
from pygls.workspace import Document

from ..aws_data import AWSContext, AWSLogicalId, AWSResourceName, Tree
from ..cursor import text_edit, word_before_after_position
from ..decode.extractors import Extractor, GetAttExtractor, LogicalIdExtractor

GET_ATT_EXTRACTOR = GetAttExtractor()
GET_ATT_SRC_EXTRACTOR = LogicalIdExtractor()


def attribute_completions(
    template_data: Tree,
    aws_context: AWSContext,
    document: Document,
    position: Position,
    get_att_extractor: Extractor[str] = GET_ATT_EXTRACTOR,
    get_att_src_extractor: Extractor[AWSLogicalId] = GET_ATT_SRC_EXTRACTOR,
) -> Optional[CompletionList]:
    get_att_lookup = get_att_extractor.extract(template_data)
    get_att_span = get_att_lookup.at(position.line, position.character)
    if get_att_span:
        text = get_att_span.value
        _, col, _ = next(ps[0] for e, ps in get_att_lookup.items() if e == text)
        res, _, att = text.partition(".")

        before, after = word_before_after_position(document, position)
        if col <= position.character <= col + len(res):
            get_att_src_lookup = get_att_src_extractor.extract(template_data)
            items = [
                CompletionItem(
                    label=get_att_src.logical_name,
                    documentation=get_att_src.as_documentation(aws_context),
                    text_edit=text_edit(
                        position, before, after, get_att_src.logical_name
                    ),
                )
                for get_att_src, _ in get_att_src_lookup.items()
            ]
            return CompletionList(is_incomplete=False, items=items)

        get_att_src_lookup = get_att_src_extractor.extract(template_data)
        for get_att_src, _ in get_att_src_lookup.items():
            if get_att_src.logical_name == res:
                type_ = get_att_src.type_
                if type_:
                    resource_name = AWSResourceName(value=type_)
                    if type_ and resource_name in aws_context:
                        items = [
                            CompletionItem(label=return_val, documentation=desc)
                            for return_val, desc in aws_context.return_values(
                                resource_name
                            ).items()
                        ]
                        return CompletionList(is_incomplete=False, items=items)
    return None
