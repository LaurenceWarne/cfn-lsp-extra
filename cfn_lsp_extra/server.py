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

from .parsing import SafePositionLoader
from .parsing import flatten_mapping
from .scrape.markdown import AWSResource
from .scrape.markdown import parse_urls


class CfnLanguageServer(LanguageServer):
    def __init__(
        self,
        aws_resources: List[AWSResource],
        loop=None,
        protocol_cls=LanguageServerProtocol,
        max_workers: int = 2,
    ):
        super().__init__(loop, protocol_cls, max_workers)
        self.aws_resources = aws_resources


def server() -> CfnLanguageServer:
    # logger.info("Parsing documentation from cloudformation docs...")
    urls = (
        # Not using importlib.resources.files is considered legacy but is
        # necessary for python < 3.9
        read_text("cfn_lsp_extra.resources", "doc_urls").splitlines()
    )
    descriptions = asyncio.run(parse_urls(urls))
    # logger.info("Done parsing documentation")
    server = CfnLanguageServer(descriptions)

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
                aws_prop.resource in ls.aws_resources
                and aws_prop.property_
                in ls.aws_resources[aws_prop.resource].property_descriptions
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
                            value=ls.aws_resources[aws_prop.resource][
                                aws_prop.property_
                            ],
                        ),
                    )

    return server


@click.command()
@click.version_option()
def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    server().start_io()


if __name__ == "__main__":
    main()
