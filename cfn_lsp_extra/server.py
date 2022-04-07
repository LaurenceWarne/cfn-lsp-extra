"""
LSP implementation
https://pygls.readthedocs.io/en/latest/
https://microsoft.github.io/language-server-protocol/specifications/specification-current/
"""

import sys
from typing import Optional

import click
from pygls.lsp.methods import (
    COMPLETION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_CLOSE,
    TEXT_DOCUMENT_DID_OPEN,
    HOVER,
    TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL,
)
from pygls.lsp.types import (
    CompletionItem,
    CompletionList,
    CompletionOptions,
    CompletionParams,
    ConfigurationItem,
    ConfigurationParams,
    Diagnostic,
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    HoverParams,
    Hover,
    MarkupContent,
    MarkupKind,
    DidOpenTextDocumentParams,
    MessageType,
    Position,
    Range,
    Registration,
    RegistrationParams,
    SemanticTokens,
    SemanticTokensLegend,
    SemanticTokensParams,
    Unregistration,
    UnregistrationParams,
)
from pygls.server import LanguageServer
import yaml

from .parsing import SafePositionLoader, flatten_mapping


server = LanguageServer()


@server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    ls.show_message("Text Document Did Open")
    params.text_document.text


@server.feature(HOVER)
def did_hover(ls, params: HoverParams) -> Optional[Hover]:
    """Text document did hover notification."""
    line_at, char = params.position.line, params.position.character - 1
    uri = params.text_document.uri
    document = server.workspace.get_document(uri)
    # Parse document
    data = yaml.load(document.source, Loader=SafePositionLoader)
    props = flatten_mapping(data)
    for aws_prop, positions in props.items():
        for line, column in positions:
            column_max = column + len(aws_prop.property_)
            within_col = column <= char <= column_max
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
