"""
Classes for dealing with aws properties
"""
from __future__ import annotations

from enum import Enum
from typing import Any
from typing import List
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


AWSPropertyName.update_forward_refs()


AWSName = Union[AWSResourceName, AWSPropertyName]


class AWSContext(BaseModel):
    """A handle on AWS resource data for the lsp server."""

    resources: Tree

    def __getitem__(self, name: AWSName) -> Tree:
        try:
            resource, *subprops = name.split()
            prop = self.resources[resource]
            for subprop in subprops:
                prop = prop["properties"][subprop]
            return prop
        except KeyError:
            raise ValueError(f"'{name}' is not a recognised property")

    def description(self, name: AWSName) -> str:
        """Get the description of obj."""
        return self[name]["description"]  # type: ignore[no-any-return]

    def same_level(self, obj: AWSName) -> List[str]:
        """Return names at the same (property/resource) level as obj."""
        if isinstance(obj, AWSResourceName):
            return list(self.resources.keys())
        elif isinstance(obj, AWSPropertyName):
            try:
                return list(self[obj.parent]["properties"].keys())
            except KeyError:
                return []
        else:
            raise ValueError(f"obj has to be of type AWSName, but was '{type(obj)}'")
