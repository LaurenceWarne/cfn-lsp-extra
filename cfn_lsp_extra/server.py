"""
LSP implementation
https://pygls.readthedocs.io/en/latest/
https://microsoft.github.io/language-server-protocol/specifications/specification-current/
"""

import asyncio
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
        aws_resources: list[AWSResource],
        loop=None,
        protocol_cls=LanguageServerProtocol,
        max_workers: int = 2,
    ):
        super().__init__(loop, protocol_cls, max_workers)
        self.aws_resources = aws_resources


def server() -> CfnLanguageServer:
    descriptions = asyncio.run(
        parse_urls(
            [
                "https://raw.githubusercontent.com/awsdocs/aws-cloudformation-user-guide/main/doc_source/aws-properties-ec2-instance.md",
                "https://raw.githubusercontent.com/awsdocs/aws-cloudformation-user-guide/main/doc_source/aws-resource-ec2-subnet.md",
            ]
        )
    )
    server = CfnLanguageServer(descriptions)

    @server.feature(TEXT_DOCUMENT_DID_OPEN)
    async def did_open(ls: CfnLanguageServer, params: DidOpenTextDocumentParams):
        """Text document did open notification."""
        ls.show_message("Text Document Did Open")
        params.text_document.text

    @server.feature(HOVER)
    def did_hover(ls: CfnLanguageServer, params: HoverParams) -> Optional[Hover]:
        """Text document did hover notification."""
        line_at, char_at = params.position.line, params.position.character - 1
        uri = params.text_document.uri
        document = server.workspace.get_document(uri)
        # Parse document
        data = yaml.load(document.source, Loader=SafePositionLoader)
        props = flatten_mapping(data)
        for aws_prop, positions in props.items():
            for line, column in positions:
                column_max = column + len(aws_prop.property_)
                within_col = column <= char_at <= column_max
                if (
                    line == line_at
                    and within_col
                    and aws_prop.resource in ls.aws_resources
                ):
                    return Hover(
                        range=Range(
                            start=Position(line=line, character=column),
                            end=Position(line=line, character=column_max),
                        ),
                        contents=MarkupContent(
                            kind=MarkupKind.Markdown,
                            value=ls.aws_resources[
                                aws_prop.resource
                            ].property_descriptions[aws_prop.property_],
                        ),
                    )

    return server


@click.command()
@click.version_option()
def main() -> None:
    server().start_io()


if __name__ == "__main__":
    main()
