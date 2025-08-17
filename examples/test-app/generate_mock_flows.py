#!/usr/bin/env python
"""
Generate mock Amplitude flow data for testing TestGenesis.
This simulates the output that would come from Amplitude.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path


def generate_mock_flow(flow_type="standard", frequency=10):
    """Generate a mock flow with Amplitude-style events."""
    base_time = datetime.now() - timedelta(hours=random.randint(1, 24))

    if flow_type == "login_success":
        return {
            "flow_id": f"flow_{random.randint(1000, 9999)}",
            "frequency": frequency,
            "actions": [
                {
                    "type": "navigation",
                    "target": "/",
                    "data": {
                        "[Amplitude] Page URL": "/",
                        "timestamp": base_time.isoformat()
                    }
                },
                {
                    "type": "navigation",
                    "target": "/login",
                    "data": {
                        "[Amplitude] Page URL": "/login",
                        "timestamp": (base_time + timedelta(seconds=2)).isoformat()
                    }
                },
                {
                    "type": "form",
                    "target": "login_form",
                    "data": {
                        "form_name": "login_form",
                        "timestamp": (base_time + timedelta(seconds=5)).isoformat()
                    }
                },
                {
                    "type": "login_success",
                    "data": {
                        "user_id": "user123",
                        "timestamp": (base_time + timedelta(seconds=6)).isoformat()
                    }
                },
                {
                    "type": "[Amplitude] Page Viewed",
                    "data": {
                        "[Amplitude] Page URL": "/dashboard",
                        "timestamp": (base_time + timedelta(seconds=7)).isoformat()
                    }
                }
            ]
        }

    elif flow_type == "shopping_cart":
        return {
            "flow_id": f"flow_{random.randint(1000, 9999)}",
            "frequency": frequency,
            "actions": [
                {
                    "type": "[Amplitude] Page Viewed",
                    "data": {
                        "[Amplitude] Page URL": "/store",
                        "timestamp": base_time.isoformat()
                    }
                },
                {
                    "type": "product_view",
                    "data": {
                        "product_id": "prod_123",
                        "product_name": "Test Product",
                        "timestamp": (base_time + timedelta(seconds=3)).isoformat()
                    }
                },
                {
                    "type": "add_to_cart",
                    "data": {
                        "product_id": "prod_123",
                        "quantity": 1,
                        "timestamp": (base_time + timedelta(seconds=5)).isoformat()
                    }
                },
                {
                    "type": "[Amplitude] Page Viewed",
                    "data": {
                        "[Amplitude] Page URL": "/cart",
                        "timestamp": (base_time + timedelta(seconds=7)).isoformat()
                    }
                },
                {
                    "type": "[Amplitude] Page Viewed",
                    "data": {
                        "[Amplitude] Page URL": "/checkout",
                        "timestamp": (base_time + timedelta(seconds=10)).isoformat()
                    }
                },
                {
                    "type": "checkout_complete",
                    "data": {
                        "order_id": "order_456",
                        "total": 99.99,
                        "timestamp": (base_time + timedelta(seconds=20)).isoformat()
                    }
                }
            ]
        }

    elif flow_type == "login_error":
        return {
            "flow_id": f"flow_{random.randint(1000, 9999)}",
            "frequency": frequency,
            "actions": [
                {
                    "type": "[Amplitude] Page Viewed",
                    "data": {
                        "[Amplitude] Page URL": "/login",
                        "timestamp": base_time.isoformat()
                    }
                },
                {
                    "type": "form_submit",
                    "data": {
                        "form_name": "login_form",
                        "timestamp": (base_time + timedelta(seconds=3)).isoformat()
                    }
                },
                {
                    "type": "error",
                    "data": {
                        "error_code": "invalid_credentials",
                        "error_message": "Invalid email or password",
                        "timestamp": (base_time + timedelta(seconds=4)).isoformat()
                    }
                },
                {
                    "type": "[Amplitude] Page Viewed",
                    "data": {
                        "[Amplitude] Page URL": "/login",
                        "timestamp": (base_time + timedelta(seconds=5)).isoformat()
                    }
                }
            ]
        }

    else:  # Generic page navigation
        pages = ["/", "/about", "/contact", "/profile", "/settings"]
        selected_pages = random.sample(pages, min(3, len(pages)))
        actions = []
        for i, page in enumerate(selected_pages):
            actions.append({
                "type": "[Amplitude] Page Viewed",
                "data": {
                    "[Amplitude] Page URL": page,
                    "timestamp": (base_time + timedelta(seconds=i*3)).isoformat()
                }
            })

        return {
            "flow_id": f"flow_{random.randint(1000, 9999)}",
            "frequency": frequency,
            "actions": actions
        }


def main():
    """Generate mock flow files."""
    output_dir = Path("./test_flows")
    output_dir.mkdir(exist_ok=True)

    print(f"\n{'='*60}")
    print("Generating Mock Amplitude Flows")
    print(f"Output directory: {output_dir}")
    print(f"{'='*60}\n")

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
        filename = f"flow_{i+1:03d}_{flow_type}_{frequency}freq.json"
        filepath = output_dir / filename

        with open(filepath, "w") as f:
            json.dump(flow_data, f, indent=2)

        generated_files.append(filename)
        print(f"✓ Generated: {filename}")

    print(f"\n{'='*60}")
    print("Mock Flow Generation Complete!")
    print(f"Generated {len(generated_files)} flow files")
    print(f"{'='*60}\n")

    print("You can now test TestGenesis with these flows:")
    print(f"  testgenesis generate {output_dir}/flow_001_login_success_25freq.json \\")
    print("    --framework playwright \\")
    print("    --output tests/login.spec.ts")

    return generated_files


if __name__ == "__main__":
    main()
