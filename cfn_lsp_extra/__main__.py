"""Command-line interface."""
import click

from .server import main


if __name__ == "__main__":
    main(prog_name="cfn-lsp-extra")  # pragma: no cover
