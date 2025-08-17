"""Playwright test code generator."""

import json
from pathlib import Path

from ..models.test_flow import Action, TestFlow


def generate_playwright_test(flow_path: str, output_path: str) -> None:
    """Generate a Playwright test from a test flow."""
    # Load test flow
    flow_data = json.loads(Path(flow_path).read_text())
    actions = [
        Action(
            type=action["type"],
            target=action["target"],
            data=action.get("data"),
            assertions=action.get("assertions", []),
        )
        for action in flow_data["actions"]
    ]
    flow = TestFlow(name=flow_data["name"], actions=actions)

    # Generate test code
    code = f"""
import {{ test, expect }} from '@playwright/test';

test('{flow.name}', async ({{ page }}) => {{
"""

    # Add actions
    for action in flow.actions:
        if action.type == "navigation":
            code += f"    await page.goto('{action.target}');\n"
            if action.assertions and "url" in action.assertions:
                code += f"    await expect(page).toHaveURL('{action.target}');\n"

        elif action.type == "click":
            code += f"    await page.click('{action.target}');\n"
            if action.assertions and "visible" in action.assertions:
                code += f"    await expect(page.locator('{action.target}')).toBeVisible();\n"

        elif action.type == "form":
            if action.data:
                for field, value in action.data.items():
                    selector = f'{action.target} [name="{field}"]'
                    code += f"    await page.fill('{selector}', '{value}');\n"
            code += f"    await page.click('{action.target}');\n"
            if action.assertions:
                if "form_valid" in action.assertions:
                    code += "    // Add form validation assertions\n"
                if "submit_success" in action.assertions:
                    code += "    // Add submission success assertions\n"

    code += "});\n"

    # Save test file
    Path(output_path).write_text(code)
