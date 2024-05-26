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


def to_aws_context(sam_dct: Tree) -> Tree:
    d_ = {}
    base = sam_dct["definitions"]
    d_["ResourceTypes"] = {k: recurse(v) for k, v in base.items() if "." not in k}
    d_["PropertyTypes"] = {k: recurse(v) for k, v in base.items() if "." in k}
    return d_


def recurse(d: Tree) -> Tree:
    if not isinstance(d, dict):
        return d
    d_: Tree = {}
    for k, v in d.items():
        if isinstance(v, dict) and PROP_KEY in v and isinstance(v[PROP_KEY], dict):
            required_set = set()
            if REQUIRED in v:
                required_set = set(v[REQUIRED])
            for k2, v2 in v[PROP_KEY].items():
                if k2 == REQUIRED:
                    continue
                d_[k2] = recurse(v2)
                d_[k2]["Required"] = k2 in required_set
        # If "properties" is in v, we want to ignore all other keys
        elif k == REF_KEY:
            d_["Type"] = v2.partition(".")[-1]
        elif k == TYPE_KEY:
            d_["PrimitiveType"] = v2
        else:
            d_[k2] = v2
        d_[k] = recurse({k2: v2 for k2, v2 in v.items() if k2 != PROP_KEY})
    return d_
