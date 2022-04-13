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

import cfnlint.config
import cfnlint.core
import cfnlint.decode
import cfnlint.runner
import click
import yaml
from pygls.lsp.methods import COMPLETION
from pygls.lsp.methods import HOVER
from pygls.lsp.methods import TEXT_DOCUMENT_DID_OPEN
from pygls.lsp.types import DidOpenTextDocumentParams
from pygls.lsp.types import Hover
from pygls.lsp.types import HoverParams
from pygls.lsp.types import MarkupContent
from pygls.lsp.types import MarkupKind
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.lsp.types.basic_structures import Diagnostic
from pygls.lsp.types.language_features.completion import CompletionItem
from pygls.lsp.types.language_features.completion import CompletionList
from pygls.lsp.types.language_features.completion import CompletionOptions
from pygls.lsp.types.language_features.completion import CompletionParams
from pygls.server import LanguageServer

from .aws_data import AWSContext
from .aws_data import AWSResource
from .context import cache
from .context import download_context
from .parsing import SafePositionLoader
from .parsing import flatten_mapping
from .scrape.markdown import parse_urls


def server(aws_context: AWSContext) -> LanguageServer:
    server = LanguageServer()

    # @server.thread()
    @server.feature(TEXT_DOCUMENT_DID_OPEN)
    def did_open(ls: LanguageServer, params: DidOpenTextDocumentParams) -> None:
        """Text document did open notification."""
        logger = logging.getLogger(__name__)
        ls.show_message("Text Document Did Open")
        text_doc = ls.workspace.get_document(params.text_document.uri)
        filename = text_doc.path
        conf, _, _ = cfnlint.core.get_args_filenames([])
        template, rules, errors = cfnlint.core.get_template_rules(filename, conf)
        ls.show_message(f"file: {filename}")
        ls.show_message(f"errors: {errors}")

        if not errors:
            runner = cfnlint.runner.Runner(
                rules, filename, template, regions=None, mandatory_rules=None
            )
            errors = runner.transform()
        diagnostics = [
            Diagnostic(
                range=Range(
                    start=Position(line=m.linenumber - 1, character=m.columnnumber - 1),
                    end=Position(
                        line=m.linenumberend - 1, character=m.columnnumberend - 1
                    ),
                ),
                message=m.message,
                source="cfn-lsp-extra",
            )
            for m in errors
        ]

        if diagnostics:
            ls.publish_diagnostics(text_doc.uri, diagnostics)
        ls.show_message(f"LINTING ERRORS: {diagnostics}")

    @server.feature(COMPLETION)
    def completions(
        ls: LanguageServer, params: CompletionParams
    ) -> Optional[CompletionList]:
        """Returns completion items."""
        line_at = params.position.line
        uri = params.text_document.uri
        document = server.workspace.get_document(uri)
        try:
            data = yaml.load(document.source, Loader=SafePositionLoader)
        except yaml.scanner.ScannerError:
            # Try adding a ':' and see if that makes the yaml valid
            new_source_lst = document.source.splitlines()
            new_source_lst[line_at] = new_source_lst[line_at].rstrip() + ":"
            new_source = "\n".join(new_source_lst)
            data = yaml.load(new_source, Loader=SafePositionLoader)

        props = flatten_mapping(data)
        for aws_prop, positions in props.items():
            if aws_prop.resource in aws_context.resources:
                for line, _ in positions:
                    if line == line_at:
                        return CompletionList(
                            is_incomplete=aws_prop.property_
                            in aws_context.resources[
                                aws_prop.resource
                            ].property_descriptions,
                            items=[
                                CompletionItem(label=s)
                                for s in aws_context.resources[
                                    aws_prop.resource
                                ].property_descriptions.keys()
                            ],
                        )

    @server.feature(HOVER)
    def did_hover(ls: LanguageServer, params: HoverParams) -> Optional[Hover]:
        """Text document did hover notification."""
        line_at, char_at = params.position.line, params.position.character
        uri = params.text_document.uri
        document = server.workspace.get_document(uri)
        # Parse document
        try:
            data = yaml.load(document.source, Loader=SafePositionLoader)
        except yaml.scanner.ScannerError:  # Invalid yaml
            return None
        props = flatten_mapping(data)
        for aws_prop, positions in props.items():
            if not (
                aws_prop.resource in aws_context.resources
                and aws_prop.property_
                in aws_context.resources[aws_prop.resource].property_descriptions
            ):
                continue
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
                            kind=MarkupKind.Markdown,
                            value=aws_context[aws_prop],
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
