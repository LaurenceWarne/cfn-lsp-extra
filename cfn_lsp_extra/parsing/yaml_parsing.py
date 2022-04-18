"""
Utilities for parsing yaml document strings.
"""
from collections import defaultdict
from typing import Any
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import Tuple
from typing import TypeVar
from typing import Union

from cfnlint.decode.cfn_yaml import multi_constructor
from pydantic import BaseModel


try:
    from yaml.cyaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml.loader import SafeLoader  # type: ignore[misc]

from pydantic.types import NonNegativeInt
from yaml.nodes import MappingNode
from yaml.nodes import Node
from yaml.nodes import ScalarNode
from yaml.nodes import SequenceNode
from yaml.resolver import BaseResolver

from ..aws_data import AWSProperty
from .position import PositionLookup
from .position import Spanning


class SafePositionLoader(SafeLoader):
    """A loader which saves positional information on elements.

    It takes inspiration from https://stackoverflow.com/questions/13319067/parsing-yaml-return-with-line-number#13319530."""  # noqa

    POSITION_PREFIX = "__position__"
    VALUES_POSITION_PREFIX = "__value_positions__"

    def _positional_key_value(self, node: Node) -> Tuple[str, List[int]]:
        return self.POSITION_PREFIX + node.value, [
            node.start_mark.line,
            node.start_mark.column,
        ]

    def construct_mapping(self, node: MappingNode, deep: bool = False) -> Any:
        mapping = super(  # type: ignore[no-untyped-call]
            SafePositionLoader, self
        ).construct_mapping(node, deep=deep)

        for key_node, value_node in node.value:
            position_key, position_value = self._positional_key_value(key_node)
            mapping[position_key] = position_value

            # Stick positional info on leaf nodes into their own mapping so they
            # aren't confused with others
            if isinstance(value_node, ScalarNode):
                if self.VALUES_POSITION_PREFIX not in mapping:
                    mapping[self.VALUES_POSITION_PREFIX] = []
                    position_key, position_value = self._positional_key_value(
                        value_node
                    )
                mapping[self.VALUES_POSITION_PREFIX].append(
                    {position_key: position_value}
                )
        return mapping


SafePositionLoader.add_multi_constructor(  # type: ignore[no-untyped-call]
    "!", multi_constructor
)

# https://github.com/python/mypy/issues/731
# Yaml = Dict[str, Union[str, "Yaml"]]
Yaml = Any
