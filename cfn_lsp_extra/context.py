"""
Utilities for loading the aws cloudformation doc content.
"""
import asyncio
import json
import logging
from importlib.resources import read_text
from pathlib import Path

from platformdirs import PlatformDirs

from .scrape.markdown import AWSContext
from .scrape.markdown import parse_urls


logger = logging.getLogger(__name__)
dirs = PlatformDirs("cfn-lsp-extra", "cfn-lsp-extra")
ctx_path = Path(dirs.user_cache_dir) / "context.json"


def download_context() -> AWSContext:
    # Not using importlib.resources.files is considered legacy but is
    # necessary for python < 3.9
    urls = read_text("cfn_lsp_extra.resources", "doc_urls").splitlines()
    return asyncio.run(parse_urls(urls))


def load_context(ctx_path: Path = ctx_path, void_cache: bool = False) -> AWSContext:
    if not ctx_path.exists or void_cache:
        context: AWSContext = download_context()
        ctx_path.parent.mkdir(parents=True, exist_ok=True)
        with ctx_path.open("w") as f:
            json.dump(context.dict(), f)
    else:
        with ctx_path.open("r") as f:
            context = AWSContext(**json.load(f))
    return context


def cache(path: Path = ctx_path, void_cache: bool = False) -> AWSContext:
    """Return the AWS context cache from path, optionally voiding it."""
    if not path.exists or void_cache:
        logger.info(f"Loading context into {path}...")
        load_context(path, void_cache=True)
        logger.info(f"Finished downloading context to {path}")
    else:
        logger.info(f"Found context at {path}")
        load_context(path, void_cache=False)
