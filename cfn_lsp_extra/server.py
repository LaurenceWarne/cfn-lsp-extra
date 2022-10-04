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
from pygls.workspace import Document

from .aws_data import AWSContext
from .aws_data import AWSPropertyName
from .aws_data import AWSResourceName
from .cfnlint_integration import diagnostics  # type: ignore[attr-defined]
from .completions import completions_for
from .completions.resources import resolve_resource_completion_item
from .decode import CfnDecodingException
from .decode import decode
from .decode import decode_unfinished
from .decode.extractors import CompositeExtractor
from .decode.extractors import ResourceExtractor
from .decode.extractors import ResourcePropertyExtractor
from .ref import resolve_ref


logger = logging.getLogger(__name__)
TRIGGER_CHARACTERS = [
    ".",
    "Type: ",
    "!Ref ",
    "Ref: ",
    "!GetAtt ",
    "GetAtt: ",
    "!",
    '"Type": "',
    '"Ref": "',
    '"GetAtt": "',
    '"',
]


def server(cfn_aws_context: AWSContext, sam_aws_context: AWSContext) -> LanguageServer:
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
        logger.debug("Is template SAM: %s", is_document_sam(text_doc))
        file_path = text_doc.path
        ls.publish_diagnostics(text_doc.uri, diagnostics(text_doc.source, file_path))

    @server.thread()
    @server.feature(TEXT_DOCUMENT_DID_CHANGE)
    def did_change(ls: LanguageServer, params: DidChangeTextDocumentParams) -> None:
        """Text document did change notification."""
        text_doc = ls.workspace.get_document(params.text_document.uri)
        file_path = text_doc.path
        # Publishing diagnostics removes old ones
        ls.publish_diagnostics(text_doc.uri, diagnostics(text_doc.source, file_path))

    @server.feature(
        COMPLETION,
        CompletionOptions(trigger_characters=TRIGGER_CHARACTERS, resolve_provider=True),
    )
    def completions(
        ls: LanguageServer, params: CompletionParams
    ) -> Optional[CompletionList]:
        """Returns completion items."""
        uri = params.text_document.uri
        document = server.workspace.get_document(uri)
        aws_context = sam_aws_context if is_document_sam(document) else cfn_aws_context
        try:
            template_data = decode_unfinished(
                document.source, document.filename, params.position
            )
        except CfnDecodingException as e:
            logger.debug("Failed to decode document: %s", e)
            return None
        return completions_for(template_data, aws_context, document, params.position)

    @server.feature(COMPLETION_ITEM_RESOLVE)
    def completion_item_resolve(
        ls: LanguageServer, completion_item: CompletionItem
    ) -> CompletionItem:
        """Resolves a completion item."""
        if re.match(r"^.+::.+::.+$", completion_item.label):
            return resolve_resource_completion_item(completion_item, sam_aws_context)
        else:
            return completion_item  # Not a resource

    @server.feature(HOVER)
    def did_hover(ls: LanguageServer, params: HoverParams) -> Optional[Hover]:
        """Text document did hover notification."""
        line_at, char_at = params.position.line, params.position.character
        uri = params.text_document.uri
        document = server.workspace.get_document(uri)
        aws_context = sam_aws_context if is_document_sam(document) else cfn_aws_context
        try:
            template_data = decode(document.source, document.filename)
        except CfnDecodingException as e:
            logger.debug("Failed to decode document: %s", e)
            return None
        position_lookup = extractor.extract(template_data)
        span = position_lookup.at(line_at, char_at)

        if span:
            try:
                documentation = aws_context.description(span.value)
                char, length = span.char, span.span
            except KeyError:  # no description for value, e.g. incomplete
                return None
        else:  # Attempt to resolve it as a Ref
            link = resolve_ref(params.position, template_data)
            if link:
                documentation = link.source_span.value.as_documentation()
                char, length = link.target_span.char, link.target_span.span
            else:
                return None

        return Hover(
            range=Range(
                start=Position(line=line_at, character=char),
                end=Position(line=line_at, character=char + length),
            ),
            contents=MarkupContent(kind=MarkupKind.Markdown, value=documentation),
        )

    @server.feature(DEFINITION)
    def goto_definition(
        ls: LanguageServer, params: DefinitionParams
    ) -> Optional[Location]:
        document = server.workspace.get_document(params.text_document.uri)
        try:
            template_data = decode(document.source, document.filename)
        except CfnDecodingException as e:
            logger.debug("Failed to decode document: %s", e)
            return None
        link = resolve_ref(params.position, template_data)
        if link:
            return Location(
                uri=document.uri,
                range=Range(
                    start=Position(
                        line=link.source_span.line, character=link.source_span.char
                    ),
                    end=Position(
                        line=link.source_span.line,
                        character=link.source_span.char + link.source_span.span,
                    ),
                ),
            )
        return None

    return server


def is_document_sam(document: Document) -> bool:
    for line in document.lines:
        if not line.lstrip().startswith("#"):
            return line.rstrip() == "Transform: AWS::Serverless-2016-10-31"
    return False
