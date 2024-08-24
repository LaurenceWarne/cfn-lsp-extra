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
from .specification import (
    PARSE_SUCCESS_RATIO_KEY,
    documentation,
    file_content,
    run_command,
)
from .with_success_failure_count import WithSuccessFailureCount

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


def to_aws_context(
    sam_dct: Tree, base_directory: Path, base_url: str
) -> WithSuccessFailureCount[Tree]:
    d_: WithSuccessFailureCount[Tree] = WithSuccessFailureCount.zero(
        {AWSSpecification.RESOURCE_TYPES: {}, AWSSpecification.PROPERTY_TYPES: {}}
    )
    base = sam_dct["definitions"]
    for k, v in base.items():
        if "." not in k and SERVERLESS_PREFIX in k:
            res_with_counts = normalise_resource(k, v, base_directory, base_url)
            d_.value[AWSSpecification.RESOURCE_TYPES][k] = res_with_counts.value
            d_ = d_.add_counts(res_with_counts)
        elif SERVERLESS_PREFIX in k:
            res_with_counts = normalise_property(k, v, base_directory, base_url)
            d_.value[AWSSpecification.PROPERTY_TYPES][k] = res_with_counts.value
            d_ = d_.add_counts(res_with_counts)
    return d_


def normalise_resource(
    name: str, d: Tree, base_directory: Path, base_url: str
) -> WithSuccessFailureCount[Tree]:
    if not isinstance(d, dict):
        return WithSuccessFailureCount.zero(d)

    d_: WithSuccessFailureCount[Tree] = WithSuccessFailureCount.zero({})
    props = d[PROP_KEY][AWSSpecification.PROPERTIES][PROP_KEY]
    d_.value[AWSSpecification.PROPERTIES] = props
    link = f"{base_url}sam-resource-{name.split('::')[-1].lower()}"
    bs = file_content(base_directory, link)
    doc_with_counts = documentation(bs, link, name)
    d_.value[AWSSpecification.MARKDOWN_DOCUMENTATION] = doc_with_counts.value
    d_ = d_.add_counts(doc_with_counts)

    required = d[PROP_KEY][AWSSpecification.PROPERTIES].get(REQUIRED, [])
    for property_name in list(props.keys()):
        sub_props = d_.value[AWSSpecification.PROPERTIES][property_name]
        sub_props[AWSSpecification.REQUIRED] = property_name in required
        sub_doc_with_counts = documentation(bs, link, property_name)
        sub_props[AWSSpecification.MARKDOWN_DOCUMENTATION] = sub_doc_with_counts.value
        d_ = d_.add_counts(sub_doc_with_counts)
        normalise_types(sub_props)
    return d_


def normalise_property(
    name: str, d: Tree, base_directory: Path, base_url: str
) -> WithSuccessFailureCount[Tree]:
    if not isinstance(d, dict):
        return WithSuccessFailureCount.zero(d)

    parent, _, prop = name.partition(".")
    resource = parent.split("::")[-1]

    d_: WithSuccessFailureCount[Tree] = WithSuccessFailureCount.zero({})
    d_.value[AWSSpecification.PROPERTIES] = d[PROP_KEY]

    parent_link = f"{base_url}sam-resource-{parent.split('::')[-1].lower()}"
    parent_bs = file_content(base_directory, parent_link)
    a_element = parent_bs.find(
        "a",
        string=lambda x: x and x.lower() == prop.lower(),
        href=lambda h: not h.startswith("#") and "#" in h,
    )
    if a_element:
        link_val = a_element if isinstance(a_element, str) else a_element["href"]
        link = link_val[0] if isinstance(link_val, list) else link_val
        logger.info("Found replacement URL for %s: %s", name, link)
    else:
        link = f"{base_url}sam-property-{resource.lower()}-{prop.lower()}"
    bs = file_content(base_directory, link)
    doc_with_counts = documentation(bs, link, name)
    d_.value[AWSSpecification.MARKDOWN_DOCUMENTATION] = doc_with_counts.value
    d_ = d_.add_counts(doc_with_counts)

    for property_name, sub_props in d_.value[AWSSpecification.PROPERTIES].items():
        # property_name = 'Type', v =  {'type': 'string'}
        sub_doc_with_counts = documentation(bs, link, property_name)
        sub_props[AWSSpecification.MARKDOWN_DOCUMENTATION] = sub_doc_with_counts.value
        d_ = d_.add_counts(sub_doc_with_counts)
        normalise_types(sub_props)
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
        logger.info("Using base URL: %s", base_url)
        aws_context, md_succ, md_fails = to_aws_context(
            sam_dct=spec_json, base_directory=doc_dir, base_url=base_url
        ).to_tuple()
        logger.info("Failed getting markdown: %d/%d", md_fails, md_fails + md_succ)
        aws_context[PARSE_SUCCESS_RATIO_KEY] = round(md_succ / (md_fails + md_succ), 4)
        with open(out_file, "w") as sam_spec_out:
            json.dump(aws_context, sam_spec_out, indent=2)
    logger.info("Wrote context to %s", out_file)
