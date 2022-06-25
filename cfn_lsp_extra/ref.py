from typing import Optional

from pygls.lsp.types.basic_structures import Position

from .aws_data import AWSRefName
from .aws_data import Tree
from .decode.extractors import ParameterExtractor


def resolve_ref(ref_name: AWSRefName, template_data: Tree) -> Optional[Position]:
    param_extractor = ParameterExtractor()
    param_lookup = param_extractor.extract(template_data)
    for param, position_list in param_lookup.items():
        if param.logical_name == ref_name.value and position_list:
            line, char, _ = position_list[0]
            return Position(line=line, character=char)
    else:
        return None
