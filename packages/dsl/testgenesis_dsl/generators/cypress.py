"""Cypress test code generator."""

from pathlib import Path
from typing import Any, Dict

import json

from ..models.test_flow import TestFlow, Action


def generate_cypress_test(flow_path: str, output_path: str) -> None:
    """Generate a Cypress test from a test flow."""
    # Load test flow
    flow_data = json.loads(Path(flow_path).read_text())
    actions = [Action(**action) for action in flow_data["actions"]]
    flow = TestFlow(name=flow_data["name"], actions=actions)

    # Generate test code
    code = f"""
describe('{flow.name}', () => {{
  it('completes successfully', () => {{
"""

    # Add actions
    for action in flow.actions:
        if action.type == "navigation":
            code += f"    cy.visit('{action.target}');\n"
            if action.assertions and "url" in action.assertions:
                code += f"    cy.url().should('include', '{action.target}');\n"

        elif action.type == "click":
            code += f"    cy.get('{action.target}').click();\n"
            if action.assertions and "visible" in action.assertions:
                code += f"    cy.get('{action.target}').should('be.visible');\n"

        elif action.type == "form":
            if action.data:
                for field, value in action.data.items():
                    selector = f"{action.target} [name=\"{field}\"]"
                    code += f"    cy.get('{selector}').type('{value}');\n"
            code += f"    cy.get('{action.target}').click();\n"
            if action.assertions:
                if "form_valid" in action.assertions:
                    code += f"    cy.get('{action.target}').should('have.class', 'valid');\n"
                if "submit_success" in action.assertions:
                    code += "    cy.get('.success-message').should('be.visible');\n"

    code += "  });\n});\n"

    # Save test file
    Path(output_path).write_text(code)
