"""
Utilities for parsing yaml document strings.
"""
from typing import Any
from typing import List
from typing import Tuple

from cfnlint.decode.cfn_yaml import multi_constructor


try:
    from yaml.cyaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml.loader import SafeLoader  # type: ignore[misc]

from yaml.nodes import MappingNode
from yaml.nodes import Node
from yaml.nodes import ScalarNode


POSITION_PREFIX = "__position__"
VALUES_POSITION_PREFIX = "__value_positions__"


class SafePositionLoader(SafeLoader):
    """A loader which saves positional information on elements.

    It takes inspiration from https://stackoverflow.com/questions/13319067/parsing-yaml-return-with-line-number#13319530."""  # noqa

    def _positional_key_value(self, node: Node) -> Tuple[str, List[int]]:
        return POSITION_PREFIX + node.value, [
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
                if VALUES_POSITION_PREFIX not in mapping:
                    mapping[VALUES_POSITION_PREFIX] = []
                position_key, position_value = self._positional_key_value(value_node)
                mapping[VALUES_POSITION_PREFIX].append({position_key: position_value})
        return mapping


SafePositionLoader.add_multi_constructor(  # type: ignore[no-untyped-call]
    "!", multi_constructor
)
