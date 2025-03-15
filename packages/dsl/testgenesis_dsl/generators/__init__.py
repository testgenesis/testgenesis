"""Test code generators for different frameworks."""

from .playwright import generate_playwright_test
from .cypress import generate_cypress_test


def generate_test_code(flow_path: str, framework: str, output_path: str) -> None:
    """Generate test code for the specified framework."""
    if framework == "playwright":
        generate_playwright_test(flow_path, output_path)
    elif framework == "cypress":
        generate_cypress_test(flow_path, output_path)
    else:
        raise ValueError(f"Unsupported framework: {framework}")


__all__ = ["generate_test_code", "generate_playwright_test", "generate_cypress_test"]
