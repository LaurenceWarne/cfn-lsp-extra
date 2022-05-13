"""Command-line interface."""

import logging

import click
from click import Context

from .context import download_context
from .context import load_context
from .server import server


@click.group(invoke_without_command=True)
@click.version_option()
@click.option("-v", "--verbose", count=True, help="Print more output.")
@click.pass_context
def cli(ctx: Context, verbose: int) -> None:
    """Start a cfn-lsp-extra server."""
    level = [logging.ERROR, logging.INFO, logging.DEBUG][min(verbose, 2)]
    logging.basicConfig(level=level)
    # This fn is called regardless, so we have to check if a subcommand should be run
    if ctx.invoked_subcommand is None:
        aws_context = load_context()
        server(aws_context).start_io()  # type: ignore[no-untyped-call]
    return None


@cli.command()
def generate_cache() -> None:
    """Generate the documentation cache and exit."""
    download_context()
    return None


def main() -> None:
    cli(prog_name="cfn-lsp-extra", auto_envvar_prefix="CFN_LSP_EXTRA")


if __name__ == "__main__":
    main()
