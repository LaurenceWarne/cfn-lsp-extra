"""

"""
from abc import ABC
from abc import abstractmethod
from collections import defaultdict
from typing import Any
from typing import Generic
from typing import Optional
from typing import TypeVar

from ..aws_data import AWSProperty
from .position import Spanning
from .yaml_parsing import SafePositionLoader
from .yaml_parsing import Yaml


E = TypeVar("E")


class Extractor(ABC, Generic[E]):
    @abc.abstractmethod
    def extract(self, node: Yaml) -> List[Spanning[E]]:
        ...


class ResourcePropertyExtractor(Extractor[AWSProperty]):
    """Extractor for resource properties.

    Methods
    -------
    extract(node)
        Extract resource properties from node."""

    def extract(self, node: Yaml) -> List[Spanning[AWSProperty]]:
        props = []
        if "Properties" in node and "Type" in node:
            type_ = node["Type"]
            for key, value in node["Properties"].items():
                if key.startswith(SafePositionLoader.POSITION_PREFIX):
                    prop = key.lstrip(SafePositionLoader.POSITION_PREFIX)
                    aws_prop = AWSProperty(resource=type_, property_=prop)
                    line, char = value
                    props.append(
                        Spanning(item=aws_prop, line=line, char=char, span=len(prop))
                    )
        return props


AWSResourceName = str


class ResourceExtractor(Extractor[AWSResourceName]):
    """Extractor for resources names.

    Methods
    -------
    extract(node)
        Extract a resource name from node."""

    def extract(self, node: Yaml) -> List[Spanning[AWSProperty]]:
        props = []
        if "Properties" in node and "Type" in node:
            type_ = node["Type"]
            span = Spanning(item=type_, line=..., char=..., span=...)
            props.append(span)
        return props
