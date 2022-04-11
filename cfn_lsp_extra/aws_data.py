"""
Classes for dealing with aws properties
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class AWSProperty:
    resource: str
    property_: str

    def __str__(self):
        return f"{self.resource}/{self.property_}"


@dataclass
class AWSResource:
    """Information on an AWS Cloudformation resource and its supported properties."""

    name: str
    property_descriptions: Dict[str, str]

    def __getitem__(self, property_: str) -> str:
        return self.property_descriptions[property_]


@dataclass
class AWSContext:
    """A handle on AWS resource data for the lsp server."""

    resources: Dict[str, AWSResource]

    def __getitem__(self, aws_property: AWSProperty) -> str:
        return self.resources[aws_property.resource][aws_property.property_]
