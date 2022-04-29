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
ctx_path_override = Path(dirs.user_cache_dir) / "context.json"


def download_context(path: Path = ctx_path_override) -> None:
    # Not using importlib.resources.files is considered legacy but is
    # necessary for python < 3.9
    urls = read_text("cfn_lsp_extra.resources", "doc_urls").splitlines()
    logger.info(f"Downloading documentation from {len(urls)} urls")
    ctx = asyncio.run(parse_urls(urls))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(ctx.dict(), f, indent=2, sort_keys=True)


def load_context(override_path: Path = ctx_path_override) -> AWSContext:
    """Load AWS context from a cache."""
    if override_path.exists:
        logger.info(f"Loading custom context from {override_path}")
        with override_path.open("r") as f:
            return AWSContext(**json.load(f))
    else:
        logger.info("Loading context...")  # type: ignore[unreachable]
        with open_text("cfn_lsp_extra.resources", "context.json") as f:
            return AWSContext(**json.load(f))
