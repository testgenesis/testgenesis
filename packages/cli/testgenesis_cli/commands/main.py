"""TestGenesis CLI main entry point."""


import click

from testgenesis_cli.analytics.amplitude import amplitude
from testgenesis_cli.commands.generate import generate


@click.group()
def cli() -> None:
    """TestGenesis CLI - Generate E2E tests from analytics data."""
    pass


cli.add_command(amplitude)
cli.add_command(generate)


if __name__ == "__main__":
    cli()
