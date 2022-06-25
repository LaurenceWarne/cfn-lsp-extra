"""
LSP implementation
https://pygls.readthedocs.io/en/latest/
https://microsoft.github.io/language-server-protocol/specifications/specification-current/
"""

import logging
import re
from typing import Optional
from typing import Union

from pygls.lsp.methods import COMPLETION
from pygls.lsp.methods import COMPLETION_ITEM_RESOLVE
from pygls.lsp.methods import DEFINITION
from pygls.lsp.methods import HOVER
from pygls.lsp.methods import TEXT_DOCUMENT_DID_CHANGE
from pygls.lsp.methods import TEXT_DOCUMENT_DID_OPEN
from pygls.lsp.types import CompletionItem
from pygls.lsp.types import CompletionList
from pygls.lsp.types import CompletionOptions
from pygls.lsp.types import CompletionParams
from pygls.lsp.types import DefinitionParams
from pygls.lsp.types import DidChangeTextDocumentParams
from pygls.lsp.types import DidOpenTextDocumentParams
from pygls.lsp.types import Hover
from pygls.lsp.types import HoverParams
from pygls.lsp.types import Location
from pygls.lsp.types import MarkupContent
from pygls.lsp.types import MarkupKind
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.server import LanguageServer

from .aws_data import AWSContext
from .aws_data import AWSPropertyName
from .aws_data import AWSRefName
from .aws_data import AWSResourceName
from .cfnlint_integration import diagnostics  # type: ignore[attr-defined]
from .completions import completions_for
from .completions.resources import resolve_resource_completion_item
from .decode import CfnDecodingException
from .decode import decode
from .decode import decode_unfinished
from .decode.extractors import CompositeExtractor
from .decode.extractors import KeyExtractor
from .decode.extractors import ResourceExtractor
from .decode.extractors import ResourcePropertyExtractor
from .ref import resolve_ref


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

    @server.feature(
        COMPLETION,
        CompletionOptions(trigger_characters=["!", '"'], resolve_provider=True),
    )
    def completions(
        ls: LanguageServer, params: CompletionParams
    ) -> Optional[CompletionList]:
        """Returns completion items."""
        uri = params.text_document.uri
        document = server.workspace.get_document(uri)
        try:
            template_data = decode_unfinished(
                document.source, document.filename, params.position
            )
        except CfnDecodingException as e:
            logger.debug(f"Failed to decode document: {e}")
            return None
        return completions_for(template_data, aws_context, document, params.position)

    @server.feature(COMPLETION_ITEM_RESOLVE)
    def completion_item_resolve(
        ls: LanguageServer, completion_item: CompletionItem
    ) -> CompletionItem:
        """Resolves a completion item."""
        if re.match(r"^.+::.+::.+$", completion_item.label):
            return resolve_resource_completion_item(completion_item, aws_context)
        else:
            return completion_item  # Not a resource

    @server.feature(HOVER)
    def did_hover(ls: LanguageServer, params: HoverParams) -> Optional[Hover]:
        """Text document did hover notification."""
        line_at, char_at = params.position.line, params.position.character
        uri = params.text_document.uri
        document = server.workspace.get_document(uri)
        try:
            template_data = decode(document.source, document.filename)
        except CfnDecodingException as e:
            logger.debug(f"Failed to decode document: {e}")
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

    @server.feature(DEFINITION)
    def goto_definition(
        ls: LanguageServer, params: DefinitionParams
    ) -> Optional[Location]:
        logger.info("CALLED GOTO DEFINITION")
        line_at, char_at = params.position.line, params.position.character
        document = server.workspace.get_document(params.text_document.uri)
        try:
            template_data = decode(document.source, document.filename)
        except CfnDecodingException as e:
            logger.debug(f"Failed to decode document: {e}")
            return None
        ref_extractor = KeyExtractor[AWSRefName]("Ref", lambda s: AWSRefName(value=s))
        ref_lookup = ref_extractor.extract(template_data)
        logger.info(template_data)
        logger.info(ref_lookup)
        span = ref_lookup.at(line_at, char_at)
        logger.info(f"FOUND SPAN {span}")
        if span:
            from .decode.extractors import ParameterExtractor

            param_extractor = ParameterExtractor()
            param_lookup = param_extractor.extract(template_data)
            logger.info(list(param_lookup.items()))
            position = resolve_ref(span.value, template_data)
            if position:
                return Location(
                    uri=document.uri,
                    range=Range(
                        start=position,
                        end=Position(
                            line=position.line,
                            character=position.character + len(span.value.value),
                        ),
                    ),
                )
        else:
            return None

    return server
