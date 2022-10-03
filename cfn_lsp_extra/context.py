"""
Utilities for loading the aws cloudformation doc content.
"""
import asyncio
import json
import logging
from collections import ChainMap
from importlib.resources import open_text
from importlib.resources import read_text
from pathlib import Path
from typing import MutableMapping

from platformdirs import PlatformDirs

from .aws_data import AWSContext
from .aws_data import AWSContextMap
from .aws_data import AWSName
from .aws_data import Tree
from .scrape.markdown import SAM_BASE_URL
from .scrape.markdown import parse_urls


logger = logging.getLogger(__name__)
dirs = PlatformDirs("cfn-lsp-extra", "cfn-lsp-extra")
CFN_OVERRIDE_CTX_PATH = Path(dirs.user_config_dir) / "context.json"
SAM_OVERRIDE_CTX_PATH = Path(dirs.user_config_dir) / "sam_context.json"
custom_ctx_path = Path(dirs.user_config_dir) / "custom.json"


def download_context(
    cfn_path: Path = CFN_OVERRIDE_CTX_PATH, sam_path: Path = SAM_OVERRIDE_CTX_PATH
) -> None:
    # Not using importlib.resources.files is considered legacy but is
    # necessary for python < 3.9
    cfn_urls = read_text("cfn_lsp_extra.resources", "doc_urls").splitlines()
    logger.info("CFN: Downloading documentation from %s urls", len(cfn_urls))
    cfn_ctx_map = asyncio.run(parse_urls(cfn_urls))

    sam_urls = read_text("cfn_lsp_extra.resources", "sam_doc_urls").splitlines()
    logger.info("SAM: Downloading documentation from %s urls", len(sam_urls))
    sam_ctx_map = asyncio.run(parse_urls(sam_urls, base_url=SAM_BASE_URL))
    cfn_path.parent.mkdir(parents=True, exist_ok=True)
    with cfn_path.open("w") as f:
        json.dump({"resources": cfn_ctx_map.resources}, f, indent=2, sort_keys=True)
    logger.info("Wrote CFN context to %s", cfn_path)
    with sam_path.open("w") as f:
        json.dump({"resources": sam_ctx_map.resources}, f, indent=2, sort_keys=True)
    logger.info("Wrote SAM context to %s", sam_path)


def with_custom(
    context_map: MutableMapping[AWSName, Tree], custom_path: Path = custom_ctx_path
) -> AWSContext:
    """Overwrite part of context with custom content."""
    logger.info("Updating context using custom file %s", custom_path)
    with open_text("cfn_lsp_extra.resources", "custom.json") as f:
        context_map = ChainMap(AWSContextMap(**json.load(f)), context_map)
    if custom_path.exists():
        logger.info("Updating context using user custom file %s", custom_path)
        with custom_path.open("r") as f:
            context_map = ChainMap(AWSContextMap(**json.load(f)), context_map)
    return AWSContext(resource_map=context_map)


def load_context(
    resource: str, override_path: Path = CFN_OVERRIDE_CTX_PATH
) -> AWSContext:
    """Load AWS context from a cache."""
    if override_path.exists():
        logger.info("Loading custom context from %s", override_path)
        with override_path.open("r") as f:
            return with_custom(AWSContextMap(**json.load(f)))
    else:
        logger.info("Loading context...")
        with open_text("cfn_lsp_extra.resources", resource) as f:
            return with_custom(AWSContextMap(**json.load(f)))


def load_cfn_context() -> AWSContext:
    return load_context("context.json", CFN_OVERRIDE_CTX_PATH)


def load_sam_context(cfn_context: AWSContext) -> AWSContext:
    return AWSContext(
        resource_map=ChainMap(
            load_context("sam_context.json", SAM_OVERRIDE_CTX_PATH).resource_map,
            cfn_context.resource_map,
        )
    )
