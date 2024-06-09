"""
Utilities for loading the aws cloudformation doc content.
"""
import json
import logging
from collections import ChainMap
from pathlib import Path

from importlib_resources import as_file, files
from platformdirs import PlatformDirs

from .aws_data import AWSContext, AWSSpecification, Tree

logger = logging.getLogger(__name__)
dirs = PlatformDirs("cfn-lsp-extra", "cfn-lsp-extra")
CFN_OVERRIDE_CTX_PATH = Path(dirs.user_config_dir) / "context.json"
SAM_OVERRIDE_CTX_PATH = Path(dirs.user_config_dir) / "sam_context.json"
custom_ctx_path = Path(dirs.user_config_dir) / "custom.json"


def with_custom(context_map: Tree, custom_path: Path = custom_ctx_path) -> AWSContext:
    """Overwrite part of context with custom content."""
    logger.info("Updating context using custom file %s", custom_path)
    source = files("cfn_lsp_extra.resources").joinpath("custom.json")
    with as_file(source) as path, open(path, "r") as f:
        context_map = ChainMap(json.load(f), context_map)
    if custom_path.exists():
        logger.info("Updating context using user custom file %s", custom_path)
        with custom_path.open("r") as f:
            context_map = ChainMap(json.load(f), context_map)
    return AWSContext(
        resource_map=context_map[AWSSpecification.RESOURCE_TYPES],
        property_map=context_map[AWSSpecification.PROPERTY_TYPES],
    )


def load_context(
    resource: str, override_path: Path = CFN_OVERRIDE_CTX_PATH
) -> AWSContext:
    """Load AWS context from a cache."""
    if override_path.exists():
        logger.info("Loading custom context from %s", override_path)
        with override_path.open("r") as f:
            d = json.load(f)
            return AWSContext(
                d[AWSSpecification.RESOURCE_TYPES], d[AWSSpecification.PROPERTY_TYPES]
            )
    else:
        logger.info("Loading context...")
        source = files("cfn_lsp_extra.resources").joinpath(resource)
        with as_file(source) as path, open(path, "r") as f:
            return with_custom(json.load(f))


def load_cfn_context() -> AWSContext:
    return load_context("context.json", CFN_OVERRIDE_CTX_PATH)


def load_sam_context(cfn_context: AWSContext) -> AWSContext:
    return load_context("sam_context.json", SAM_OVERRIDE_CTX_PATH)
