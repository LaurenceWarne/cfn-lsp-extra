"""
https://raw.githubusercontent.com/awslabs/goformation/master/schema/sam.schema.json
"""
import json  # noqa: I001
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

import requests

from ..aws_data import AWSSpecification, Tree
from .specification import documentation, file_content, run_command

logger = logging.getLogger(__name__)

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
DEFAULT_SPEC_URL = "https://raw.githubusercontent.com/awslabs/goformation/master/schema/sam.schema.json"
DOC_URL = "docs.aws.amazon.com/serverless-application-model/latest/developerguide/"


def to_aws_context(sam_dct: Tree, base_directory: Path, base_url: str) -> Tree:
    d_ = {}
    base = sam_dct["definitions"]
    d_[AWSSpecification.RESOURCE_TYPES] = {
        k: normalise_resource(k, v, base_directory, base_url)
        for k, v in base.items()
        if "." not in k and SERVERLESS_PREFIX in k
    }
    d_[AWSSpecification.PROPERTY_TYPES] = {
        k: normalise_property(k, v, base_directory, base_url)
        for k, v in base.items()
        if "." in k and SERVERLESS_PREFIX in k
    }
    return d_


def normalise_resource(name: str, d: Tree, base_directory: Path, base_url: str) -> Tree:
    if not isinstance(d, dict):
        return d

    d_ = {}
    props = d[PROP_KEY][AWSSpecification.PROPERTIES][PROP_KEY]
    d_[AWSSpecification.PROPERTIES] = props
    link = f"{base_url}sam-resource-{name.split('::')[-1].lower()}"
    bs = file_content(base_directory, link, base_url=base_url)
    d_[AWSSpecification.MARKDOWN_DOCUMENTATION] = documentation(bs, link, name)

    required = d[PROP_KEY][AWSSpecification.PROPERTIES].get(REQUIRED, [])
    for property_name in list(props.keys()):
        sub_props = d_[AWSSpecification.PROPERTIES][property_name]
        sub_props[AWSSpecification.REQUIRED] = property_name in required
        normalise_types(sub_props)
    return d_


def normalise_property(name: str, d: Tree, base_directory: Path, base_url: str) -> Tree:
    if not isinstance(d, dict):
        return d

    parent, _, prop = name.partition(".")
    resource = parent.split("::")[-1]

    d_ = {}
    d_[AWSSpecification.PROPERTIES] = d[PROP_KEY]
    link = f"{base_url}sam-property-{resource}-{prop.lower()}"
    bs = file_content(base_directory, link, base_url=base_url)
    d_[AWSSpecification.MARKDOWN_DOCUMENTATION] = documentation(bs, link, name)

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


def run(
    spec_file: Optional[Path],
    documentation_directory: Optional[Path],
    out_path: Optional[Path],
) -> None:
    out_file = Path("new-aws-sam-context.json").absolute()
    if spec_file:
        spec_json = json.loads(spec_file.read_bytes())
    else:
        logger.info("Downloading spec from %s", DEFAULT_SPEC_URL)
        spec_json = json.loads(requests.get(DEFAULT_SPEC_URL).text)
    with tempfile.TemporaryDirectory() as tmp_directory:
        os.chdir(tmp_directory)
        doc_dir = documentation_directory or Path(DOC_URL)
        base_url = f"https://{DOC_URL}"
        if not documentation_directory:
            run_command(f"wget --no-parent -r {base_url}")
        aws_context = to_aws_context(spec_json, doc_dir, base_url)
        with open(out_file, "w") as sam_spec_out:
            json.dump(aws_context, sam_spec_out, indent=2)
    logger.info("Wrote context to %s", out_file)
