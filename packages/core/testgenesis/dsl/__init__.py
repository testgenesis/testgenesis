"""TestGenesis DSL for defining test flows."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class UserAction:
    """Represents a single user action in a test flow."""

    type: str  # navigation, click, form, etc.
    target: str  # URL, selector, etc.
    assertions: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    wait_for: Optional[str] = None
    timeout: int = 5000

    def to_playwright(self) -> str:
        """Convert action to Playwright test code."""
        code = []

        if self.wait_for:
            code.append(
                f"await page.waitForSelector('{self.wait_for}', {{ timeout: {self.timeout} }})"
            )

        if self.type == "navigation":
            code.append(f"await page.goto('{self.target}')")
            if "url" in self.assertions:
                code.append(f"expect(page.url()).toContain('{self.target}')")
            if "title" in self.assertions:
                code.append("await expect(page).toHaveTitle(/.*/)")

        elif self.type == "click":
            code.append(f"await page.click('{self.target}')")

        elif self.type == "form":
            for field, value in self.data.items():
                code.append(f"await page.fill('{self.target} [name=\"{field}\"]', '{value}')")
            code.append(f"await page.click('{self.target} [type=\"submit\"]')")

        return "\n".join(code)

    def to_cypress(self) -> str:
        """Convert action to Cypress test code."""
        code = []

        if self.wait_for:
            code.append(f"cy.get('{self.wait_for}', {{ timeout: {self.timeout} }})")

        if self.type == "navigation":
            code.append(f"cy.visit('{self.target}')")
            if "url" in self.assertions:
                code.append(f"cy.url().should('include', '{self.target}')")
            if "title" in self.assertions:
                code.append("cy.title().should('match', /.*/)")

        elif self.type == "click":
            code.append(f"cy.get('{self.target}').click()")

        elif self.type == "form":
            for field, value in self.data.items():
                code.append(f"cy.get('{self.target} [name=\"{field}\"]').type('{value}')")
            code.append(f"cy.get('{self.target} [type=\"submit\"]').click()")

        return "\n".join(code)


@dataclass
class TestFlow:
    """Represents a sequence of user actions that form a test."""

    name: str
    actions: List[UserAction]
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def get_pattern(self) -> str:
        """Get a string representation of the action pattern for comparison."""
        return "|".join(f"{a.type}:{a.target}" for a in self.actions)

    def to_playwright(self) -> str:
        """Convert flow to Playwright test code."""
        code = [
            "import { test, expect } from '@playwright/test';",
            "",
            f"test('{self.name}', async ({page}) => {{",
        ]

        for action in self.actions:
            code.extend(f"  {line}" for line in action.to_playwright().split("\n"))

        code.append("});")
        return "\n".join(code)

    def to_cypress(self) -> str:
        """Convert flow to Cypress test code."""
        code = [
            f"describe('{self.name}', () => {{",
            "  it('completes successfully', () => {",
        ]

        for action in self.actions:
            code.extend(f"    {line}" for line in action.to_cypress().split("\n"))

        code.extend(["  })", "})"])
        return "\n".join(code)


@dataclass
class UserJourney:
    """Represents a collection of related test flows."""

    name: str
    flows: List[TestFlow]
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
