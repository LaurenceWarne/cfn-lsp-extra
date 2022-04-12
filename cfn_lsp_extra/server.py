"""
LSP implementation
https://pygls.readthedocs.io/en/latest/
https://microsoft.github.io/language-server-protocol/specifications/specification-current/
"""

import asyncio
import logging
from importlib.resources import read_text
from typing import Dict
from typing import List
from typing import Optional

import click
import yaml
from pygls.lsp.methods import HOVER
from pygls.lsp.methods import TEXT_DOCUMENT_DID_OPEN
from pygls.lsp.types import DidOpenTextDocumentParams
from pygls.lsp.types import Hover
from pygls.lsp.types import HoverParams
from pygls.lsp.types import MarkupContent
from pygls.lsp.types import MarkupKind
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.server import LanguageServer
from pygls.server import LanguageServerProtocol

from .context import cache
from .context import download_context
from .parsing import SafePositionLoader
from .parsing import flatten_mapping
from .scrape.markdown import AWSContext
from .scrape.markdown import AWSResource
from .scrape.markdown import parse_urls


class CfnLanguageServer(LanguageServer):
    def __init__(
        self,
        aws_context: AWSContext,
        loop=None,
        protocol_cls=LanguageServerProtocol,
        max_workers: int = 2,
    ):
        super().__init__(loop, protocol_cls, max_workers)
        self.aws_context = aws_context


def server(aws_context: AWSContext) -> CfnLanguageServer:
    server = CfnLanguageServer(aws_context)

    @server.feature(TEXT_DOCUMENT_DID_OPEN)
    async def did_open(ls: CfnLanguageServer, params: DidOpenTextDocumentParams):
        """Text document did open notification."""
        ls.show_message("Text Document Did Open")
        params.text_document.text

    @server.feature(HOVER)
    def did_hover(ls: CfnLanguageServer, params: HoverParams) -> Optional[Hover]:
        """Text document did hover notification."""
        line_at, char_at = params.position.line, params.position.character
        uri = params.text_document.uri
        document = server.workspace.get_document(uri)
        # Parse document
        try:
            data = yaml.load(document.source, Loader=SafePositionLoader)
        except yaml.scanner.ScannerError:  # Invalid yaml
            return
        props = flatten_mapping(data)
        for aws_prop, positions in props.items():
            if not (
                aws_prop.resource in ls.aws_context.resources
                and aws_prop.property_
                in ls.aws_context.resources[aws_prop.resource].property_descriptions
            ):
                continue
            for line, column in positions:
                column_max = column + len(aws_prop.property_)
                within_col = column <= char_at <= column_max
                if line == line_at and within_col:
                    return Hover(
                        range=Range(
                            start=Position(line=line, character=column),
                            end=Position(line=line, character=column_max),
                        ),
                        contents=MarkupContent(
                            kind=MarkupKind.Markdown,
                            value=ls.aws_context[aws_prop],
                        ),
                    )

    return server


@click.command()
@click.version_option()
@click.option("-v", "--verbose", is_flag=True, help="Print more output.")
@click.option("--no-cache", is_flag=True, help="Don't use cached documentation.")
@click.option(
    "--generate-cache",
    is_flag=True,
    help="Generate the documentation cache and exit.",
)
def main(verbose: bool, no_cache: bool, generate_cache: bool) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
    if generate_cache:
        cache(void_cache=True)
        return
    no_cache = True
    aws_context = download_context() if no_cache else cache()
    server(aws_context).start_io()


if __name__ == "__main__":
    main(auto_envvar_prefix="CFN_LSP_EXTRA")
