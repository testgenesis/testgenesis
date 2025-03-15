"""Playwright test code generator."""

from ..models.test_flow import UserAction, TestFlow


def generate_action(action: UserAction) -> str:
    """Generate Playwright code for a user action."""
    code = []

    if action.wait_for:
        code.append(
            f"await page.waitForSelector('{action.wait_for}', {{ timeout: {action.timeout} }})"
        )

    if action.type == "navigation":
        code.append(f"await page.goto('{action.target}')")
        if "url" in action.assertions:
            code.append(f"expect(page.url()).toContain('{action.target}')")
        if "title" in action.assertions:
            code.append("await expect(page).toHaveTitle(/.*/)")

    elif action.type == "click":
        code.append(f"await page.click('{action.target}')")

    elif action.type == "form":
        for field, value in action.data.items():
            code.append(f"await page.fill('{action.target} [name=\"{field}\"]', '{value}')")
        code.append(f"await page.click('{action.target} [type=\"submit\"]')")

    return "\n".join(code)


def generate_test(flow: TestFlow) -> str:
    """Generate a complete Playwright test file."""
    code = [
        "import { test, expect } from '@playwright/test';",
        "",
        f"test('{flow.name}', async ({page}) => {{",
    ]

    for action in flow.actions:
        code.extend(f"  {line}" for line in generate_action(action).split("\n"))

    code.append("});")
    return "\n".join(code)
