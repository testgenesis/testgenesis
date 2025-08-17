"""Test generation command."""


import click
from rich.console import Console

from testgenesis_dsl import generate_test_code

console = Console()


@click.command()
@click.argument("flow_path", type=click.Path(exists=True))
@click.option(
    "--framework",
    type=click.Choice(["playwright", "cypress"]),
    required=True,
    help="Test framework to generate code for",
)
@click.option(
    "--output",
    type=click.Path(),
    required=True,
    help="Output file path for the generated test",
)
def generate(flow_path: str, framework: str, output: str) -> None:
    """Generate test code from a test flow file."""
    try:
        generate_test_code(flow_path, framework, output)
        console.print(f"[green]Generated {framework} test at: {output}[/green]")
    except Exception as e:
        console.print(f"[red]Error generating test: {e!s}[/red]")
        raise click.Abort()
