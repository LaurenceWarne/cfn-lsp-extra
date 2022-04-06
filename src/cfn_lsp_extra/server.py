"""
LSP implementation
https://pygls.readthedocs.io/en/latest/
https://microsoft.github.io/language-server-protocol/specifications/specification-current/
"""
import click
from pygls.lsp.methods import (COMPLETION, TEXT_DOCUMENT_DID_CHANGE,
                               TEXT_DOCUMENT_DID_CLOSE, TEXT_DOCUMENT_DID_OPEN,
                               HOVER, TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL)
from pygls.lsp.types import (CompletionItem, CompletionList, CompletionOptions,
                             CompletionParams, ConfigurationItem,
                             ConfigurationParams, Diagnostic,
                             DidChangeTextDocumentParams,
                             DidCloseTextDocumentParams,
                             HoverParams, Hover, MarkedString,
                             DidOpenTextDocumentParams, MessageType, Position,
                             Range, Registration, RegistrationParams,
                             SemanticTokens, SemanticTokensLegend, SemanticTokensParams,
                             Unregistration, UnregistrationParams)
from pygls.server import LanguageServer


server = LanguageServer()

@server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    ls.show_message('Text Document Did Open')
    params.text_document.text


@server.feature(HOVER)
def did_hover(ls, params: HoverParams) -> Optional[Hover]:
    """Text document did open notification."""
    line, char = params.position.line, params.position.character
    uri = params.text_document.uri
    document = server.workspace.get_document(uri)
    line_text = document.lines[line]
    ls.show_message(line_text)
    return Hover(
        range=Range(
            start=Position(line=line, character=char-1),
            end=Position(line=line, character=char + 1)
        )
        contents=MarkedString(line_text)
    )
    

@click.command()
@click.version_option()
def main() -> None:
    server.start_tcp('127.0.0.1', 8080)

if __name__ == "__main__":
    main()
