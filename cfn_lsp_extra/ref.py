from typing import Optional

from .aws_data import AWSParameter
from .aws_data import AWSRefName
from .aws_data import Tree
from .decode.extractors import ParameterExtractor
from .decode.position import Spanning


def resolve_ref(
    ref_name: AWSRefName, template_data: Tree
) -> Optional[Spanning[AWSParameter]]:
    """Given a ref_name, find the position of its definition in a template."""
    param_extractor = ParameterExtractor()
    param_lookup = param_extractor.extract(template_data)
    for param, position_list in param_lookup.items():
        if param.logical_name == ref_name.value and position_list:
            line, char, _ = position_list[0]
            return Spanning(
                value=param, line=line, char=char, span=len(param.logical_name)
            )
    else:
        return None
