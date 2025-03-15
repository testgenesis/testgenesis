"""TestGenesis CLI main entry point."""

import click

from ..analytics.amplitude import amplitude
from .generate import generate


@click.group()
def cli():
    """TestGenesis CLI tools."""
    pass


cli.add_command(amplitude)
cli.add_command(generate)


if __name__ == "__main__":
    cli()
