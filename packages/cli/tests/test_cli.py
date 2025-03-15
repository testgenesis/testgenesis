"""Tests for the main CLI interface."""

from click.testing import CliRunner

from testgenesis_cli.cli import cli


def test_cli_help():
    """Test that the CLI shows help with all available commands."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    # Check main description
    assert "TestGenesis CLI" in result.output
    assert "Extract user flows from analytics platforms" in result.output

    # Check available commands
    assert "Commands:" in result.output
    assert "amplitude" in result.output
    assert "generate" in result.output


def test_amplitude_command_help():
    """Test that the amplitude command group shows proper help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["amplitude", "--help"])

    assert result.exit_code == 0
    assert "Commands for working with Amplitude analytics" in result.output
    assert "extract-flows" in result.output


def test_generate_command_help():
    """Test that the generate command shows proper help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["generate", "--help"])

    assert result.exit_code == 0
    assert "Generate test code from a test flow file" in result.output
    assert "--framework" in result.output
    assert "--output" in result.output 