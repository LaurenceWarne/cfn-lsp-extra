"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """Cnf Lsp Extra."""


if __name__ == "__main__":
    main(prog_name="cnf-lsp-extra")  # pragma: no cover
