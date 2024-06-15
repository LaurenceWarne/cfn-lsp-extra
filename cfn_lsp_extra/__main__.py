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
    level = [logging.ERROR, logging.INFO, logging.DEBUG][min(verbose, 2)]
    logging.basicConfig(level=level, force=True)
    if ctx.invoked_subcommand is None:
        cfn_aws_context = load_cfn_context()
        sam_aws_context = load_sam_context(cfn_aws_context)
        logger.info("Starting cfn-lsp-extra server")
        server(cfn_aws_context, sam_aws_context).start_io()


@cli.command()
@click.option("-s", "--specification-file", type=click.Path(exists=True))
@click.option("-d", "--documentation-directory", type=click.Path(exists=True))
@click.option("-o", "--output-path", type=click.Path(exists=False))
def update_specification(
    specification_file: Optional[str] = None,
    documentation_directory: Optional[str] = None,
    output_path: Optional[str] = None,
) -> None:
    """Update the specification used by cfn-lsp-extra."""
    logging.basicConfig(level=logging.INFO, force=True)
    try:
        from .scrape.specification import run
    except ImportError as e:
        raise Exception(
            "Please Install cfn-lsp-extra[parse] to run 'update-specification'"
        ) from e
    else:
        run(
            Path(specification_file) if specification_file else None,
            Path(documentation_directory).absolute()
            if documentation_directory
            else None,
            Path(output_path) if output_path else None,
        )


@cli.command()
@click.option("-s", "--specification-file", type=click.Path(exists=True))
@click.option("-d", "--documentation-directory", type=click.Path(exists=True))
@click.option("-o", "--output-path", type=click.Path(exists=False))
def update_sam_specification(
    specification_file: Optional[str] = None,
    documentation_directory: Optional[str] = None,
    output_path: Optional[str] = None,
) -> None:
    logging.basicConfig(level=logging.INFO, force=True)
    try:
        from .scrape.sam_specification import run
    except ImportError as e:
        raise Exception(
            "Please Install cfn-lsp-extra[parse] to run 'update-specification'"
        ) from e
    else:
        run(
            Path(specification_file) if specification_file else None,
            Path(documentation_directory).absolute()
            if documentation_directory
            else None,
            Path(output_path) if output_path else None,
        )


def main() -> None:
    cli(prog_name="cfn-lsp-extra", auto_envvar_prefix="CFN_LSP_EXTRA")


if __name__ == "__main__":
    main()
