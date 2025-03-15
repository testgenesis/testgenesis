"""Playwright test code generator."""

from pathlib import Path
from typing import Any, Dict

import json

from ..models.test_flow import TestFlow


def generate_playwright_test(flow_path: str, output_path: str) -> None:
    """Generate a Playwright test from a test flow."""
    # Load test flow
    flow_data = json.loads(Path(flow_path).read_text())
    flow = TestFlow(name=flow_data["name"], actions=flow_data["actions"])

    # Generate test code
    code = f"""
import {{ test, expect }} from '@playwright/test';

test('{flow.name}', async ({{ page }}) => {{
"""

    # Add actions
    for action in flow.actions:
        if action.type == "navigation":
            code += f"    await page.goto('{action.target}');\n"
            if action.assertions:
                code += f"    await expect(page).toHaveURL('{action.target}');\n"

        elif action.type == "click":
            code += f"    await page.click('{action.target}');\n"
            if action.assertions:
                code += f"    await expect(page.locator('{action.target}')).toBeVisible();\n"

        elif action.type == "form":
            if action.data:
                for selector, value in action.data.items():
                    code += f"    await page.fill('{selector}', '{value}');\n"
            code += f"    await page.click('{action.target}');\n"
            if action.assertions:
                code += "    // Add form validation assertions here\n"

    code += "});\n"

    # Save test file
    Path(output_path).write_text(code)
