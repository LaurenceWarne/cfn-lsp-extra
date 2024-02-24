"""
Classes for dealing with aws properties.

For reference as of 21/05/2022 there are 186 resource prefixes. and a total
of 899 resources.  The most properties for a resource is 52 for
'AWS::RDS::DBInstance' and the average is 6.193548387096774.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Iterator, List, MutableMapping, Optional, Union

from attrs import frozen

from .scrape.markdown_textwrapper import TEXT_WRAPPER

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


@frozen
class AWSResourceName:
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


@frozen
class AWSPropertyName:
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
        return other in self.parent

    def split(self) -> List[str]:
        if isinstance(self.parent, AWSResourceName):
            return [str(self.parent), self.property_]
        return self.parent.split() + [self.property_]

    def short_form(self) -> str:
        return self.property_


AWSName = Union[AWSResourceName, AWSPropertyName]


class OverridingKeyNotInContextError(Exception):
    def __init__(self, message: str, path: str):
        super().__init__(message)
        self.path = path


class AWSContextMap(MutableMapping[AWSName, Tree]):
    def __init__(self, resources: Tree):
        self.resources = resources

    def __iter__(self) -> Iterator[AWSName]:
        for resource in self.resources:
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
        except KeyError as e:
            raise KeyError(f"'{name}' is not a recognised resource or property") from e

    def __contains__(self, name: AWSName) -> bool:
        return name in self.resource_map

    def description(self, name: AWSName) -> str:
        """Get the description of obj."""
        return self[name]["description"]  # type: ignore[no-any-return]

    def return_values(self, resource: AWSResourceName) -> Dict[str, str]:
        return self[resource].get("return_values", {})  # type: ignore[no-any-return]

    def ref_return_value(self, resource: AWSResourceName) -> str:
        return self[resource].get("ref_return_value", "unknown")  # type: ignore[no-any-return]

    def allowed_values(self, property_: AWSPropertyName) -> List[str]:
        return self[property_].get("values", [])  # type: ignore[no-any-return]

    def properties_with_allowed_values(self) -> List[AWSPropertyName]:
        """Return properties with a finite set of allowed values, e.g. for completion."""
        ls = []

        def extract_recursively(name: AWSName, prop_tree: Tree) -> None:
            if "values" in prop_tree and prop_tree["values"]:
                ls.append(name)
            for sub_prop_name, sub_prop_tree in prop_tree["properties"].items():
                extract_recursively(name / sub_prop_name, sub_prop_tree)

        for resource_name, resource_content in self.resource_map.items():
            for property_name, property_tree in resource_content["properties"].items():
                extract_recursively(resource_name / property_name, property_tree)

        return ls  # type: ignore[return-value]

    def same_level(self, obj: AWSName) -> List[AWSName]:
        """Return names at the same (property/resource) level as obj."""
        if isinstance(obj, AWSResourceName):
            return list(self.resource_map.keys())
        if isinstance(obj, AWSPropertyName):
            try:
                return [obj.parent / p for p in self[obj.parent]["properties"]]
            except KeyError:
                return []
        raise ValueError(f"obj has to be of type AWSName, but was '{type(obj)}'")


@frozen
class AWSRefName:
    value: str


@frozen
class AWSRefSource(ABC):
    """An object which can be linked to using !Ref, e.g. a parameter."""

    logical_name: str

    @abstractmethod
    def as_documentation(self, aws_context: AWSContext) -> str:
        ...


@frozen
class AWSParameter(AWSRefSource):
    logical_name: str
    type_: str
    description: Optional[str] = None
    default: Optional[str] = None

    def as_documentation(self, aws_context: AWSContext) -> str:
        description_str = "\n" + self.description if self.description else ""
        # We can't triple quote here since flake8 will flag the "  " as trailing whitespace...
        return (
            f"### Parameter: `{self.logical_name}`{description_str}  \n"
            f"*Type*: `{self.type_}`  \n"
            f"*Default*: {self.default}"
        )


@frozen
class AWSLogicalId(AWSRefSource):
    logical_name: str
    type_: Optional[str]

    def as_documentation(self, aws_context: AWSContext) -> str:
        ref_return_value = ""
        if self.type_:
            res_name = AWSResourceName(value=self.type_)
            if res_name in aws_context:
                ref_return_value = (
                    f"\n*Return Value*: {aws_context.ref_return_value(res_name)}  "
                )
        type_str = "`" + self.type_ + "`" if self.type_ else "not given"
        full_str = (
            f"### Resource: `{self.logical_name}`  \n"
            f"*Type*: {type_str}{ref_return_value}"
        )
        content = ""
        for line in full_str.splitlines():
            content += "\n".join(TEXT_WRAPPER.wrap(line)) + "\n"
        return content
