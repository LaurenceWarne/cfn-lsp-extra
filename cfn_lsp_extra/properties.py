"""
Classes for dealing with aws properties
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class AWSResource:
    name: str
    property_descriptions: Dict[str, str]

    def __getitem__(self, property_: str) -> str:
        return self.property_descriptions[property_]


@dataclass(frozen=True)
class AWSProperty:
    resource: str
    property_: str

    def __str__(self):
        return f"{self.resource}/{self.property_}"
