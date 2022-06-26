from typing import Optional

from pygls.lsp.types import Position

from .aws_data import AWSParameter
from .aws_data import AWSRefName
from .aws_data import Tree
from .decode.extractors import KeyExtractor
from .decode.extractors import ParameterExtractor
from .decode.position import Spanning


def resolve_ref(
    position: Position, template_data: Tree
) -> Optional[Spanning[AWSParameter]]:
    """Attempt to resolve the source and documentation of a ref at position.

    Parameters
    ----------
    position : Position
        The position to look at in the template

    Returns
    -------
    Optional[Spanning[AWSParameter]]
        A spanning object containing the ref source if it was found, else None
    """
    ref_extractor = KeyExtractor[AWSRefName]("Ref", lambda s: AWSRefName(value=s))
    ref_lookup = ref_extractor.extract(template_data)
    ref_span = ref_lookup.at(position.line, position.character)
    if ref_span:
        param_extractor = ParameterExtractor()
        param_lookup = param_extractor.extract(template_data)
        for param, position_list in param_lookup.items():
            if param.logical_name == ref_span.value.value and position_list:
                line, char, _ = position_list[0]
                return Spanning(
                    value=param, line=line, char=char, span=len(param.logical_name)
                )
    return None
