"""Command-line interface."""

import logging

import click
from click import Context

from .context import download_context
from .context import load_context
from .server import server


@click.group(invoke_without_command=True)
@click.version_option()
@click.option("-v", "--verbose", is_flag=True, help="Print more output.")
@click.pass_context
def main(ctx: Context, verbose: bool) -> None:
    """Start a cfn-lsp-extra server."""
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
    # This fn is called regardless, so we have to check if a subcommand should be run
    if ctx.invoked_subcommand is None:
        aws_context = load_context()
        server(aws_context).start_io()  # type: ignore[no-untyped-call]
    return None


@main.command()
def generate_cache() -> None:
    """Generate the documentation cache and exit."""
    download_context()
    return None


# TODO this is not used by install.poetry.scripts
if __name__ == "__main__":
    main(prog_name="cfn-lsp-extra", auto_envvar_prefix="CFN_LSP_EXTRA")
