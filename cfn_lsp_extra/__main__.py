"""Command-line interface."""

import logging
from pathlib import Path
from typing import Optional

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
    # This fn is called regardless, so we have to check if a subcommand should be run
    if ctx.invoked_subcommand is None:
        cfn_aws_context = load_cfn_context()
        sam_aws_context = load_sam_context(cfn_aws_context)
        logger.info("Starting cfn-lsp-extra server")
        server(cfn_aws_context, sam_aws_context).start_io()


@cli.command()
@click.argument("specification-file", type=click.Path(exists=True))
@click.argument("documentation-directory", type=click.Path(exists=True), required=False)
def update_specification(
    specification_file: str, documentation_directory: Optional[str] = None
) -> None:
    """Update the specification used by cfn-lsp-extra."""
    try:
        from .scrape.specification import run
    except ImportError as e:
        raise Exception(
            "Please Install cfn-lsp-extra[parse] to run 'update-specification'"
        ) from e
    else:
        logging.basicConfig(level=logging.INFO)
        run(
            Path(specification_file),
            Path(documentation_directory).absolute()
            if documentation_directory
            else None,
        )


@cli.command()
@click.argument("specification-file", type=click.Path(exists=True))
@click.argument("documentation-directory", type=click.Path(exists=True), required=False)
def update_sam_specification(
    specification_file: str, documentation_directory: Optional[str] = None
) -> None:
    try:
        from .scrape.sam_specification import run
    except ImportError as e:
        raise Exception(
            "Please Install cfn-lsp-extra[parse] to run 'update-specification'"
        ) from e
    else:
        logging.basicConfig(level=logging.INFO)
        run(
            Path(specification_file),
            Path(documentation_directory).absolute()
            if documentation_directory
            else None,
        )


def main() -> None:
    cli(prog_name="cfn-lsp-extra", auto_envvar_prefix="CFN_LSP_EXTRA")


if __name__ == "__main__":
    main()
