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
from pygls.lsp.types.language_features.completion import CompletionOptions
from pygls.lsp.types.language_features.completion import CompletionParams
from pygls.server import LanguageServer

from cfn_lsp_extra.parsing.extractors import ResourcePropertyExtractor

from .aws_data import AWSContext
from .aws_data import AWSResource
from .cfnlint_integration import diagnostics  # type: ignore[attr-defined]
from .context import cache
from .context import download_context
from .parsing.yaml_parsing import SafePositionLoader
from .scrape.markdown import parse_urls


def server(aws_context: AWSContext) -> LanguageServer:
    server = LanguageServer()

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
            data = yaml.load(document.source, Loader=SafePositionLoader)
        except (yaml.scanner.ScannerError, yaml.parser.ParserError):
            # Try adding a ':' and see if that makes the yaml valid
            new_source_lst = document.source.splitlines()
            new_source_lst[line_at] = new_source_lst[line_at].rstrip() + ":"
            new_source = "\n".join(new_source_lst)
            data = yaml.load(new_source, Loader=SafePositionLoader)

        extractor = ResourcePropertyExtractor()
        position_lookup = extractor.extract(data)
        aws_prop_span = position_lookup.at(line_at, char_at)
        if aws_prop_span and aws_prop_span.value.resource in aws_context.resources:
            return CompletionList(
                is_incomplete=aws_prop_span.value.property_
                in aws_context.resources[
                    aws_prop_span.value.resource
                ].property_descriptions,
                items=[
                    CompletionItem(label=s)
                    for s in aws_context.resources[
                        aws_prop_span.value.resource
                    ].property_descriptions.keys()
                ],
            )
        return None

    @server.feature(HOVER)
    def did_hover(ls: LanguageServer, params: HoverParams) -> Optional[Hover]:
        """Text document did hover notification."""
        line_at, char_at = params.position.line, params.position.character
        uri = params.text_document.uri
        document = server.workspace.get_document(uri)
        # Parse document
        try:
            data = yaml.load(document.source, Loader=SafePositionLoader)
        except (yaml.scanner.ScannerError, yaml.parser.ParserError):
            return None
        extractor = ResourcePropertyExtractor()
        position_lookup = extractor.extract(data)
        aws_prop_span = position_lookup.at(line_at, char_at)
        if (
            aws_prop_span
            and aws_prop_span.value.resource in aws_context.resources
            and aws_prop_span.value.property_
            in aws_context.resources[aws_prop_span.value.resource].property_descriptions
        ):
            return Hover(
                range=Range(
                    start=Position(line=line_at, character=aws_prop_span.char),
                    end=Position(
                        line=line_at, character=aws_prop_span.char + aws_prop_span.span
                    ),
                ),
                contents=MarkupContent(
                    kind=MarkupKind.Markdown,
                    value=aws_context[aws_prop_span.value],
                ),
            )
        return None

    return server


@click.command()
@click.version_option()
@click.option("-v", "--verbose", is_flag=True, help="Print more output.")
@click.option("--no-cache", is_flag=True, help="Don't use cached documentation.")
@click.option(
    "--generate-cache",
    is_flag=True,
    help="Generate the documentation cache and exit.",
)
def main(verbose: bool, no_cache: bool, generate_cache: bool) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
    if generate_cache:
        cache(void_cache=True)
        return None
    no_cache = True
    aws_context = download_context() if no_cache else cache()
    server(aws_context).start_io()  # type: ignore[no-untyped-call]
    return None


if __name__ == "__main__":
    main(auto_envvar_prefix="CFN_LSP_EXTRA")
