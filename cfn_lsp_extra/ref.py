from typing import Optional

from pygls.lsp.types import Position

from .aws_data import AWSRefName
from .aws_data import AWSRefSource
from .aws_data import Tree
from .decode.extractors import CompositeExtractor
from .decode.extractors import Extractor
from .decode.extractors import KeyExtractor
from .decode.extractors import LogicalIdExtractor
from .decode.extractors import ParameterExtractor
from .decode.position import PositionLink
from .decode.position import Spanning


REF_EXTRACTOR = KeyExtractor[AWSRefName]("Ref", lambda s: AWSRefName(value=s))
REF_SRC_EXTRACTOR = CompositeExtractor[AWSRefSource](
    LogicalIdExtractor(), ParameterExtractor()
)


def resolve_ref(
    position: Position,
    template_data: Tree,
    ref_extractor: Extractor[AWSRefName] = REF_EXTRACTOR,
    ref_src_extractor: Extractor[AWSRefSource] = REF_SRC_EXTRACTOR,
) -> Optional[PositionLink[AWSRefSource, AWSRefName]]:
    """Attempt to resolve the source and documentation of a ref at position.

    Parameters
    ----------
    position : Position
        The position to look at in the template
    template_data : Tree
        The decoded template
    extractor: Extractor[AWSRefSource]
        The extractor to use to extract the source of refs

    Returns
    -------
    Optional[PositionLink[AWSRefSource, AWSRefName]]
        A spanning object containing the ref source if it was found, else None
    """
    ref_lookup = ref_extractor.extract(template_data)
    ref_span = ref_lookup.at(position.line, position.character)
    if ref_span:
        ref_src_lookup = ref_src_extractor.extract(template_data)
        for ref_src, position_list in ref_src_lookup.items():
            if ref_src.logical_name == ref_span.value.value and position_list:
                line, char, _ = position_list[0]
                src_span = Spanning[AWSRefSource](
                    value=ref_src, line=line, char=char, span=len(ref_src.logical_name)
                )
                return PositionLink[AWSRefSource, AWSRefName](
                    source_span=src_span, target_span=ref_span
                )
    return None
