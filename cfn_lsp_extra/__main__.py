"""Command-line interface."""

import logging

import click
from click import Context

from .context import download_context, load_cfn_context, load_sam_context
from .server import server

logger = logging.getLogger(__name__)


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
        cfn_aws_context = load_cfn_context()
        sam_aws_context = load_sam_context(cfn_aws_context)
        logger.info("Starting cfn-lsp-extra server")
        server(cfn_aws_context, sam_aws_context).start_io()


@cli.command()
def generate_cache() -> None:
    """Generate the documentation cache and exit."""
    download_context()


def main() -> None:
    cli(prog_name="cfn-lsp-extra", auto_envvar_prefix="CFN_LSP_EXTRA")


if __name__ == "__main__":
    main()
