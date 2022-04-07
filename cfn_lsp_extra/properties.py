"""
Classes for dealing with aws properties
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AWSProperty:
    resource: str
    property_: str

    def __str__(self):
        return f"{self.resource}/{self.property_}"
