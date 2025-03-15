"""Cypress test code generator."""

from pathlib import Path
from typing import Any, Dict

import json

from ..models.test_flow import TestFlow


def generate_cypress_test(flow_path: str, output_path: str) -> None:
    """Generate a Cypress test from a test flow."""
    # Load test flow
    flow_data = json.loads(Path(flow_path).read_text())
    flow = TestFlow(name=flow_data["name"], actions=flow_data["actions"])

    # Generate test code
    code = f"""
describe('{flow.name}', () => {{
  it('completes successfully', () => {{
"""

    # Add actions
    for action in flow.actions:
        if action.type == "navigation":
            code += f"    cy.visit('{action.target}');\n"
            if action.assertions:
                code += f"    cy.url().should('include', '{action.target}');\n"

        elif action.type == "click":
            code += f"    cy.get('{action.target}').click();\n"
            if action.assertions:
                code += f"    cy.get('{action.target}').should('be.visible');\n"

        elif action.type == "form":
            if action.data:
                for selector, value in action.data.items():
                    code += f"    cy.get('{selector}').type('{value}');\n"
            code += f"    cy.get('{action.target}').click();\n"
            if action.assertions:
                code += "    // Add form validation assertions here\n"

    code += "  });\n});\n"

    # Save test file
    Path(output_path).write_text(code)
