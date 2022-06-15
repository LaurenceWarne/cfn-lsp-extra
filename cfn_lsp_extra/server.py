"""
LSP implementation
https://pygls.readthedocs.io/en/latest/
https://microsoft.github.io/language-server-protocol/specifications/specification-current/
"""

import logging
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
from pygls.lsp.types.language_features.completion import CompletionList
from pygls.lsp.types.language_features.completion import CompletionOptions
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
from .completions import completions_for
from .decode import decode
from .decode import decode_unfinished


logger = logging.getLogger(__name__)


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

    @server.feature(COMPLETION, CompletionOptions(trigger_characters=["!"]))
    def completions(
        ls: LanguageServer, params: CompletionParams
    ) -> Optional[CompletionList]:
        """Returns completion items."""
        line_at = params.position.line
        uri = params.text_document.uri
        document = server.workspace.get_document(uri)
        try:
            template_data = decode_unfinished(
                document.source, document.filename, line_at
            )
        except CfnDecodingException:
            return None
        return completions_for(template_data, aws_context, document, params.position)

    @server.feature(HOVER)
    def did_hover(ls: LanguageServer, params: HoverParams) -> Optional[Hover]:
        """Text document did hover notification."""
        line_at, char_at = params.position.line, params.position.character
        uri = params.text_document.uri
        document = server.workspace.get_document(uri)
        try:
            template_data = decode(document.source, document.filename)
        except CfnDecodingException:
            return None
        position_lookup = extractor.extract(template_data)
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
