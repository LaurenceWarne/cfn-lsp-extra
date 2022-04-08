"""
LSP implementation
https://pygls.readthedocs.io/en/latest/
https://microsoft.github.io/language-server-protocol/specifications/specification-current/
"""

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

from .parsing import SafePositionLoader
from .parsing import flatten_mapping


server = LanguageServer()


@server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    ls.show_message("Text Document Did Open")
    params.text_document.text


@server.feature(HOVER)
def did_hover(ls, params: HoverParams) -> Optional[Hover]:
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
            if line == line_at and within_col:
                return Hover(
                    range=Range(
                        start=Position(line=line, character=column),
                        end=Position(line=line, character=column_max),
                    ),
                    contents=MarkupContent(
                        kind=MarkupKind.Markdown, value=str(aws_prop)
                    ),
                )


@click.command()
@click.version_option()
def main() -> None:
    server.start_io()


if __name__ == "__main__":
    main()
