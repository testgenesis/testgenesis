#!/usr/bin/env python
"""Generate test events by interacting with the test app."""

import time
from datetime import datetime

import requests

BASE_URL = "http://localhost:8050"


def simulate_user_journey():
    """Simulate a complete user journey through the app."""
    session = requests.Session()

    print(f"Starting user journey simulation at {datetime.now()}")

    # Visit home page
    print("1. Visiting home page...")
    response = session.get(BASE_URL)
    print(f"   Status: {response.status_code}")
    time.sleep(1)

    # Visit login page
    print("2. Visiting login page...")
    response = session.get(f"{BASE_URL}/login")
    print(f"   Status: {response.status_code}")
    time.sleep(1)

    # Attempt login (this will fail but generate events)
    print("3. Attempting login...")
    # Note: NiceGUI apps typically use WebSocket for form submission
    # For simplicity, we'll just visit the pages to generate page view events

    # Visit store page
    print("4. Visiting store page...")
    response = session.get(f"{BASE_URL}/store")
    print(f"   Status: {response.status_code}")
    time.sleep(1)

    # Visit cart page
    print("5. Visiting cart page...")
    response = session.get(f"{BASE_URL}/cart")
    print(f"   Status: {response.status_code}")
    time.sleep(1)

    # Visit profile page
    print("6. Visiting profile page...")
    response = session.get(f"{BASE_URL}/profile")
    print(f"   Status: {response.status_code}")
    time.sleep(1)

    # Visit checkout page
    print("7. Visiting checkout page...")
    response = session.get(f"{BASE_URL}/checkout")
    print(f"   Status: {response.status_code}")
    time.sleep(1)

    print(f"\nUser journey completed at {datetime.now()}")
    print("Events should now be available in Amplitude")


def simulate_error_flows():
    """Simulate flows that trigger errors."""
    session = requests.Session()

    print(f"\nSimulating error flows at {datetime.now()}")

    # Toggle login error
    print("1. Toggling login error...")
    response = session.get(f"{BASE_URL}/api/toggle-error/login")
    print(f"   Response: {response.text if response.status_code == 200 else response.status_code}")
    time.sleep(1)

    # Try login with error enabled
    print("2. Visiting login page (with error enabled)...")
    response = session.get(f"{BASE_URL}/login")
    print(f"   Status: {response.status_code}")
    time.sleep(1)

    # Toggle checkout error
    print("3. Toggling checkout error...")
    response = session.get(f"{BASE_URL}/api/toggle-error/checkout")
    print(f"   Response: {response.text if response.status_code == 200 else response.status_code}")
    time.sleep(1)

    # Try checkout with error enabled
    print("4. Visiting checkout page (with error enabled)...")
    response = session.get(f"{BASE_URL}/checkout")
    print(f"   Status: {response.status_code}")
    time.sleep(1)

    print(f"\nError flow simulation completed at {datetime.now()}")


if __name__ == "__main__":
    # Run multiple user journeys to generate enough data
    for i in range(3):
        print(f"\n{'=' * 50}")
        print(f"SIMULATION RUN {i + 1}/3")
        print(f"{'=' * 50}")

        simulate_user_journey()

        if i == 1:  # Add some error flows in the second run
            simulate_error_flows()

        if i < 2:
            print("\nWaiting 5 seconds before next simulation...")
            time.sleep(5)

    print(f"\n{'=' * 50}")
    print("ALL SIMULATIONS COMPLETE")
    print(f"{'=' * 50}")
    print("\nYou can now use the TestGenesis CLI to extract flows from Amplitude")
    print("Example command:")
    print("  testgenesis amplitude extract-flows \\")
    print("    --api-key da0e05f882b7795f28eaba07890d418d \\")
    print("    --start-date $(date -v-1d +%Y-%m-%d) \\")
    print("    --end-date $(date +%Y-%m-%d) \\")
    print("    --output-dir ./test_flows")
