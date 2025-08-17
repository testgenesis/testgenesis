"""Tests for test generation command."""

import json
from collections.abc import Generator
from pathlib import Path

import pytest
from click.testing import CliRunner

from testgenesis_cli.commands.generate import generate


@pytest.fixture
def sample_flow_file(tmp_path):
    """Create a sample test flow file."""
    flow_data = {
        "name": "login_flow",
        "frequency": 10,
        "actions": [
            {"type": "navigation", "target": "/login", "assertions": ["url", "title"]},
            {
                "type": "form",
                "target": "#login-form",
                "data": {"username": "testuser", "password": "password123"},
                "assertions": ["form_valid", "submit_success"],
            },
        ],
    }

    flow_file = tmp_path / "login_flow.json"
    flow_file.write_text(json.dumps(flow_data))
    return flow_file


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def test_flow(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a test flow file for testing."""
    flow_path = tmp_path / "test_flow.json"
    flow_path.write_text("""
    {
        "name": "test_login",
        "actions": [
            {
                "type": "navigation",
                "target": "/login",
                "assertions": ["url"]
            },
            {
                "type": "form",
                "target": "#login-form",
                "data": {
                    "#email": "test@example.com",
                    "#password": "password123"
                },
                "assertions": ["form_valid"]
            }
        ]
    }
    """)
    yield flow_path


def test_generate_playwright(runner: CliRunner, test_flow: Path, tmp_path: Path) -> None:
    """Test generating a Playwright test."""
    output_path = tmp_path / "test.spec.ts"
    result = runner.invoke(
        generate, [str(test_flow), "--framework", "playwright", "--output", str(output_path)]
    )

    assert result.exit_code == 0
    assert output_path.exists()
    assert "test_login" in output_path.read_text()
    assert "@playwright/test" in output_path.read_text()


def test_generate_cypress(runner: CliRunner, test_flow: Path, tmp_path: Path) -> None:
    """Test generating a Cypress test."""
    output_path = tmp_path / "test.cy.ts"
    result = runner.invoke(
        generate, [str(test_flow), "--framework", "cypress", "--output", str(output_path)]
    )

    assert result.exit_code == 0
    assert output_path.exists()
    assert "test_login" in output_path.read_text()
    assert "describe(" in output_path.read_text()


def test_generate_invalid_framework(runner: CliRunner, test_flow: Path, tmp_path: Path) -> None:
    """Test generating with an invalid framework."""
    output_path = tmp_path / "test.ts"
    result = runner.invoke(
        generate, [str(test_flow), "--framework", "invalid", "--output", str(output_path)]
    )

    assert result.exit_code != 0
    assert not output_path.exists()


def test_generate_missing_flow(runner: CliRunner, tmp_path: Path) -> None:
    """Test generating with a missing flow file."""
    output_path = tmp_path / "test.ts"
    result = runner.invoke(
        generate,
        [
            str(tmp_path / "nonexistent.json"),
            "--framework",
            "playwright",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code != 0
    assert not output_path.exists()


def test_generate_playwright_test(sample_flow_file, tmp_path):
    """Test generating a Playwright test from a flow file."""
    runner = CliRunner()
    output_file = tmp_path / "login_flow.spec.ts"

    result = runner.invoke(
        generate, [str(sample_flow_file), "--framework", "playwright", "--output", str(output_file)]
    )

    if result.exit_code != 0:
        print(f"\nCommand failed with output:\n{result.output}")

    assert result.exit_code == 0
    assert output_file.exists()

    generated_code = output_file.read_text()
    assert "import { test, expect } from '@playwright/test';" in generated_code
    assert "test('login_flow'" in generated_code
    assert "await page.goto('/login')" in generated_code
    assert "await page.fill('#login-form [name=\"username\"]', 'testuser')" in generated_code


def test_generate_cypress_test(sample_flow_file, tmp_path):
    """Test generating a Cypress test from a flow file."""
    runner = CliRunner()
    output_file = tmp_path / "login_flow.cy.ts"

    result = runner.invoke(
        generate, [str(sample_flow_file), "--framework", "cypress", "--output", str(output_file)]
    )

    assert result.exit_code == 0
    assert output_file.exists()

    generated_code = output_file.read_text()
    assert "describe('login_flow'" in generated_code
    assert "cy.visit('/login')" in generated_code
    assert "cy.get('#login-form [name=\"username\"]').type('testuser')" in generated_code


def test_invalid_flow_file():
    """Test handling of invalid flow file."""
    runner = CliRunner()
    result = runner.invoke(generate, ["nonexistent.json"])
    assert result.exit_code != 0
    assert "Error" in result.output
