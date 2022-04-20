"""Command-line interface."""

import logging

import click
from click import Context

from .context import cache
from .context import download_context
from .server import server


@click.group(invoke_without_command=True)
@click.version_option()
@click.option("-v", "--verbose", is_flag=True, help="Print more output.")
@click.option("--no-cache", is_flag=True, help="Don't use cached documentation.")
@click.pass_context
def main(ctx: Context, verbose: bool, no_cache: bool) -> None:
    """Start a cfn-lsp-extra server."""
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
    # This fn is called regardless, so we have to check if a subcommand should be run
    if ctx.invoked_subcommand is None:
        no_cache = True
        aws_context = download_context() if no_cache else cache()
        server(aws_context).start_io()  # type: ignore[no-untyped-call]
    return None


@main.command()
def generate_cache() -> None:
    """Generate the documentation cache and exit."""
    cache(void_cache=True)
    return None


# TODO this is not used by install.poetry.scripts
if __name__ == "__main__":
    main(prog_name="cfn-lsp-extra", auto_envvar_prefix="CFN_LSP_EXTRA")
