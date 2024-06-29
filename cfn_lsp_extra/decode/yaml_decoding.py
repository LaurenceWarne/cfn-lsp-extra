"""
Utilities for parsing yaml document strings.
"""
from typing import Any, List, Tuple

from cfnlint.decode.cfn_yaml import FN_PREFIX, UNCONVERTED_SUFFIXES
from cfnlint.decode.node import dict_node, list_node

try:
    from yaml.cyaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml.loader import SafeLoader  # type: ignore[assignment]

from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

POSITION_PREFIX = "__position__"
VALUES_POSITION_PREFIX = "__value_positions__"


# Copied from an earlier version of cfnlint for compat
def multi_constructor(loader: SafeLoader, tag_suffix: str, node: Node) -> Node:
    """Deal with !Ref style function format."""

    if tag_suffix not in UNCONVERTED_SUFFIXES:
        tag_suffix = f"{FN_PREFIX}{tag_suffix}"

    if tag_suffix == "Fn::GetAtt":
        constructor = construct_getatt
    elif isinstance(node, ScalarNode):
        constructor = loader.construct_scalar  # type: ignore[assignment]
    elif isinstance(node, SequenceNode):
        constructor = loader.construct_sequence  # type: ignore[assignment]
    elif isinstance(node, MappingNode):
        constructor = loader.construct_mapping  # type: ignore[assignment]
    else:
        raise Exception(f"Bad tag: !{tag_suffix}")

    return dict_node({tag_suffix: constructor(node)}, node.start_mark, node.end_mark)  # type: ignore[no-any-return]


def construct_getatt(node: Node) -> Node:
    """Reconstruct !GetAtt into a list."""

    if isinstance(node.value, str):
        return list_node(node.value.split(".", 1), node.start_mark, node.end_mark)  # type: ignore[no-any-return]
    if isinstance(node.value, list):
        return list_node([s.value for s in node.value], node.start_mark, node.end_mark)  # type: ignore[no-any-return]

    raise ValueError(f"Unexpected node type: {type(node.value)}")


class SafePositionLoader(SafeLoader):
    """A loader which saves positional information on elements.

    It takes inspiration from https://stackoverflow.com/questions/13319067/parsing-yaml-return-with-line-number#13319530.
    """  # noqa

    yaml_multi_constructors = {"!": multi_constructor}

    def _positional_key_value(self, node: Node) -> Tuple[str, List[int]]:
        return POSITION_PREFIX + node.value, [
            node.start_mark.line,
            node.start_mark.column,
        ]

    def _value_position(self, scalar_node: ScalarNode) -> Any:
        position_key, position_value = self._positional_key_value(scalar_node)
        return {position_key: position_value}

    def construct_mapping(self, node: MappingNode, deep: bool = False) -> Any:
        mapping = super(SafePositionLoader, self).construct_mapping(node, deep=deep)

        for key_node, value_node in node.value:
            position_key, position_value = self._positional_key_value(key_node)
            mapping[position_key] = position_value

            # Stick positional info on leaf nodes into their own mapping so they
            # aren't confused with others, first we check if value_node is a
            # !Ref
            obj = self.construct_object(value_node)  # type: ignore[no-untyped-call]
            if isinstance(value_node, ScalarNode) and hasattr(obj, "start_mark"):
                key = key_node.value
                if not isinstance(mapping[key], dict):
                    continue  # This is a duplicate key (ie bad template)
                to_add = []
                for _, sub_value in obj.items():
                    line, char = value_node.end_mark.line, value_node.end_mark.column
                    sub_value = (
                        ".".join(sub_value)
                        if isinstance(sub_value, list)
                        else sub_value
                    )
                    char -= len(sub_value)
                    to_add.append({POSITION_PREFIX + value_node.value: [line, char]})
                mapping[key][VALUES_POSITION_PREFIX] = to_add

            # node is a normal ScalarNode (not a !Ref)
            elif isinstance(value_node, ScalarNode):
                if VALUES_POSITION_PREFIX not in mapping:
                    mapping[VALUES_POSITION_PREFIX] = []
                value_position = self._value_position(value_node)
                mapping[VALUES_POSITION_PREFIX].append(value_position)
        return mapping

    def construct_sequence(self, node: SequenceNode, deep: bool = False) -> Any:
        mapping = super(SafePositionLoader, self).construct_sequence(node, deep)

        for idx, value_node in enumerate(node.value):
            obj = self.construct_object(value_node)  # type: ignore[no-untyped-call]
            if isinstance(value_node, ScalarNode) and hasattr(obj, "start_mark"):
                to_add = []
                for _, sub_value in obj.items():
                    line, char = value_node.end_mark.line, value_node.end_mark.column
                    char -= len(sub_value)
                    to_add.append({POSITION_PREFIX + value_node.value: [line, char]})
                mapping[idx][VALUES_POSITION_PREFIX] = to_add

        return mapping
