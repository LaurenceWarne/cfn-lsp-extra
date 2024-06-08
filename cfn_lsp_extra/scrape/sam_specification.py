"""
https://raw.githubusercontent.com/awslabs/goformation/master/schema/sam.schema.json
"""
import functools
import json  # noqa: I001
import logging
import os
import sys
from typing import Optional

from bs4 import BeautifulSoup
from markdownify import markdownify as md  # type: ignore[import-untyped]

from .. import remove_prefix, remove_suffix
from ..aws_data import AWSContext, AWSResourceName, AWSSpecification, Tree

PROP_KEY = "properties"
REF_KEY = "$ref"
REF_PREFIX = "#/definitions/"
REQUIRED = "required"
TYPE_KEY = "type"
PRIMITIVE_TYPE = "PrimitiveType"
PROPERTY_SKIP_LIST = (
    REQUIRED,
    PRIMITIVE_TYPE,
    "additionalProperties",
    PROP_KEY,
    TYPE_KEY,
)
ANY_OF = "anyOf"


def to_aws_context(sam_dct: Tree) -> Tree:
    d_ = {}
    base = sam_dct["definitions"]
    d_["ResourceTypes"] = {
        k: normalise_resource(v)
        for k, v in base.items()
        if "." not in k and "AWS::Serverless" in k
    }
    # d_["PropertyTypes"] = {k: recurse(v) for k, v in base.items() if "." in k}
    return d_


def normalise_resource(d: Tree) -> Tree:
    if not isinstance(d, dict):
        return d

    d_ = {}
    props = d[PROP_KEY][AWSSpecification.PROPERTIES][PROP_KEY]
    d_[AWSSpecification.PROPERTIES] = props

    required = d[PROP_KEY][AWSSpecification.PROPERTIES].get(REQUIRED, [])
    for property_name in list(props.keys()):
        sub_props = d_[AWSSpecification.PROPERTIES][property_name]
        sub_props[AWSSpecification.REQUIRED] = property_name in required
        if REF_KEY in sub_props:
            ref = sub_props.pop(REF_KEY)
            sub_props["Type"] = ref.split(".")[-1]
        elif ANY_OF in sub_props:
            sub_props["Type"] = next(
                t[REF_KEY].split(".")[-1] for t in sub_props.pop(ANY_OF) if REF_KEY in t
            )
    return d_
