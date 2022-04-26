"""
Classes for dealing with aws properties
"""
from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Union

from pydantic import BaseModel


# A Tree type representing a recursive nested structure such as yaml or json
# https://github.com/python/mypy/issues/731
# Tree = Dict[str, Union[str, "Tree"]]
Tree = Any


class AWSResourceName(BaseModel, frozen=True):
    value: str

    def __str__(self) -> str:
        return self.value

    def __truediv__(self, other: str) -> AWSPropertyName:
        return AWSPropertyName(parent=self, property_=other)


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


class AWSProperty(BaseModel):
    """Property of an AWS resource."""

    name: AWSPropertyName
    description: str
    subproperties: Dict[str, AWSProperty] = {}


AWSProperty.update_forward_refs()


AWSName = Union[AWSResourceName, AWSPropertyName]


class AWSResource(BaseModel):
    """Information on an AWS Cloudformation resource and its supported properties.

    It's a thin wrapper around a dictionary mapping property names of a given
    aws resource e.g. 'InstanceType' to properties themselves."""

    name: AWSResourceName
    description: str
    properties: Dict[str, AWSProperty]

    def __getitem__(self, property_name: AWSPropertyName) -> AWSProperty:
        return self.properties[property_name.property_]


class AWSContext(BaseModel):
    """A handle on AWS resource data for the lsp server."""

    resources: Tree

    def __getitem__(self, aws_property_name: AWSPropertyName) -> str:
        return self.resources[aws_property_name.parent][  # type: ignore[no-any-return]
            aws_property_name.property_
        ]

    def description(self, obj: Union[AWSResourceName, AWSPropertyName]) -> str:
        if isinstance(obj, AWSPropertyName):
            try:
                resource, *subprops = obj.split()
                prop = self.resources[resource]
                for subprop in subprops:
                    prop = prop["properties"][subprop]
                return prop["description"]  # type: ignore[no-any-return]
            except KeyError:
                raise ValueError(f"'{obj}' is not a recognised property")
        elif isinstance(obj, AWSResourceName):
            try:
                return self.resources[obj.value][  # type: ignore[no-any-return]
                    "description"
                ]
            except KeyError:
                raise ValueError(f"'{obj}' is not a recognised resource")
        else:
            raise ValueError(f"Can't get a description for value of type '{type(obj)}'")
