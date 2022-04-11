"""
Utilities for loading the aws cloudformation doc content.
"""
import asyncio
import json
import logging
from importlib.resources import read_text
from pathlib import Path

from platformdirs import PlatformDirs

from .scrape.markdown import parse_urls


dirs = PlatformDirs("cfn-lsp-extra", "cfn-lsp-extra")

logger = logging.getLogger(__name__)


class SourceLoader:
    def load(self):
        urls = (
            # Not using importlib.resources.files is considered legacy but is
            # necessary for python < 3.9
            read_text("cfn_lsp_extra.resources", "doc_urls").splitlines()
        )
        return asyncio.run(parse_urls(urls))


class ContextLoader(SourceLoader):
    def __init__(self, ctx_path=Path(dirs.user_cache_dir) / "context.json"):
        self.ctx_path = ctx_path

    def load(self):
        if not self.ctx_path.exists:
            context = super.load()
            with open(self.ctx_path, "w") as f:
                f.write(json.dump(context))
        else:
            with open(self.ctx_path, "r") as f:
                context = json.load(f)
        return context
