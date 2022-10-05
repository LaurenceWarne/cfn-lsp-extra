"""
Classes for dealing with aws properties.

For reference as of 21/05/2022 there are 186 resource prefixes. and a total
of 899 resources.  The most properties for a resource is 52 for
'AWS::RDS::DBInstance' and the average is 6.193548387096774.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from enum import Enum
from typing import Any
from typing import Dict
from typing import Iterator
from typing import List
from typing import MutableMapping
from typing import Optional
from typing import Union

from pydantic import BaseModel


# A Tree type representing a recursive nested structure such as yaml or json
# https://github.com/python/mypy/issues/731
# Tree = Dict[str, Union[str, "Tree"]]
Tree = Any


class AWSRoot(Enum):
    """Represents the root of the heirarchy.

    This enum's root value is this type's sole value."""

    root = 0

    def parent(self) -> AWSRoot:
        return self

    def __truediv__(self, resource: str) -> AWSResourceName:
        return AWSResourceName(value=resource)


class AWSResourceName(BaseModel, frozen=True):
    value: str
    parent: AWSRoot = AWSRoot.root

    def __str__(self) -> str:
        return self.value

    def __truediv__(self, other: str) -> AWSPropertyName:
        return AWSPropertyName(parent=self, property_=other)

    def split(self) -> List[str]:
        return [self.value]

    def short_form(self) -> str:
        return self.value


class AWSPropertyName(BaseModel, frozen=True):
    """Property of an AWS resource or AWS resource property."""

    parent: Union[AWSPropertyName, AWSResourceName]
    property_: str

    def __str__(self) -> str:
        return f"{self.parent}/{self.property_}"

    def __truediv__(self, other: str) -> AWSPropertyName:
        return AWSPropertyName(parent=self, property_=other)

    def __contains__(self, other: str) -> bool:
        if other == self.property_:
            return True
        if isinstance(self.parent, AWSResourceName):
            return other == self.parent.value
        else:
            return other in self.parent

    def split(self) -> List[str]:
        if isinstance(self.parent, AWSResourceName):
            return [str(self.parent), self.property_]
        else:
            return self.parent.split() + [self.property_]

    def short_form(self) -> str:
        return self.property_


AWSPropertyName.update_forward_refs()


AWSName = Union[AWSResourceName, AWSPropertyName]


class OverridingKeyNotInContextException(Exception):
    def __init__(self, message: str, path: str):
        super().__init__(message)
        self.path = path


class AWSContextMap(MutableMapping[AWSName, Tree]):
    def __init__(self, resources: Tree):
        self.resources = resources

    def __iter__(self) -> Iterator[AWSName]:
        for resource in self.resources.keys():
            yield AWSResourceName(value=resource)

    def __getitem__(self, name: AWSName) -> Tree:
        resource, *subprops = name.split()
        prop = self.resources[resource]
        for subprop in subprops:
            prop = prop["properties"][subprop]
        return prop

    def __len__(self) -> int:
        return len(self.resources)

    def __repr__(self) -> str:
        return repr(self.resources)

    # https://github.com/microsoft/pylance-release/issues/2097

    def __delitem__(self, key: AWSName) -> None:
        pass

    def __setitem__(self, key: AWSName, value: Tree) -> None:
        pass


class AWSContext:
    """A handle on AWS resource data for the lsp server."""

    def __init__(self, resource_map: MutableMapping[AWSName, Tree]):
        self.resource_map = resource_map

    def __getitem__(self, name: AWSName) -> Tree:
        try:
            return self.resource_map[name]
        except KeyError:
            raise KeyError(f"'{name}' is not a recognised resource or property")

    def __contains__(self, name: AWSName) -> bool:
        return name in self.resource_map

    def description(self, name: AWSName) -> str:
        """Get the description of obj."""
        return self[name]["description"]  # type: ignore[no-any-return]

    def return_values(self, resource: AWSResourceName) -> Dict[str, str]:
        return self[resource]["return_values"]  # type: ignore[no-any-return]

    def same_level(self, obj: AWSName) -> List[AWSName]:
        """Return names at the same (property/resource) level as obj."""
        if isinstance(obj, AWSResourceName):
            return list(self.resource_map.keys())
        elif isinstance(obj, AWSPropertyName):
            try:
                return [obj.parent / p for p in self[obj.parent]["properties"].keys()]
            except KeyError:
                return []
        else:
            raise ValueError(f"obj has to be of type AWSName, but was '{type(obj)}'")


class AWSRefName(BaseModel, frozen=True):
    value: str


class AWSRefSource(BaseModel, ABC):
    """An object which can be linked to using !Ref, e.g. a parameter."""

    logical_name: str

    @abstractmethod
    def as_documentation(self) -> str:
        ...


class AWSParameter(AWSRefSource, frozen=True):
    logical_name: str
    type_: str
    description: Optional[str] = None
    default: Optional[str] = None

    def as_documentation(self) -> str:
        description_str = "\n" + self.description if self.description else ""
        return f"""### Parameter: `{self.logical_name}`{description_str}
*Type*: `{self.type_}`
*Default*: {self.default}"""


class AWSLogicalId(AWSRefSource, frozen=True):
    logical_name: str
    type_: Optional[str]

    def as_documentation(self) -> str:
        return f"""### Resource: `{self.logical_name}`
*Type*: {"`" + self.type_ + "`" if self.type_ else "not given"}"""
