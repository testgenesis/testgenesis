"""Test code generators for different frameworks."""

from .cypress import generate_cypress_test
from .playwright import generate_playwright_test


def generate_test_code(flow_path: str, framework: str, output_path: str) -> None:
    """Generate test code for the specified framework."""
    if framework == "playwright":
        generate_playwright_test(flow_path, output_path)
    elif framework == "cypress":
        generate_cypress_test(flow_path, output_path)
    else:
        raise ValueError(f"Unsupported framework: {framework}")


__all__ = ["generate_cypress_test", "generate_playwright_test", "generate_test_code"]
