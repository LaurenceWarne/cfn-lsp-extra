"""
https://raw.githubusercontent.com/awslabs/goformation/master/schema/sam.schema.json
"""
import functools
import json  # noqa: I001
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup
from markdownify import markdownify as md  # type: ignore[import-untyped]

from .. import remove_prefix, remove_suffix
from ..aws_data import AWSSpecification, Tree

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
SERVERLESS_PREFIX = "AWS::Serverless"


def to_aws_context(sam_dct: Tree, base_directory: str) -> Tree:
    d_ = {}
    base = sam_dct["definitions"]
    d_["ResourceTypes"] = {
        k: normalise_resource(v)
        for k, v in base.items()
        if "." not in k and SERVERLESS_PREFIX in k
    }
    d_["PropertyTypes"] = {
        k: normalise_property(v)
        for k, v in base.items()
        if "." in k and SERVERLESS_PREFIX in k
    }
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
        normalise_types(sub_props)
    return d_


def normalise_property(d: Tree) -> Tree:
    if not isinstance(d, dict):
        return d

    d_ = {}
    d_[AWSSpecification.PROPERTIES] = d[PROP_KEY]

    for v in d_[AWSSpecification.PROPERTIES].values():
        normalise_types(v)
    return d_


def normalise_types(d: Tree) -> Tree:
    if REF_KEY in d:
        ref = d.pop(REF_KEY)
        d[AWSSpecification.TYPE] = ref.split(".")[-1]
    elif ANY_OF in d:  # We just take the first
        types = d.pop(ANY_OF)
        find = next((t[REF_KEY].split(".")[-1] for t in types if REF_KEY in t), None)
        if find:
            d[AWSSpecification.TYPE] = find
        else:
            d[AWSSpecification.PRIMITIVE_TYPE] = types[0]
    elif TYPE_KEY in d and d[TYPE_KEY] == "array":
        d.pop(TYPE_KEY)
        d[AWSSpecification.TYPE] = "List"
        item_type = d.pop("items")
        if isinstance(item_type, dict) and REF_KEY in item_type:
            d[AWSSpecification.ITEM_TYPE] = item_type[REF_KEY].split(".")[-1]
        else:
            d[AWSSpecification.ITEM_TYPE] = item_type[TYPE_KEY]
    elif TYPE_KEY in d:
        d[AWSSpecification.PRIMITIVE_TYPE] = d.pop(TYPE_KEY)
    return d


def run(spec_file: Path) -> None:
    out_file = Path("new-aws-sam-context.json").absolute()
    with tempfile.TemporaryDirectory() as tmp_directory:
        d = json.loads(spec_file.read_bytes())
        os.chdir(tmp_directory)
        doc_dir = (
            "docs.aws.amazon.com/serverless-application-model/latest/developerguide"
        )
        os.system(f"wget --no-parent -r https://{doc_dir}")
        aws_context = to_aws_context(d, doc_dir)
        with open(out_file, "w") as sam_spec_out:
            json.dump(aws_context, sam_spec_out, indent=2)
