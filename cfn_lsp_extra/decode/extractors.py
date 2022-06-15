"""

"""
from abc import ABC
from abc import abstractmethod
from typing import Generic
from typing import List
from typing import TypeVar
from typing import Union

from ..aws_data import AWSPropertyName
from ..aws_data import AWSResourceName
from ..aws_data import Tree
from .position import PositionLookup
from .position import Spanning
from .yaml_decoding import POSITION_PREFIX
from .yaml_decoding import VALUES_POSITION_PREFIX


# credit https://stackoverflow.com/questions/16891340/remove-a-prefix-from-a-string
def remove_prefix(text: str, prefix: str) -> str:
    """Remove prefix from text if necessary."""
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text


E = TypeVar("E", covariant=True)


class Extractor(ABC, Generic[E]):
    def extract(self, node: Tree) -> PositionLookup[E]:
        """Call extract_node at each of the inner nodes of node.

        Parameters
        ----------
        node : Tree
            node to extract from (recursively).

        Returns
        -------
        PositionLookup[T]
            A PositionLookup object containing items from source."""
        position_lookup = PositionLookup[E]()
        for span in self.extract_node(node):
            position_lookup[span.value].append((span.line, span.char, span.span))
        for child in node.values():
            if isinstance(child, dict):
                position_lookup.extend_with_appends(self.extract(child))
        return position_lookup

    @abstractmethod
    def extract_node(self, node: Tree) -> List[Spanning[E]]:
        ...


class ResourcePropertyExtractor(Extractor[AWSPropertyName]):
    """Extractor for resource properties.

    Methods
    -------
    extract(node)
        Extract resource properties from node.

    Returns
    -------
    PositionLookup[T]
        A PositionLookup mapping AWSPropertyName objects to positions."""

    def extract_node(self, node: Tree) -> List[Spanning[AWSPropertyName]]:
        props = []
        is_res_node = "Properties" in node and "Type" in node
        if is_res_node and isinstance(node["Properties"], dict):
            type_ = node["Type"]
            props = self._extract_recursive(
                node["Properties"], AWSResourceName(value=type_)
            )
        elif (
            is_res_node
            and isinstance(node["Properties"], str)
            and VALUES_POSITION_PREFIX in node
        ):
            props = self._extract_unfinished(node)
        return props

    def _extract_recursive(
        self, node: Tree, parent: Union[AWSPropertyName, AWSResourceName]
    ) -> List[Spanning[AWSPropertyName]]:
        props = []
        for key, value in node.items():
            if key.startswith(POSITION_PREFIX):
                prop = remove_prefix(key, POSITION_PREFIX)
                aws_prop = parent / prop
                line, char = value
                props.append(
                    Spanning[AWSPropertyName](
                        value=aws_prop, line=line, char=char, span=len(prop)
                    )
                )
                if isinstance(node[prop], dict):
                    props.extend(self._extract_recursive(node[prop], aws_prop))
                elif isinstance(node[prop], list):
                    for sub_node in filter(lambda p: isinstance(p, dict), node[prop]):
                        props.extend(self._extract_recursive(sub_node, aws_prop))
        return props

    def _extract_unfinished(self, node: Tree) -> List[Spanning[AWSPropertyName]]:
        props = []
        unfinished_property = node["Properties"]
        type_ = node["Type"]
        for dct in node[VALUES_POSITION_PREFIX]:
            key = POSITION_PREFIX + unfinished_property
            if key in dct:
                line, char = dct[key]
                aws_prop = AWSResourceName(value=type_) / unfinished_property
                props.append(
                    Spanning[AWSPropertyName](
                        value=aws_prop,
                        line=line,
                        char=char,
                        span=len(unfinished_property),
                    )
                )
                break
        return props


class ResourceExtractor(Extractor[AWSResourceName]):
    """Extractor for resources names.

    Methods
    -------
    extract(node)
        Extract a resource name from node.

    Returns
    -------
    PositionLookup[T]
        A PositionLookup mapping AWSResourceName objects to positions."""

    def extract_node(self, node: Tree) -> List[Spanning[AWSResourceName]]:
        props = []
        if "Resources" in node and isinstance(node["Resources"], dict):
            for _, resource_dct in node["Resources"].items():
                if (
                    isinstance(resource_dct, dict)
                    and "Type" in resource_dct
                    and VALUES_POSITION_PREFIX in resource_dct
                ):
                    type_ = resource_dct["Type"] or ""
                    value_positions = resource_dct[VALUES_POSITION_PREFIX]
                    key = POSITION_PREFIX + str(type_)  # type could be fn call
                    for dct in value_positions:
                        if key in dct:
                            line, char = dct[key]
                            props.append(
                                Spanning[AWSResourceName](
                                    value=AWSResourceName(value=type_),
                                    line=line,
                                    char=char,
                                    span=len(type_),
                                )
                            )
                            break
        return props


T = TypeVar("T", covariant=True)


class CompositeExtractor(Extractor[T]):
    """Accumulates the results of multiple Extractor objects."""

    def __init__(self, *extractors: Extractor[T]):
        self._extractors = extractors

    def extract_node(self, node: Tree) -> List[Spanning[T]]:
        ls = []
        for extractor in self._extractors:
            ls.extend(extractor.extract_node(node))
        return ls
