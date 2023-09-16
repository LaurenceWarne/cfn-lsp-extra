"""
LSP implementation
https://pygls.readthedocs.io/en/latest/
https://microsoft.github.io/language-server-protocol/specifications/specification-current/
"""

import logging
import re
from typing import Optional
from typing import Union

from lsprotocol.types import COMPLETION_ITEM_RESOLVE
from lsprotocol.types import INITIALIZED
from lsprotocol.types import TEXT_DOCUMENT_COMPLETION
from lsprotocol.types import TEXT_DOCUMENT_DEFINITION
from lsprotocol.types import TEXT_DOCUMENT_DID_CHANGE
from lsprotocol.types import TEXT_DOCUMENT_DID_OPEN
from lsprotocol.types import TEXT_DOCUMENT_DID_SAVE
from lsprotocol.types import TEXT_DOCUMENT_HOVER
from lsprotocol.types import WORKSPACE_DID_CHANGE_CONFIGURATION
from lsprotocol.types import CompletionItem
from lsprotocol.types import CompletionList
from lsprotocol.types import CompletionOptions
from lsprotocol.types import CompletionParams
from lsprotocol.types import DefinitionParams
from lsprotocol.types import DidChangeConfigurationParams
from lsprotocol.types import DidChangeTextDocumentParams
from lsprotocol.types import DidOpenTextDocumentParams
from lsprotocol.types import DidSaveTextDocumentParams
from lsprotocol.types import Hover
from lsprotocol.types import HoverParams
from lsprotocol.types import InitializedParams
from lsprotocol.types import Location
from pygls.server import LanguageServer
from pygls.workspace import Document

from .aws_data import AWSContext
from .aws_data import AWSPropertyName
from .aws_data import AWSResourceName
from .cfnlint_integration import diagnostics  # type: ignore[attr-defined]
from .completions import TRIGGER_CHARACTERS
from .completions import completions_for
from .completions.resources import resolve_resource_completion_item
from .config.user_configuration import DiagnosticPublishingMethod
from .config.user_configuration import UserConfiguration
from .config.user_configuration import configuration_params
from .config.user_configuration import from_did_change_config
from .config.user_configuration import from_get_configuration_response
from .decode import CfnDecodingException
from .decode import decode
from .decode import decode_unfinished
from .decode.extractors import AllowedValuesExtractor
from .decode.extractors import CompositeExtractor
from .decode.extractors import ResourceExtractor
from .decode.extractors import ResourcePropertyExtractor
from .definitions import definition
from .hovers import hover


logger = logging.getLogger(__name__)


def server(cfn_aws_context: AWSContext, sam_aws_context: AWSContext) -> LanguageServer:
    server = LanguageServer("cfn-lsp-extra", "")  # TODO get real version here
    extractor = CompositeExtractor[Union[AWSResourceName, AWSPropertyName]](
        ResourcePropertyExtractor(), ResourceExtractor()
    )
    allowed_values_extractor = AllowedValuesExtractor(
        set(cfn_aws_context.properties_with_allowed_values())
    )
    logger.info(
        "Found a total of %d properties with enum values",
        len(allowed_values_extractor.property_set),
    )
    config = UserConfiguration()

    @server.thread()
    @server.feature(INITIALIZED)
    def intialiazed(ls: LanguageServer, params: InitializedParams) -> None:
        """Client initialized notification."""
        workspace_capabilities = ls.client_capabilities.workspace
        if workspace_capabilities and workspace_capabilities.configuration:
            logger.info("Obtaining user config")
            try:
                config_response = ls.get_configuration(
                    params=configuration_params()
                ).result(timeout=1)
            except TimeoutError:
                logger.error("Timeout retrieving config")
            else:
                nonlocal config
                config = from_get_configuration_response(config_response)
                logger.info("Obtained user config: %s", config)

    @server.thread()
    @server.feature(TEXT_DOCUMENT_DID_OPEN)
    def did_open(ls: LanguageServer, params: DidOpenTextDocumentParams) -> None:
        """Text document did open notification."""
        uri = params.text_document.uri
        ls.show_message("Text Document Did Open")
        text_doc = ls.workspace.get_document(uri)
        logger.debug("Is template SAM: %s", is_document_sam(text_doc))
        file_path = text_doc.path
        ls.publish_diagnostics(text_doc.uri, diagnostics(text_doc.source, file_path))

    @server.thread()
    @server.feature(TEXT_DOCUMENT_DID_CHANGE)
    def did_change(ls: LanguageServer, params: DidChangeTextDocumentParams) -> None:
        """Text document did change notification."""
        uri = params.text_document.uri
        text_doc = ls.workspace.get_document(uri)
        file_path = text_doc.path
        if (
            config.diagnostic_publishing_method
            == DiagnosticPublishingMethod.ON_DID_CHANGE
        ):
            # Publishing diagnostics removes old ones
            ls.publish_diagnostics(
                text_doc.uri, diagnostics(text_doc.source, file_path)
            )

    @server.thread()
    @server.feature(TEXT_DOCUMENT_DID_SAVE)
    def did_save(ls: LanguageServer, params: DidSaveTextDocumentParams) -> None:
        """Text document did save notification."""
        uri = params.text_document.uri
        text_doc = ls.workspace.get_document(uri)
        file_path = text_doc.path
        if (
            config.diagnostic_publishing_method
            == DiagnosticPublishingMethod.ON_DID_SAVE
        ):
            ls.publish_diagnostics(
                text_doc.uri, diagnostics(text_doc.source, file_path)
            )

    @server.feature(
        TEXT_DOCUMENT_COMPLETION,
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
        return completions_for(
            template_data,
            aws_context,
            document,
            params.position,
            allowed_values_extractor,
        )

    @server.feature(COMPLETION_ITEM_RESOLVE)
    def completion_item_resolve(
        ls: LanguageServer, completion_item: CompletionItem
    ) -> CompletionItem:
        """Resolves a completion item."""
        if re.match(r"^.+::.+::.+$", completion_item.label):
            return resolve_resource_completion_item(completion_item, sam_aws_context)
        else:
            return completion_item  # Not a resource

    @server.feature(TEXT_DOCUMENT_HOVER)
    def did_hover(ls: LanguageServer, params: HoverParams) -> Optional[Hover]:
        """Text document did hover notification."""
        uri = params.text_document.uri
        document = server.workspace.get_document(uri)
        aws_context = sam_aws_context if is_document_sam(document) else cfn_aws_context
        try:
            template_data = decode(document.source, document.filename)
        except CfnDecodingException as e:
            logger.debug("Failed to decode document: %s", e)
            return None
        position_lookup = extractor.extract(template_data)
        return hover(
            template_data, params.position, aws_context, document, position_lookup
        )

    @server.feature(TEXT_DOCUMENT_DEFINITION)
    def goto_definition(
        ls: LanguageServer, params: DefinitionParams
    ) -> Optional[Location]:
        document = server.workspace.get_document(params.text_document.uri)
        aws_context = sam_aws_context if is_document_sam(document) else cfn_aws_context
        try:
            template_data = decode(document.source, document.filename)
        except CfnDecodingException as e:
            logger.debug("Failed to decode document: %s", e)
            return None
        return definition(template_data, document, params.position, aws_context)

    @server.feature(WORKSPACE_DID_CHANGE_CONFIGURATION)
    def did_change_configuration(
        ls: LanguageServer, params: DidChangeConfigurationParams
    ) -> None:
        """Workspace did change configuration notification."""
        logger.info("Received user configuration: %s", params)
        nonlocal config
        config = from_did_change_config(params)

    return server


def is_document_sam(document: Document) -> bool:
    for line in document.lines:
        if not line.lstrip().startswith("#"):
            return line.rstrip() == "Transform: AWS::Serverless-2016-10-31"
    return False
