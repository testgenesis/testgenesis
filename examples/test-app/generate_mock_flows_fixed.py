#!/usr/bin/env python
"""
Generate mock TestGenesis flow data with the correct Action format.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path


def generate_mock_flow(flow_type="standard", frequency=10):
    """Generate a mock flow with correct TestGenesis Action format."""
    base_time = datetime.now() - timedelta(hours=random.randint(1, 24))

    if flow_type == "login_success":
        return {
            "name": f"login_success_flow_{random.randint(1000, 9999)}",
            "frequency": frequency,
            "actions": [
                {"type": "navigation", "target": "/", "data": {"timestamp": base_time.isoformat()}},
                {
                    "type": "navigation",
                    "target": "/login",
                    "data": {"timestamp": (base_time + timedelta(seconds=2)).isoformat()},
                },
                {
                    "type": "form",
                    "target": "login_form",
                    "data": {"timestamp": (base_time + timedelta(seconds=5)).isoformat()},
                },
                {
                    "type": "click",
                    "target": "login_button",
                    "data": {"timestamp": (base_time + timedelta(seconds=6)).isoformat()},
                },
                {
                    "type": "navigation",
                    "target": "/dashboard",
                    "data": {"timestamp": (base_time + timedelta(seconds=7)).isoformat()},
                },
            ],
        }

    elif flow_type == "shopping_cart":
        return {
            "name": f"shopping_cart_flow_{random.randint(1000, 9999)}",
            "frequency": frequency,
            "actions": [
                {
                    "type": "navigation",
                    "target": "/store",
                    "data": {"timestamp": base_time.isoformat()},
                },
                {
                    "type": "click",
                    "target": "product_card",
                    "data": {
                        "product_id": "prod_123",
                        "timestamp": (base_time + timedelta(seconds=3)).isoformat(),
                    },
                },
                {
                    "type": "click",
                    "target": "add_to_cart_button",
                    "data": {
                        "product_id": "prod_123",
                        "timestamp": (base_time + timedelta(seconds=5)).isoformat(),
                    },
                },
                {
                    "type": "navigation",
                    "target": "/cart",
                    "data": {"timestamp": (base_time + timedelta(seconds=7)).isoformat()},
                },
                {
                    "type": "navigation",
                    "target": "/checkout",
                    "data": {"timestamp": (base_time + timedelta(seconds=10)).isoformat()},
                },
                {
                    "type": "form",
                    "target": "checkout_form",
                    "data": {"timestamp": (base_time + timedelta(seconds=15)).isoformat()},
                },
                {
                    "type": "click",
                    "target": "complete_purchase_button",
                    "data": {
                        "order_id": "order_456",
                        "timestamp": (base_time + timedelta(seconds=20)).isoformat(),
                    },
                },
            ],
        }

    elif flow_type == "login_error":
        return {
            "name": f"login_error_flow_{random.randint(1000, 9999)}",
            "frequency": frequency,
            "actions": [
                {
                    "type": "navigation",
                    "target": "/login",
                    "data": {"timestamp": base_time.isoformat()},
                },
                {
                    "type": "form",
                    "target": "login_form",
                    "data": {"timestamp": (base_time + timedelta(seconds=3)).isoformat()},
                },
                {
                    "type": "error",
                    "target": "login_form",
                    "data": {
                        "error_code": "invalid_credentials",
                        "error_message": "Invalid email or password",
                        "timestamp": (base_time + timedelta(seconds=4)).isoformat(),
                    },
                },
            ],
        }

    else:  # Generic page navigation
        pages = ["/", "/about", "/contact", "/profile", "/settings"]
        selected_pages = random.sample(pages, min(3, len(pages)))
        actions = []
        for i, page in enumerate(selected_pages):
            actions.append(
                {
                    "type": "navigation",
                    "target": page,
                    "data": {"timestamp": (base_time + timedelta(seconds=i * 3)).isoformat()},
                }
            )

        return {
            "name": f"generic_flow_{random.randint(1000, 9999)}",
            "frequency": frequency,
            "actions": actions,
        }


def main():
    """Generate mock flow files with correct format."""
    output_dir = Path("./test_flows")
    output_dir.mkdir(exist_ok=True)

    # Clear existing files
    for file in output_dir.glob("*.json"):
        file.unlink()

    print(f"\n{'=' * 60}")
    print("Generating Mock TestGenesis Flows")
    print(f"Output directory: {output_dir}")
    print(f"{'=' * 60}\n")

    # Generate various types of flows
    flows = [
        ("login_success", 25),
        ("login_success", 18),
        ("shopping_cart", 30),
        ("shopping_cart", 22),
        ("login_error", 8),
        ("login_error", 5),
        ("generic", 15),
        ("generic", 12),
        ("generic", 10),
    ]

    generated_files = []

    for i, (flow_type, frequency) in enumerate(flows):
        flow_data = generate_mock_flow(flow_type, frequency)

        # Create descriptive filename
        filename = f"flow_{i + 1:03d}_{flow_type}_{frequency}freq.json"
        filepath = output_dir / filename

        with open(filepath, "w") as f:
            json.dump(flow_data, f, indent=2)

        generated_files.append(filename)
        print(f"✓ Generated: {filename}")

    print(f"\n{'=' * 60}")
    print("Mock Flow Generation Complete!")
    print(f"Generated {len(generated_files)} flow files")
    print(f"{'=' * 60}\n")

    print("You can now test TestGenesis with these flows:")
    print(f"  testgenesis generate {output_dir}/flow_001_login_success_25freq.json \\")
    print("    --framework playwright \\")
    print("    --output tests/generated/login.spec.ts")

    return generated_files


if __name__ == "__main__":
    main()
