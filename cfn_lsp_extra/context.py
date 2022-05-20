"""
Utilities for loading the aws cloudformation doc content.
"""
import asyncio
import json
import logging
from importlib.resources import open_text
from importlib.resources import read_text
from pathlib import Path

from platformdirs import PlatformDirs

from .aws_data import AWSContext
from .scrape.markdown import parse_urls


logger = logging.getLogger(__name__)
dirs = PlatformDirs("cfn-lsp-extra", "cfn-lsp-extra")
override_ctx_path = Path(dirs.user_config_dir) / "context.json"
custom_ctx_path = Path(dirs.user_config_dir) / "custom.json"


def download_context(path: Path = override_ctx_path) -> None:
    # Not using importlib.resources.files is considered legacy but is
    # necessary for python < 3.9
    urls = read_text("cfn_lsp_extra.resources", "doc_urls").splitlines()
    logger.info(f"Downloading documentation from {len(urls)} urls")
    ctx = asyncio.run(parse_urls(urls))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(ctx.dict(), f, indent=2, sort_keys=True)


def with_custom(context: AWSContext, custom_path: Path = custom_ctx_path) -> AWSContext:
    """Overwrite part of context with custom content."""
    logger.info(f"Updating context using custom file {custom_path}")
    with open_text("cfn_lsp_extra.resources", "custom.json") as f:
        context.update(AWSContext(**json.load(f)))
    if custom_path.exists():
        logger.info(f"Updating context using custom file {custom_path}")
        with custom_path.open("r") as f:
            context.update(AWSContext(**json.load(f)))
    return context


def load_context(override_path: Path = override_ctx_path) -> AWSContext:
    """Load AWS context from a cache."""
    if override_path.exists():
        logger.info(f"Loading custom context from {override_path}")
        with override_path.open("r") as f:
            return with_custom(AWSContext(**json.load(f)))
    else:
        logger.info("Loading context...")
        with open_text("cfn_lsp_extra.resources", "context.json") as f:
            return with_custom(AWSContext(**json.load(f)))
