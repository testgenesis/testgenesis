"""Tests for test generation command."""

import json
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


def test_generate_playwright_test(sample_flow_file, tmp_path):
    """Test generating a Playwright test from a flow file."""
    runner = CliRunner()
    output_file = tmp_path / "login_flow.spec.ts"

    result = runner.invoke(
        generate, [str(sample_flow_file), "--framework", "playwright", "--output", str(output_file)]
    )

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
