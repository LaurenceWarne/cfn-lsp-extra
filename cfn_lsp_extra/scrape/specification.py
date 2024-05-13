#!/usr/bin/env python3
"""
cfn-lsp-extra update-specification
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-resource-specification-format.html
https://github.com/emacs-lsp/lsp-mode/issues/3676
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-amplifyuibuilder-component-predicate.html

Not in the spec are attribute descriptions, and allowed values.
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

ALLOWED_VALUES_PREFIX = "*Allowed values*:"
MAX_ALLOWED_VALUES_WIDTH = 30

logger = logging.getLogger(__name__)


def parse(f: str) -> Tree:
    with open(f, "r") as f_:
        return json.load(f_)


def to_aws_context(d: Tree, parent: Optional[str], base_directory: str) -> Tree:
    if not isinstance(d, dict):
        return d
    d_: Tree = {}
    for k, v in d.items():
        if k == AWSSpecification.DOCUMENTATION:
            content = file_content(base_directory, v)
            doc = d_[AWSSpecification.MARKDOWN_DOCUMENTATION] = documentation(
                content, v, parent
            )
            d_[AWSSpecification.REF_RETURN_VALUE] = ref_return_value(
                content, v.split("/")[-1]
            )
            lines = doc.splitlines()
            idx, allowed_values_line = next(
                (
                    (idx, line)
                    for idx, line in enumerate(lines)
                    if line.startswith(ALLOWED_VALUES_PREFIX)
                ),
                (None, None),
            )
            if allowed_values_line and idx:
                allowed_values = (
                    remove_prefix(allowed_values_line, ALLOWED_VALUES_PREFIX)
                    .strip("` ")
                    .replace(" | ", "|")
                    .split("|")
                )
                d_[AWSSpecification.ALLOWED_VALUES] = allowed_values
                if len(allowed_values_line) > MAX_ALLOWED_VALUES_WIDTH:
                    new_line = (
                        " | ".join(allowed_values)[: MAX_ALLOWED_VALUES_WIDTH - 3]
                        + "..."
                    )
                    lines[idx] = f"{ALLOWED_VALUES_PREFIX} `{new_line}`"
                    d_[AWSSpecification.MARKDOWN_DOCUMENTATION] = "\n".join(lines)
        if (
            isinstance(v, dict)
            and AWSSpecification.ATTRIBUTES in v
            and AWSSpecification.DOCUMENTATION in v
        ):
            set_attribute_doc(
                v[AWSSpecification.DOCUMENTATION],
                v[AWSSpecification.ATTRIBUTES],
            )
        d_[k] = to_aws_context(v, k, base_directory)
    return d_


def set_attribute_doc(base_link: str, attribs_dct: Tree) -> None:
    for attrib, attrib_dct in attribs_dct.items():
        id_ = f"{base_link}#{attrib}-fn::getatt"
        attrib_dct[AWSSpecification.DOCUMENTATION] = id_


@functools.lru_cache(maxsize=None)
def file_content(
    base_directory: str, link: str, on_fail_try_download: bool = True
) -> BeautifulSoup:
    def read_file(loc: str) -> BeautifulSoup:
        with open(loc) as f:
            return BeautifulSoup(f.read(), features="lxml")

    location = remove_prefix(
        link, "http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide"
    )
    if "#" in link:  # Subprop
        file_, _, id_ = location.partition("#")
        file_ = base_directory + file_
        try:
            return read_file(file_)
        except FileNotFoundError:
            if on_fail_try_download:
                try_download(link, file_)
                return file_content(base_directory, link, on_fail_try_download=False)
            logger.info(f"No file found for {link}")
            return BeautifulSoup("")
    else:  # resource
        file_ = base_directory + location
        try:
            return read_file(file_)
        except FileNotFoundError:
            if on_fail_try_download:
                try_download(link, file_)
                return file_content(base_directory, link, on_fail_try_download=False)
            logger.info(f"No file found for {link}")
            return BeautifulSoup("")


def documentation(content: BeautifulSoup, link: str, parent: Optional[str]) -> str:
    if "#" in link:  # Subprop
        id_ = link.split("#")[-1]
        dt = content.find("dt", {"id": id_})
        if not dt:
            logger.info(f"No documentation found for {link}")
            return ""
        dd = dt.findNext("dd")
        doc = md(str(dd)) if dd else ""
    else:  # resource
        div = content.find("div", {"class": "awsdocs-page-header-container"})
        tags, el = [], div
        # Add everything until the next header tag
        while True:
            if not el:
                break
            el = el.find_next_sibling()
            if el and el.name and not (el.name.startswith("h") and len(el.name) == 2):
                tags.append(el)
            else:
                break
        doc = md("".join(map(str, tags))) if tags else ""
    return f"`{parent if parent else ''}`\n{doc}"


def ref_return_value(content: BeautifulSoup, slug: str) -> str:
    prefix = remove_suffix(slug, ".html")
    id_ = f"{prefix}-return-values-ref"
    div = content.find("h3", {"id": id_})
    p_tags, el = [], div
    while True:
        if not el:
            break
        el = el.find_next_sibling()
        if el and el.name and el.name == "p":
            p_tags.append(el)
        else:
            break
    return md("".join(map(str, p_tags))) if p_tags else ""  # type: ignore[no-any-return]


def try_download(url: str, out_file_name: str) -> None:
    os.system(f"curl -L -X GET {url} > {out_file_name}")


def main() -> None:
    f, base_dir = sys.argv[1], sys.argv[2]
    parsed = parse(f)
    ctx_map = to_aws_context(parsed, None, base_dir)
    with open("new-aws-context.json", "w") as f_:
        json.dump(ctx_map, f_, indent=2)


def run() -> None:
    with open("new-aws-context.json", "r") as f:
        ctx_map = json.load(f)
        aws_context = AWSContext(ctx_map["ResourceTypes"], ctx_map["PropertyTypes"])
    print(
        aws_context.same_level(
            AWSResourceName("AWS::ECS::TaskDefinition")
            / "ContainerDefinitions"
            / "Name"
        )
    )
    print(
        aws_context[
            AWSResourceName("AWS::ECS::TaskDefinition")
            / "ContainerDefinitions"
            / "Name"
        ]
    )


if __name__ == "__main__":
    if len(sys.argv) > 3:
        run()
    else:
        main()
