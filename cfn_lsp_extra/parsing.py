"""
Utilities for parsing document strings.
"""
from collections import defaultdict
from typing import Dict
from typing import List
from typing import Union

from cfnlint.decode.cfn_yaml import multi_constructor
from yaml.loader import SafeLoader
from yaml.nodes import MappingNode
from yaml.nodes import ScalarNode
from yaml.nodes import SequenceNode
from yaml.resolver import BaseResolver

from .properties import AWSProperty


class SafePositionLoader(SafeLoader):
    """A loader class which saves positional information on elements.

    It takes inspiration from https://stackoverflow.com/questions/13319067/parsing-yaml-return-with-line-number#13319530."""

    POSITION_PREFIX = "__position__"

    def construct_mapping(self, node: MappingNode, deep=False):
        node_pair_lst = node.value
        node_pair_lst_for_appending = []

        for key_node, value_node in node_pair_lst:
            line_value_node = ScalarNode(
                tag=BaseResolver.DEFAULT_SCALAR_TAG, value=key_node.start_mark.line
            )
            column_value_node = ScalarNode(
                tag=BaseResolver.DEFAULT_SCALAR_TAG, value=key_node.start_mark.column
            )
            meta_key_node = ScalarNode(
                tag=BaseResolver.DEFAULT_SCALAR_TAG,
                value=self.POSITION_PREFIX + key_node.value,
            )
            meta_value_node = SequenceNode(
                tag=BaseResolver.DEFAULT_SEQUENCE_TAG,
                value=[line_value_node, column_value_node],
            )
            node_pair_lst_for_appending.append((meta_key_node, meta_value_node))

        node.value = node_pair_lst + node_pair_lst_for_appending
        mapping = super(SafePositionLoader, self).construct_mapping(node, deep=deep)
        return mapping


SafePositionLoader.add_multi_constructor("!", multi_constructor)


Yaml = Dict[str, Union[str, "Yaml"]]


def flatten_mapping(yaml_dict: Yaml) -> Dict[AWSProperty, List[List[int]]]:
    position_dict = defaultdict(list)
    if "Properties" in yaml_dict:
        type_ = yaml_dict["Type"]
        for key, value in yaml_dict["Properties"].items():
            if key.startswith(SafePositionLoader.POSITION_PREFIX):
                k = AWSProperty(type_, key.lstrip(SafePositionLoader.POSITION_PREFIX))
                position_dict[k].append(value)
    else:
        for key, value in yaml_dict.items():
            if isinstance(value, dict):
                for key2, value2 in flatten_mapping(value).items():
                    position_dict[key2].extend(value2)
    return position_dict
