"""
Classes for dealing with aws properties
"""

from typing import Dict

from pydantic import BaseModel


class AWSProperty(BaseModel, frozen=True):

    resource: str
    property_: str

    def __str__(self):
        return f"{self.resource}/{self.property_}"


class AWSResource(BaseModel):
    """Information on an AWS Cloudformation resource and its supported properties.

    It's a thin wrapper around a dictionary mapping properties of a given aws
    resource e.g. 'InstanceType' to descriptions."""

    name: str
    property_descriptions: Dict[str, str]

    def __getitem__(self, property_: str) -> str:
        return self.property_descriptions[property_]


class AWSContext(BaseModel):
    """A handle on AWS resource data for the lsp server."""

    resources: Dict[str, AWSResource]

    def __getitem__(self, aws_property: AWSProperty) -> str:
        return self.resources[aws_property.resource][aws_property.property_]
