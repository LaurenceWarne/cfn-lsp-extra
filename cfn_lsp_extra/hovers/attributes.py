"""
Hovers for !GetAtt
"""
import re
from typing import Optional

from lsprotocol.types import Hover, MarkupContent, MarkupKind, Position, Range
from pygls.workspace import Document

from ..aws_data import AWSContext, AWSLogicalId, AWSResourceName, Tree
from ..cursor import word_at_position_char_bounds
from ..decode.extractors import Extractor, GetAttExtractor, LogicalIdExtractor

GET_ATT_EXTRACTOR = GetAttExtractor()
GET_ATT_SRC_EXTRACTOR = LogicalIdExtractor()
RE_END_ATTRIBUTE = re.compile(r"^[A-Za-z_0-9\.]*")
RE_START_ATTRIBUTE = re.compile(r"[A-Za-z_0-9\.]*$")


def attribute_hover(
    template_data: Tree,
    aws_context: AWSContext,
    document: Document,
    position: Position,
    get_att_extractor: Extractor[str] = GET_ATT_EXTRACTOR,
    get_att_src_extractor: Extractor[AWSLogicalId] = GET_ATT_SRC_EXTRACTOR,
) -> Optional[Hover]:
    get_att_lookup = get_att_extractor.extract(template_data)
    get_att_span = get_att_lookup.at(position.line, position.character)
    if get_att_span:
        text = get_att_span.value
        _, c, span = next(ps[0] for e, ps in get_att_lookup.items() if e == text)
        res, _, att = text.partition(".")

        get_att_src_lookup = get_att_src_extractor.extract(template_data)
        for get_att_src, _ in get_att_src_lookup.items():
            if get_att_src.logical_name == res:
                type_ = get_att_src.type_
                if type_:
                    resource_name = AWSResourceName(value=type_)
                    return_values = aws_context.return_values(resource_name)
                    char_start, char_end = word_at_position_char_bounds(
                        document, position, RE_START_ATTRIBUTE, RE_END_ATTRIBUTE
                    )
                    line_at = position.line
                    if att in return_values:
                        return Hover(
                            range=Range(
                                start=Position(line=line_at, character=char_start),
                                end=Position(line=line_at, character=char_end),
                            ),
                            contents=MarkupContent(
                                kind=MarkupKind.Markdown, value=return_values[att]
                            ),
                        )
                    break
    return None
