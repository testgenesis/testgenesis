#!/usr/bin/env python
"""
Reusable E2E test framework for generating Amplitude events using Playwright.
This can be used to create predictable user journeys for testing TestGenesis.
"""

import argparse
import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from playwright.async_api import Browser, Page, async_playwright


class AmplitudeEventGenerator:
    """Generate Amplitude events through automated browser interactions."""

    def __init__(self, base_url: str = "http://localhost:8050", headless: bool = True):
        self.base_url = base_url
        self.headless = headless
        self.browser: Browser | None = None
        self.page: Page | None = None
        self.events_generated = []

    async def setup(self):
        """Initialize Playwright browser and page."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        context = await self.browser.new_context()
        self.page = await context.new_page()

        # Log console messages for debugging
        self.page.on("console", lambda msg: print(f"[Browser Console] {msg.text}"))

    async def teardown(self):
        """Clean up browser resources."""
        if self.browser:
            await self.browser.close()

    async def wait_for_amplitude(self, milliseconds: int = 1000):
        """Wait for Amplitude events to be sent."""
        await self.page.wait_for_timeout(milliseconds)

    async def login_flow(self, email: str = "test@example.com", password: str = "password123", should_fail: bool = False):
        """Execute a login flow."""
        print(f"[{datetime.now()}] Starting login flow (should_fail={should_fail})...")

        # Navigate to login page
        await self.page.goto(f"{self.base_url}/login")
        await self.wait_for_amplitude()

        # Fill in login form
        await self.page.fill('input[type="email"]', email if not should_fail else "wrong@example.com")
        await self.page.fill('input[type="password"]', password if not should_fail else "wrongpass")
        await self.wait_for_amplitude()

        # Submit form
        await self.page.click('button:has-text("Login")')
        await self.wait_for_amplitude(2000)

        self.events_generated.append({
            "flow": "login",
            "success": not should_fail,
            "timestamp": datetime.now().isoformat()
        })

        print(f"  ✓ Login flow completed (success={not should_fail})")

    async def shopping_flow(self):
        """Execute a shopping cart flow."""
        print(f"[{datetime.now()}] Starting shopping flow...")

        # Navigate to store
        await self.page.goto(f"{self.base_url}/store")
        await self.wait_for_amplitude()

        # View products
        products = await self.page.query_selector_all('.product-card')
        if products:
            # Click on first product
            await products[0].click()
            await self.wait_for_amplitude()

        # Add to cart (if button exists)
        add_to_cart = await self.page.query_selector('button:has-text("Add to Cart")')
        if add_to_cart:
            await add_to_cart.click()
            await self.wait_for_amplitude()

        # Go to cart
        await self.page.goto(f"{self.base_url}/cart")
        await self.wait_for_amplitude()

        # Proceed to checkout
        await self.page.goto(f"{self.base_url}/checkout")
        await self.wait_for_amplitude()

        # Fill checkout form if present
        if await self.page.query_selector('input[name="cardNumber"]'):
            await self.page.fill('input[name="cardNumber"]', '4242424242424242')
            await self.page.fill('input[name="cardName"]', 'Test User')
            await self.page.fill('input[name="expiryDate"]', '12/25')
            await self.page.fill('input[name="cvv"]', '123')
            await self.wait_for_amplitude()

            # Complete purchase
            complete_btn = await self.page.query_selector('button:has-text("Complete Purchase")')
            if complete_btn:
                await complete_btn.click()
                await self.wait_for_amplitude(2000)

        self.events_generated.append({
            "flow": "shopping",
            "timestamp": datetime.now().isoformat()
        })

        print("  ✓ Shopping flow completed")

    async def profile_flow(self):
        """Execute a profile management flow."""
        print(f"[{datetime.now()}] Starting profile flow...")

        # Navigate to profile
        await self.page.goto(f"{self.base_url}/profile")
        await self.wait_for_amplitude()

        # Update profile if form exists
        if await self.page.query_selector('input[name="name"]'):
            await self.page.fill('input[name="name"]', 'Updated Name')
            await self.page.fill('input[name="email"]', 'updated@example.com')
            await self.wait_for_amplitude()

            save_btn = await self.page.query_selector('button:has-text("Save")')
            if save_btn:
                await save_btn.click()
                await self.wait_for_amplitude()

        self.events_generated.append({
            "flow": "profile",
            "timestamp": datetime.now().isoformat()
        })

        print("  ✓ Profile flow completed")

    async def error_flow(self, flow_type: str = "login"):
        """Trigger error states in specific flows."""
        print(f"[{datetime.now()}] Starting error flow for {flow_type}...")

        # Toggle error state
        await self.page.goto(f"{self.base_url}/api/toggle-error/{flow_type}")
        await self.wait_for_amplitude()

        # Execute the flow with error
        if flow_type == "login":
            await self.login_flow(should_fail=True)
        elif flow_type == "checkout":
            await self.shopping_flow()  # This will fail at checkout

        # Toggle error state back off
        await self.page.goto(f"{self.base_url}/api/toggle-error/{flow_type}")

        self.events_generated.append({
            "flow": f"error_{flow_type}",
            "timestamp": datetime.now().isoformat()
        })

        print(f"  ✓ Error flow completed for {flow_type}")

    async def run_complete_journey(self, iterations: int = 1, include_errors: bool = True):
        """Run a complete user journey multiple times."""
        print(f"\n{'='*60}")
        print("Starting E2E Amplitude Event Generation")
        print(f"Base URL: {self.base_url}")
        print(f"Iterations: {iterations}")
        print(f"Include Errors: {include_errors}")
        print(f"{'='*60}\n")

        await self.setup()

        try:
            for i in range(iterations):
                print(f"\n--- Iteration {i+1}/{iterations} ---")

                # Standard flows
                await self.login_flow()
                await self.shopping_flow()
                await self.profile_flow()

                # Error flows (on second iteration)
                if include_errors and i == 1:
                    await self.error_flow("login")
                    await self.error_flow("checkout")

                if i < iterations - 1:
                    print("\nWaiting 3 seconds before next iteration...")
                    await asyncio.sleep(3)

            # Save generated events log
            self.save_events_log()

        finally:
            await self.teardown()

        print(f"\n{'='*60}")
        print("E2E Event Generation Complete!")
        print(f"Total flows executed: {len(self.events_generated)}")
        print(f"{'='*60}\n")

        return self.events_generated

    def save_events_log(self):
        """Save a log of generated events for reference."""
        log_path = Path("generated_events.json")
        with open(log_path, "w") as f:
            json.dump({
                "generation_time": datetime.now().isoformat(),
                "base_url": self.base_url,
                "events": self.events_generated
            }, f, indent=2)
        print(f"\nEvents log saved to: {log_path}")


class AmplitudeDataExtractor:
    """Extract and verify Amplitude data using TestGenesis CLI."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def extract_flows(self, start_date: str = None, end_date: str = None, output_dir: str = "./test_flows"):
        """Extract flows from Amplitude using TestGenesis CLI."""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        print(f"\n{'='*60}")
        print("Extracting Amplitude Flows")
        print(f"Date Range: {start_date} to {end_date}")
        print(f"Output Directory: {output_dir}")
        print(f"{'='*60}\n")

        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Build command
        cmd = [
            "testgenesis", "amplitude", "extract-flows",
            "--api-key", self.api_key,
            "--start-date", start_date,
            "--end-date", end_date,
            "--output-dir", output_dir
        ]

        # Execute extraction
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            print("✓ Flow extraction successful!")
            print(f"Flows saved to: {output_dir}")

            # List extracted flows
            flows = list(Path(output_dir).glob("*.json"))
            print(f"\nExtracted {len(flows)} flows:")
            for flow in flows[:5]:  # Show first 5
                print(f"  - {flow.name}")
            if len(flows) > 5:
                print(f"  ... and {len(flows) - 5} more")
        else:
            print("✗ Flow extraction failed!")
            print(f"Error: {stderr.decode()}")

        return proc.returncode == 0


async def main():
    """Main entry point for the E2E testing framework."""
    parser = argparse.ArgumentParser(description="Generate and extract Amplitude events for E2E testing")
    parser.add_argument("--base-url", default="http://localhost:8050", help="Base URL of the test app")
    parser.add_argument("--iterations", type=int, default=3, help="Number of test iterations")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--include-errors", action="store_true", default=True, help="Include error flows")
    parser.add_argument("--extract", action="store_true", help="Extract flows after generation")
    parser.add_argument("--api-key", help="Amplitude API key for extraction")
    parser.add_argument("--output-dir", default="./test_flows", help="Output directory for extracted flows")

    args = parser.parse_args()

    # Generate events
    generator = AmplitudeEventGenerator(base_url=args.base_url, headless=args.headless)
    events = await generator.run_complete_journey(
        iterations=args.iterations,
        include_errors=args.include_errors
    )

    # Extract flows if requested
    if args.extract:
        if not args.api_key:
            # Try to get from environment
            args.api_key = os.getenv("AMPLITUDE_API_KEY", "da0e05f882b7795f28eaba07890d418d")

        print("\nWaiting 10 seconds for Amplitude to process events...")
        await asyncio.sleep(10)

        extractor = AmplitudeDataExtractor(api_key=args.api_key)
        await extractor.extract_flows(output_dir=args.output_dir)

    print("\n✅ E2E testing complete!")
    print("\nNext steps:")
    print("1. Check the generated_events.json file for event details")
    print("2. Use TestGenesis CLI to extract flows from Amplitude")
    print("3. Generate tests from the extracted flows")


if __name__ == "__main__":
    asyncio.run(main())
