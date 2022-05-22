"""
Classes for dealing with aws properties.

For reference as of 21/05/2022 there are 186 resource prefixes. and a total
of 899 resources.  The most properties for a resource is 52 for
'AWS::RDS::DBInstance' and the average is 6.193548387096774.
"""
from __future__ import annotations

from enum import Enum
from typing import Any
from typing import List
from typing import Set
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


class OverridingKeyNotInContextException(Exception):
    def __init__(self, message: str, path: str):
        super().__init__(message)
        self.path = path


class AWSContext(BaseModel):
    """A handle on AWS resource data for the lsp server."""

    resources: Tree

    def resource_prefixes(self) -> Set[str]:
        """Return a set of all 'service-provider::service-name' strings."""
        return {s.rsplit("::", 1)[0] for s in self.resources.keys()}

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

    def update(self, other: AWSContext, error_if_new: bool = True) -> None:
        """Add elements from other to this object."""

        def update_dict_recursive(mp1: Tree, mp2: Tree, path: str) -> None:
            for key, value in mp2.items():
                if key not in mp1:
                    if error_if_new:
                        bad_path = f"{path}/{key}"
                        raise OverridingKeyNotInContextException(
                            f"{bad_path} is not in the base context!", bad_path
                        )
                    else:
                        mp1[key] = value
                if not isinstance(mp1[key], dict) or not isinstance(value, dict):
                    mp1[key] = value
                else:
                    update_dict_recursive(mp1[key], value, f"{path}/{key}")

        return update_dict_recursive(self.resources, other.resources, "resources")
