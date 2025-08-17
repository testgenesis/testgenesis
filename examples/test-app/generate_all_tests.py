#!/usr/bin/env python
"""Generate Playwright tests for all flow files."""

import os
import subprocess
from pathlib import Path


def generate_tests():
    """Generate tests for all flow files."""
    flows_dir = Path("./test_flows")
    tests_dir = Path("./tests/generated")
    tests_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 60}")
    print("Generating Playwright Tests from Flows")
    print(f"Source: {flows_dir}")
    print(f"Output: {tests_dir}")
    print(f"{'=' * 60}\n")

    generated_tests = []

    # Change to root directory for testgenesis command
    os.chdir("../..")

    for flow_file in flows_dir.glob("*.json"):
        flow_name = flow_file.stem
        test_file = tests_dir / f"{flow_name}.spec.ts"

        print(f"Generating test for: {flow_file.name}")

        try:
            # Use uv run to execute testgenesis
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "testgenesis",
                    "generate",
                    f"examples/test-app/{flow_file}",
                    "--framework",
                    "playwright",
                    "--output",
                    f"examples/test-app/{test_file}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            print(f"  ✓ Generated: {test_file.name}")
            generated_tests.append(test_file.name)

        except subprocess.CalledProcessError as e:
            print(f"  ✗ Failed: {e}")
            print(f"    Error: {e.stderr}")

    print(f"\n{'=' * 60}")
    print("Test Generation Complete!")
    print(f"Generated {len(generated_tests)} test files:")
    for test in generated_tests:
        print(f"  - {test}")
    print(f"{'=' * 60}\n")

    print("To run the tests:")
    print("  cd examples/test-app")
    print("  npx playwright test tests/generated/")


if __name__ == "__main__":
    generate_tests()
