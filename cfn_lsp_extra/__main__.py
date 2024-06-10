"""Command-line interface."""

import logging
from pathlib import Path

import click
from click import Context

from .context import load_cfn_context, load_sam_context
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
@click.argument("specification-file", type=click.Path(exists=True))
def update_specification(specification_file: str) -> None:
    """Update the specification used by cfn-lsp-extra."""
    try:
        from .scrape.specification import run
    except ImportError as e:
        raise Exception(
            "Please Install cfn-lsp-extra[parse] to run 'update-specification'"
        ) from e
    else:
        run(Path(specification_file))


@cli.command()
@click.argument("specification-file", type=click.Path(exists=True))
def update_sam_specification(specification_file: str) -> None:
    try:
        from .scrape.sam_specification import run
    except ImportError as e:
        raise Exception(
            "Please Install cfn-lsp-extra[parse] to run 'update-specification'"
        ) from e
    else:
        run(Path(specification_file))


def main() -> None:
    cli(prog_name="cfn-lsp-extra", auto_envvar_prefix="CFN_LSP_EXTRA")


if __name__ == "__main__":
    main()
