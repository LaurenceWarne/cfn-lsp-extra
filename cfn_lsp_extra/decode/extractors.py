"""
Classes for extracting positional information from decoded documents.

For example extracting the positions of resource parameters.
"""
from abc import ABC
from abc import abstractmethod
from typing import Callable
from typing import Generic
from typing import List
from typing import TypeVar
from typing import Union

from ..aws_data import AWSLogicalId
from ..aws_data import AWSParameter
from ..aws_data import AWSPropertyName
from ..aws_data import AWSResourceName
from ..aws_data import Tree
from . import DEBUG_CHAR
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
    @abstractmethod
    def extract(self, node: Tree) -> PositionLookup[E]:
        """Call extract contents from node.

        Parameters
        ----------
        node : Tree
            The root node to extract from.

        Returns
        -------
        PositionLookup[T]
            A PositionLookup object containing items from source."""
        ...


class RecursiveExtractor(Extractor[E]):
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
        if isinstance(node, dict):
            position_lookup = PositionLookup.from_iterable(self.extract_node(node))
            iterable = node.values()
        else:
            position_lookup = PositionLookup[E]()
            iterable = node
        for child in iterable:
            if isinstance(child, dict):
                position_lookup.extend_with_appends(self.extract(child))
            elif isinstance(child, list):
                for sub_child in filter(lambda c: isinstance(c, (dict, list)), child):
                    position_lookup.extend_with_appends(self.extract(sub_child))
        return position_lookup

    @abstractmethod
    def extract_node(self, node: Tree) -> List[Spanning[E]]:
        ...


class ResourcePropertyExtractor(Extractor[AWSPropertyName]):
    """Extractor for resource and nested properties.

    Methods
    -------
    extract(node)
        Extract resource and nested properties from node."""

    def extract(self, node: Tree) -> PositionLookup[AWSPropertyName]:
        props = []
        if "Resources" in node and isinstance(node["Resources"], dict):
            for resource in filter(
                lambda r: isinstance(r, dict), node["Resources"].values()
            ):
                is_res_node = "Properties" in resource and "Type" in resource
                if is_res_node and isinstance(resource["Properties"], dict):
                    type_ = resource["Type"] or ""
                    props.extend(
                        self._extract_recursive(
                            resource["Properties"],
                            AWSResourceName(value=type_),
                        )
                    )
                elif (
                    is_res_node
                    and isinstance(resource["Properties"], str)
                    and VALUES_POSITION_PREFIX in resource
                ):
                    props.extend(
                        self._extract_unfinished(
                            resource,
                            resource["Properties"],
                            AWSResourceName(value=resource.get("Type", "")),
                        )
                    )
        return PositionLookup.from_iterable(props)

    def _extract_recursive(
        self, node: Tree, parent: Union[AWSPropertyName, AWSResourceName]
    ) -> List[Spanning[AWSPropertyName]]:
        props = []
        if isinstance(node, list):
            for sub_node in node:
                if isinstance(sub_node, (dict, list)):
                    props.extend(self._extract_recursive(sub_node, parent))
            return props
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
                        if isinstance(sub_node, dict):
                            props.extend(self._extract_recursive(sub_node, aws_prop))
                        elif isinstance(sub_node, list):
                            props.extend(self._extract_recursive(sub_node, parent))
                elif node[prop] == DEBUG_CHAR and VALUES_POSITION_PREFIX in node:
                    props.extend(
                        self._extract_unfinished(node, node[prop], parent / prop)
                    )
        return props

    def _extract_unfinished(
        self,
        node: Tree,
        unfinished_property: Tree,
        parent: Union[AWSPropertyName, AWSResourceName],
    ) -> List[Spanning[AWSPropertyName]]:
        props = []
        for dct in node[VALUES_POSITION_PREFIX]:
            key = POSITION_PREFIX + unfinished_property
            if key in dct:
                line, char = dct[key]
                aws_prop = parent / unfinished_property
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
        Extract resource names from node."""

    def extract(self, node: Tree) -> PositionLookup[AWSResourceName]:
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
        return PositionLookup.from_iterable(props)


class ParameterExtractor(Extractor[AWSParameter]):
    """Extractor for parameters.

    Methods
    -------
    extract(node)
        Extract resource names from node."""

    SECTION = "Parameters"

    def extract(self, node: Tree) -> PositionLookup[AWSParameter]:
        params = []
        if self.SECTION in node and isinstance(node[self.SECTION], dict):
            for param_name, content_dct in node[self.SECTION].items():
                key = POSITION_PREFIX + param_name
                add_parameter = (
                    key in node[self.SECTION]
                    and isinstance(content_dct, dict)
                    and "Type" in content_dct
                )
                if add_parameter:
                    type_ = content_dct["Type"]
                    line, char = node[self.SECTION][key]
                    param = AWSParameter(
                        logical_name=param_name,
                        type_=type_,
                        description=content_dct.get("Description", None),
                        default=content_dct.get("Default", None),
                    )
                    params.append(
                        Spanning[AWSParameter](
                            value=param,
                            line=line,
                            char=char,
                            span=len(param_name),
                        )
                    )
        return PositionLookup.from_iterable(params)


K = TypeVar("K", covariant=True)


class KeyExtractor(RecursiveExtractor[K]):
    """Extractor for named key values.

    Methods
    -------
    extract(node)
        Extract keys from node."""

    def __init__(self, key_name: str, name_fn: Callable[[str], K]):
        self.key_name = key_name
        self.name_fn = name_fn

    def extract_node(self, node: Tree) -> List[Spanning[K]]:
        found = []
        for key, value in node.items():
            if key == self.key_name and VALUES_POSITION_PREFIX in node:
                for val_pos_dct in node[VALUES_POSITION_PREFIX]:
                    p_key = POSITION_PREFIX + str(value)
                    if p_key in val_pos_dct:
                        line, char = val_pos_dct[p_key]
                        found.append(
                            Spanning[K](
                                value=self.name_fn(value),
                                line=line,
                                char=char,
                                span=len(value),
                            )
                        )
        return found


class GetAttExtractor(RecursiveExtractor[str]):
    """Extractor for GetAtts.

    Methods
    -------
    extract(node)
        Extract GetAtts from node."""

    KEY = "Fn::GetAtt"

    def extract_node(self, node: Tree) -> List[Spanning[K]]:
        found = []
        for key, value in node.items():
            if key == self.KEY and VALUES_POSITION_PREFIX in node:
                expr = ".".join(value)
                for val_pos_dct in node[VALUES_POSITION_PREFIX]:
                    p_key = POSITION_PREFIX + expr
                    if p_key in val_pos_dct:
                        line, char = val_pos_dct[p_key]
                        found.append(
                            Spanning[K](
                                value=expr,
                                line=line,
                                char=char,
                                span=len(expr),
                            )
                        )
        return found


class LogicalIdExtractor(Extractor[AWSLogicalId]):
    """Extractor for the logical ids of a template.

    Methods
    -------
    extract(node)
        Extract logical ids from node."""

    SECTION = "Resources"

    def extract(self, node: Tree) -> PositionLookup[AWSLogicalId]:
        params = []
        if self.SECTION in node and isinstance(node[self.SECTION], dict):
            for logical_id, content_dct in node[self.SECTION].items():
                key = POSITION_PREFIX + logical_id
                if key in node[self.SECTION]:
                    if isinstance(content_dct, dict) and "Type" in content_dct:
                        type_ = content_dct.get("Type", None)
                    else:
                        type_ = None
                    line, char = node[self.SECTION][key]
                    params.append(
                        Spanning[K](
                            value=AWSLogicalId(logical_name=logical_id, type_=type_),
                            line=line,
                            char=char,
                            span=len(logical_id),
                        )
                    )

        return PositionLookup.from_iterable(params)


T = TypeVar("T", covariant=True)


class CompositeExtractor(Extractor[T]):
    """Accumulates the results of multiple Extractor objects."""

    def __init__(self, *extractors: Extractor[T]):
        self._extractors = extractors

    def extract(self, node: Tree) -> PositionLookup[T]:
        lookup = PositionLookup[T]()
        for extractor in self._extractors:
            lookup.extend_with_appends(extractor.extract(node))
        return lookup
