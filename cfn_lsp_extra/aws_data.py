"""
Classes for dealing with aws properties
"""

from abc import ABC
from abc import abstractmethod
from typing import Dict
from typing import Union

from pydantic import BaseModel


class AWSProperty(BaseModel, frozen=True):
    """Property of an AWS resource."""

    resource: str
    property_: str

    def __str__(self) -> str:
        return f"{self.resource}/{self.property_}"


AWSResourceName = str


class AWSResource(BaseModel):
    """Information on an AWS Cloudformation resource and its supported properties.

    It's a thin wrapper around a dictionary mapping properties of a given aws
    resource e.g. 'InstanceType' to descriptions."""

    name: AWSResourceName
    description: str
    property_descriptions: Dict[str, str]

    def __getitem__(self, property_: str) -> str:
        return self.property_descriptions[property_]


class AWSContext(BaseModel):
    """A handle on AWS resource data for the lsp server."""

    resources: Dict[str, AWSResource]

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
