"""
cfn-lsp-extra update-specification
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-resource-specification-format.html
https://github.com/emacs-lsp/lsp-mode/issues/3676
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-amplifyuibuilder-component-predicate.html

Not in the spec are attribute descriptions, and allowed values.
"""

from __future__ import annotations

import functools
import json  # noqa: I001
import logging
import os
import tempfile
from pathlib import Path
from typing import Callable, Optional

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md  # type: ignore[import-untyped]

from .. import remove_prefix, remove_suffix
from ..aws_data import AWSSpecification, Tree
from .with_success_failure_count import WithSuccessFailureCount

ALLOWED_VALUES_PREFIX = "*Allowed values*:"
MAX_ALLOWED_VALUES_WIDTH = 30
DEFAULT_SPEC_URL = "https://dnwj8swjjbsbt.cloudfront.net/latest/gzip/CloudFormationResourceSpecification.json"
PARSE_SUCCESS_RATIO_KEY = "parse_success_ratio"

logger = logging.getLogger(__name__)


def md_(s: str) -> str:
    return md(s).replace("\n\n", "\n")  # type: ignore[no-any-return]


def to_aws_context(
    d: Tree, parent: Optional[str], base_directory: Path
) -> WithSuccessFailureCount[Tree]:
    if not isinstance(d, dict):
        return WithSuccessFailureCount.zero(d)
    d_: WithSuccessFailureCount[Tree] = WithSuccessFailureCount.zero({})
    for k, v in d.items():
        if k == AWSSpecification.DOCUMENTATION:
            content = file_content(base_directory, v)
            doc_with_counts = documentation(content, v, parent)
            doc = d_.value[
                AWSSpecification.MARKDOWN_DOCUMENTATION
            ] = doc_with_counts.value
            d_ = d_.add_counts(doc_with_counts)
            d_.value[AWSSpecification.REF_RETURN_VALUE] = ref_return_value(
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
                d_.value[AWSSpecification.ALLOWED_VALUES] = allowed_values
                if len(allowed_values_line) > MAX_ALLOWED_VALUES_WIDTH:
                    new_line = (
                        " | ".join(allowed_values)[: MAX_ALLOWED_VALUES_WIDTH - 3]
                        + "..."
                    )
                    lines[idx] = f"{ALLOWED_VALUES_PREFIX} `{new_line}`"
                    d_.value[AWSSpecification.MARKDOWN_DOCUMENTATION] = "\n".join(lines)
        if (
            isinstance(v, dict)
            and AWSSpecification.ATTRIBUTES in v
            and AWSSpecification.DOCUMENTATION in v
        ):
            set_attribute_doc(
                v[AWSSpecification.DOCUMENTATION],
                v[AWSSpecification.ATTRIBUTES],
            )
        sub_d_with_counts = to_aws_context(v, k, base_directory)
        d_.value[k] = sub_d_with_counts.value
        d_ = d_.add_counts(sub_d_with_counts)
    return d_


def set_attribute_doc(base_link: str, attribs_dct: Tree) -> None:
    for attrib, attrib_dct in attribs_dct.items():
        id_ = f"{base_link}#{attrib}-fn::getatt"
        attrib_dct[AWSSpecification.DOCUMENTATION] = id_


@functools.lru_cache(maxsize=None)
def file_content(
    base_directory: Path,
    link: str,
    on_fail_try_download: bool = True,
) -> BeautifulSoup:
    def read_file(loc: Path) -> BeautifulSoup:
        return BeautifulSoup(loc.read_text(), features="lxml")

    location = link.split("/")[-1].lstrip("/")
    if "#" in link:  # Subprop
        sub_path, _, id_ = location.partition("#")
        file_path = base_directory / sub_path
        try:
            return read_file(file_path)
        except FileNotFoundError:
            if on_fail_try_download:
                try_download(link, file_path)
                return file_content(base_directory, link, on_fail_try_download=False)
            logger.info("No file found for %s", link)
            return BeautifulSoup("")
    else:  # resource
        file_path = base_directory / location
        logger.debug("Processing %s", file_path)
        try:
            return read_file(file_path)
        except FileNotFoundError:
            if on_fail_try_download:
                try_download(link, file_path)
                return file_content(base_directory, link, on_fail_try_download=False)
            logger.info("No file found for %s", link)
            return BeautifulSoup("")


def documentation(
    content: BeautifulSoup, link: str, parent: Optional[str]
) -> WithSuccessFailureCount[str]:
    if "#" in link:  # Subprop
        # Sometimes the link is out of date (redirect), we guess the true id link using the h1 attrib
        split = link.split("#")
        id_, url_split = split[-1], split[0].split("/")
        replace: Callable[[str], str] = lambda s: s.replace(
            "aws-properties", "cfn"
        ).replace("aws-resource", "cfn")
        old_id_prefix = replace(remove_suffix(url_split[-1], ".html"))
        header = content.find("h1")
        if header and hasattr(header, "attrs"):
            true_id_prefix = replace(header.attrs["id"])
            true_id = id_.replace(old_id_prefix, true_id_prefix)
            if true_id != id_:
                logger.info("Replaced %s with %s", id_, true_id)
        else:
            true_id = id_
        dt = content.find("dt", {"id": true_id})
        if not dt:
            logger.error(
                "No documentation found for prop %s using id %s", link, true_id
            )
            return WithSuccessFailureCount.failure("")
        dd = dt.findNext("dd")
        doc = md_(str(dd)) if dd else ""
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
        doc = md_("".join(map(str, tags))) if tags else ""

    s = f"`{parent if parent else ''}`\n{doc}"
    if doc:
        return WithSuccessFailureCount.success(s)
    logger.error("Documentation for %s was found to be empty", link)
    return WithSuccessFailureCount.failure(s)


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
    return md_("".join(map(str, p_tags))) if p_tags else ""


def run_command(cmd: str) -> None:
    logger.info("Running '%s'", cmd)
    os.system(cmd)


def try_download(url: str, out_file_name: Path) -> None:
    run_command(f"curl -L -X GET {url} > {out_file_name.absolute()}")


def run(
    spec_file: Optional[Path],
    documentation_directory: Optional[Path],
    out_path: Optional[Path],
) -> None:
    out_path = out_path or Path("new-aws-context.json").absolute()
    if spec_file:
        spec_json = json.loads(spec_file.read_bytes())
    else:
        logger.info("Downloading spec from %s", DEFAULT_SPEC_URL)
        # requests handles gzip OOTB unlike urllib
        spec_json = json.loads(requests.get(DEFAULT_SPEC_URL).text)
    with tempfile.TemporaryDirectory() as tmp_directory:
        os.chdir(tmp_directory)
        doc_dir = documentation_directory or (
            Path("docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide")
        )
        if not documentation_directory:
            logger.info("Downloading documentation from %s...", doc_dir)
            run_command(f"wget --no-parent -r https://{doc_dir}")
        else:
            logger.info(
                "Not downloading documentation, using existing directory %s",
                documentation_directory,
            )
        ctx_map, md_succ, md_fails = to_aws_context(spec_json, None, doc_dir).to_tuple()
        ctx_map[PARSE_SUCCESS_RATIO_KEY] = round(md_succ / (md_fails + md_succ), 4)
        logger.info("Failed getting markdown: %d/%d", md_fails, md_fails + md_succ)
        with open(out_path, "w") as f_:
            json.dump(ctx_map, f_, indent=2)
    logger.info("Wrote context to %s", out_path)
