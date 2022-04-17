"""

"""
from abc import ABC
from abc import abstractmethod
from collections import defaultdict
from typing import Any
from typing import Generic
from typing import List
from typing import Optional
from typing import TypeVar

from ..aws_data import AWSProperty
from .position import PositionLookup
from .position import Spanning
from .yaml_parsing import SafePositionLoader
from .yaml_parsing import Yaml


E = TypeVar("E")


class Extractor(ABC, Generic[E]):
    def extract(self, node: Yaml) -> PositionLookup[E]:
        """Call extract_node at each of the inner nodes of node.

        Parameters
        ----------
        node : Yaml
            node to extract from (recursively)"""
        position_lookup = PositionLookup[E]()
        for span in self.extract_node(node):
            position_lookup[span.value].append((span.line, span.char, span.span))
        for child in node.values():
            if isinstance(child, dict):
                position_lookup.extend_with_appends(self.extract(child))
        return position_lookup

    @abstractmethod
    def extract_node(self, node: Yaml) -> List[Spanning[E]]:
        ...


class ResourcePropertyExtractor(Extractor[AWSProperty]):
    """Extractor for resource properties.

    Methods
    -------
    extract(node)
        Extract resource properties from node."""

    def extract_node(self, node: Yaml) -> List[Spanning[AWSProperty]]:
        props = []
        if "Properties" in node and "Type" in node:
            type_ = node["Type"]
            for key, value in node["Properties"].items():
                if key.startswith(SafePositionLoader.POSITION_PREFIX):
                    prop = key.lstrip(SafePositionLoader.POSITION_PREFIX)
                    aws_prop = AWSProperty(resource=type_, property_=prop)
                    line, char = value
                    props.append(
                        Spanning[AWSProperty](
                            value=aws_prop, line=line, char=char, span=len(prop)
                        )
                    )
        return props


AWSResourceName = str


class ResourceExtractor(Extractor[AWSResourceName]):
    """Extractor for resources names.

    Methods
    -------
    extract(node)
        Extract a resource name from node."""

    def extract_node(self, node: Yaml) -> List[Spanning[AWSResourceName]]:
        props = []
        if "Properties" in node and "Type" in node:
            type_ = node["Type"]
            span = Spanning[AWSResourceName](item=type_, line=..., char=..., span=...)
            props.append(span)
        return props
