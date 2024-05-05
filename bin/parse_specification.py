#!/usr/bin/env python3
"""
pip-run bs4 lxml markdownify -- bin/parse_resource_specification.py CloudFormationResourceSpecification.json docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-resource-specification-format.html
https://github.com/emacs-lsp/lsp-mode/issues/3676
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-amplifyuibuilder-component-predicate.html

Not in the spec are attribute descriptions, and allowed values.
"""

import json
import os
import pprint
import sys

from bs4 import BeautifulSoup
from markdownify import markdownify as md

ALLOWED_VALUES_PREFIX = "*Allowed values*:"


def parse(f):
    with open(f, "r") as f_:
        content = json.load(f_)
    return content


def rename_props(d, base_directory):
    if not isinstance(d, dict):
        return d
    d_ = {}
    for k, v in d.items():
        # if k.startswith("AWS::"):
        #     print(k)
        if k == "Documentation":
            content = file_content(base_directory, v)
            doc = d_["MarkdownDocumentation"] = documentation(content, v)
            d_["RefReturnValue"] = ref_return_value(content, v.split("/")[-1])
            lines = doc.splitlines()
            allowed_values_line = next(
                (line for line in lines if line.startswith(ALLOWED_VALUES_PREFIX)), None
            )
            if allowed_values_line:
                allowed_values = (
                    allowed_values_line.removeprefix(ALLOWED_VALUES_PREFIX)
                    .strip("` ")
                    .replace(" | ", "|")
                    .split("|")
                )
                d_["AllowedValues"] = allowed_values
        if isinstance(v, dict) and "Attributes" in v and "Documentation" in v:
            set_attribute_doc(v["Documentation"], v["Attributes"])
        d_[k] = rename_props(v, base_directory)
    return d_


def set_attribute_doc(base_link, attribs_dct):
    for attrib, attrib_dct in attribs_dct.items():
        id_ = f"{base_link}#{attrib}-fn::getatt"
        attrib_dct["Documentation"] = id_


def to_aws_context(resource_types, property_types, base_dir):
    return {
        "resources": rename_props(resource_types, base_dir),
        "properties": rename_props(property_types, base_dir),
    }


def file_content(
    base_directory: str, link: str, file_contents={}, on_fail_try_download=True
) -> str:
    def read_file(loc) -> None:
        with open(loc) as f:
            file_contents[loc] = BeautifulSoup(f.read(), features="lxml")

    location = link.removeprefix(
        "http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide"
    )
    if "#" in link:  # Subprop
        file_, _, id_ = location.partition("#")
        file_ = base_directory + file_
        if file_ not in file_contents:
            try:
                read_file(file_)
            except FileNotFoundError:
                if on_fail_try_download:
                    try_download(link, file_)
                    return file_content(
                        base_directory, link, on_fail_try_download=False
                    )
                else:
                    print(f"No file found for {link}")
                    return ""

    else:  # resource
        file_ = base_directory + location
        if file_ not in file_contents:
            try:
                read_file(file_)
            except FileNotFoundError:
                if on_fail_try_download:
                    try_download(link, file_)
                    return file_content(
                        base_directory, link, on_fail_try_download=False
                    )
                else:
                    print(f"No file found for {link}")
                    return ""
    return file_contents[file_]


def documentation(content, link):
    if "#" in link:  # Subprop
        id_ = link.split("#")[-1]
        dt = content.find("dt", {"id": id_})
        if not dt:
            print(f"No documentation found for {link}")
            return ""
        dd = dt.findNext("dd")
        return md(str(dd)) if dd else ""
    else:  # resource
        div = content.find("div", {"class": "awsdocs-page-header-container"})
        p_tags, el = [], div
        while True:
            if not el:
                break
            el = el.find_next_sibling()
            if el.name == "p":
                p_tags.append(el)
            else:
                break
        return md("\n".join(map(str, p_tags))) if p_tags else ""


def ref_return_value(content, slug):
    prefix = slug.removesuffix(".html")
    id_ = f"{prefix}-return-values-ref"
    div = content.find("h3", {"id": id_})
    p_tags, el = [], div
    while True:
        if not el:
            break
        el = el.find_next_sibling()
        if el.name == "p":
            p_tags.append(el)
        else:
            break
    return md("\n".join(map(str, p_tags))) if p_tags else ""


def try_download(url, out_file_name):
    os.system(f"curl -L -X GET {url} > {out_file_name}")


def main():
    f, base_dir = sys.argv[1], sys.argv[2]
    parsed = parse(f)
    property_types = parsed["PropertyTypes"]
    resource_types = parsed["ResourceTypes"]
    aws_context = to_aws_context(resource_types, property_types, base_dir)
    with open("new-aws-context.json", "w") as f:
        json.dump(aws_context, f, indent=2)
    # print(list(aws_context.items())[0])


if __name__ == "__main__":
    main()
