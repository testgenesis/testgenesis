"""Cypress test code generator."""

from ..models.test_flow import UserAction, TestFlow


def generate_action(action: UserAction) -> str:
    """Generate Cypress code for a user action."""
    code = []
    
    if action.wait_for:
        code.append(f"cy.get('{action.wait_for}', {{ timeout: {action.timeout} }})")
    
    if action.type == "navigation":
        code.append(f"cy.visit('{action.target}')")
        if "url" in action.assertions:
            code.append(f"cy.url().should('include', '{action.target}')")
        if "title" in action.assertions:
            code.append("cy.title().should('match', /.*/)")
            
    elif action.type == "click":
        code.append(f"cy.get('{action.target}').click()")
        
    elif action.type == "form":
        for field, value in action.data.items():
            code.append(
                f"cy.get('{action.target} [name=\"{field}\"]').type('{value}')"
            )
        code.append(f"cy.get('{action.target} [type=\"submit\"]').click()")
        
    return "\n".join(code)


def generate_test(flow: TestFlow) -> str:
    """Generate a complete Cypress test file."""
    code = [
        f"describe('{flow.name}', () => {{",
        "  it('completes successfully', () => {",
    ]
    
    for action in flow.actions:
        code.extend(f"    {line}" for line in generate_action(action).split("\n"))
        
    code.extend([
        "  })",
        "})"
    ])
    return "\n".join(code) 