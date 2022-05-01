"""
LSP implementation
https://pygls.readthedocs.io/en/latest/
https://microsoft.github.io/language-server-protocol/specifications/specification-current/
"""

from typing import Optional
from typing import Union

from pygls.lsp.methods import COMPLETION
from pygls.lsp.methods import HOVER
from pygls.lsp.methods import TEXT_DOCUMENT_DID_CHANGE
from pygls.lsp.methods import TEXT_DOCUMENT_DID_OPEN
from pygls.lsp.types import DidChangeTextDocumentParams
from pygls.lsp.types import DidOpenTextDocumentParams
from pygls.lsp.types import Hover
from pygls.lsp.types import HoverParams
from pygls.lsp.types import MarkupContent
from pygls.lsp.types import MarkupKind
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.lsp.types.language_features.completion import CompletionItem
from pygls.lsp.types.language_features.completion import CompletionList
from pygls.lsp.types.language_features.completion import CompletionParams
from pygls.server import LanguageServer

from cfn_lsp_extra.decode import CfnDecodingException
from cfn_lsp_extra.decode.extractors import CompositeExtractor
from cfn_lsp_extra.decode.extractors import ResourceExtractor
from cfn_lsp_extra.decode.extractors import ResourcePropertyExtractor

from .aws_data import AWSContext
from .aws_data import AWSPropertyName
from .aws_data import AWSResourceName
from .cfnlint_integration import diagnostics  # type: ignore[attr-defined]
from .decode import decode


def server(aws_context: AWSContext) -> LanguageServer:
    server = LanguageServer()
    extractor = CompositeExtractor[Union[AWSResourceName, AWSPropertyName]](
        ResourcePropertyExtractor(), ResourceExtractor()
    )

    @server.thread()
    @server.feature(TEXT_DOCUMENT_DID_OPEN)
    def did_open(ls: LanguageServer, params: DidOpenTextDocumentParams) -> None:
        """Text document did open notification."""
        ls.show_message("Text Document Did Open")
        text_doc = ls.workspace.get_document(params.text_document.uri)
        file_path = text_doc.path
        ls.publish_diagnostics(text_doc.uri, diagnostics(text_doc.source, file_path))

    @server.thread()
    @server.feature(TEXT_DOCUMENT_DID_CHANGE)
    def did_change(ls: LanguageServer, params: DidChangeTextDocumentParams) -> None:
        """Text document did change notification."""
        text_doc = ls.workspace.get_document(params.text_document.uri)
        file_path = text_doc.path
        diags = diagnostics(text_doc.source, file_path)
        # Publishing diagnostics removes old ones
        ls.publish_diagnostics(text_doc.uri, diags)
        ls.show_message("Finished processing Text Document Did Change")

    @server.feature(COMPLETION)
    def completions(
        ls: LanguageServer, params: CompletionParams
    ) -> Optional[CompletionList]:
        """Returns completion items."""
        line_at, char_at = params.position.line, params.position.character
        uri = params.text_document.uri
        document = server.workspace.get_document(uri)
        try:
            position_lookup = decode(document.source, document.filename, extractor)
        except CfnDecodingException:
            # Try adding a ':' and see if that makes the yaml valid
            new_source_lst = document.source.splitlines()
            new_source_lst[line_at] = new_source_lst[line_at].rstrip() + ":"
            new_source = "\n".join(new_source_lst)
            position_lookup = decode(new_source, document.filename, extractor)

        span = position_lookup.at(line_at, char_at)
        if not span:
            return None
        name = span.value

        completions = aws_context.same_level(name)
        add_documentation = isinstance(name, AWSPropertyName)
        return CompletionList(
            is_incomplete=name.split()[-1] not in completions,
            items=[
                CompletionItem(
                    label=s,
                    documentation=aws_context.description(name.parent / s)
                    if add_documentation
                    else None,
                )
                for s in completions
            ],
        )

    @server.feature(HOVER)
    def did_hover(ls: LanguageServer, params: HoverParams) -> Optional[Hover]:
        """Text document did hover notification."""
        line_at, char_at = params.position.line, params.position.character
        uri = params.text_document.uri
        document = server.workspace.get_document(uri)
        try:
            position_lookup = decode(document.source, document.filename, extractor)
        except CfnDecodingException:
            return None
        span = position_lookup.at(line_at, char_at)
        if not span:
            return None

        # See if we can get a description from the obj wrapped by the span
        try:
            description = aws_context.description(span.value)
        except ValueError:  # no description for value, e.g. incomplete
            return None
        else:
            return Hover(
                range=Range(
                    start=Position(line=line_at, character=span.char),
                    end=Position(line=line_at, character=span.char + span.span),
                ),
                contents=MarkupContent(kind=MarkupKind.Markdown, value=description),
            )

    return server
