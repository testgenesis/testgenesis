"""TestGenesis CLI."""

import click

from .analytics.amplitude import amplitude
from .commands.generate import generate


@click.group()
def cli():
    """TestGenesis CLI - Generate E2E tests from user analytics data.

    Extract user flows from analytics platforms and generate end-to-end tests.
    """
    pass


# Add commands
cli.add_command(generate)
cli.add_command(amplitude)

if __name__ == "__main__":
    cli()
