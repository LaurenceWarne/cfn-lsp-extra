"""
Classes for dealing with aws properties
"""
from __future__ import annotations

from typing import Any
from typing import Dict
from typing import Union

from pydantic import BaseModel


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

    def __getitem__(self, property_name: AWSPropertyName) -> str:
        return self.properties[property_name.property_]


class AWSContext(BaseModel):
    """A handle on AWS resource data for the lsp server."""

    resources: Any  # Dict[str, AWSResource]

    def __getitem__(self, aws_property: AWSProperty) -> str:
        return self.resources[aws_property.resource][aws_property.property_]

    def description(self, obj: Union[AWSResourceName, AWSProperty]) -> str:
        if isinstance(obj, AWSProperty):
            try:
                return self.resources[obj.resource][obj.property_]
            except KeyError:
                raise ValueError(f"'{obj}' is not a recognised property")
        elif isinstance(obj, AWSResourceName):
            try:
                return self.resources[obj].description
            except KeyError:
                raise ValueError(f"'{obj}' is not a recognised resource")
        else:
            raise ValueError(f"Can't get a description for value of type '{type(obj)}'")
