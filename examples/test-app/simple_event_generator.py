#!/usr/bin/env python
"""
Simple event generator that visits pages to generate Amplitude page view events.
"""

import asyncio
from datetime import datetime

from playwright.async_api import async_playwright


async def generate_page_views():
    """Generate page view events by visiting different pages."""
    print(f"\n{'='*60}")
    print("Simple Amplitude Event Generator")
    print(f"Starting at: {datetime.now()}")
    print(f"{'='*60}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # List of pages to visit
        pages = [
            "/",
            "/login",
            "/store",
            "/cart",
            "/profile",
            "/checkout",
            "/register"
        ]

        base_url = "http://localhost:8050"

        # Visit each page multiple times to generate data
        for iteration in range(3):
            print(f"\nIteration {iteration + 1}/3")
            for path in pages:
                url = f"{base_url}{path}"
                print(f"  Visiting: {url}")
                try:
                    await page.goto(url, wait_until="networkidle", timeout=10000)
                    await page.wait_for_timeout(500)  # Wait for Amplitude to track
                except Exception as e:
                    print(f"    Warning: {e}")

            if iteration < 2:
                print("  Waiting 2 seconds before next iteration...")
                await asyncio.sleep(2)

        await browser.close()

    print(f"\n{'='*60}")
    print("Event generation complete!")
    print(f"Ended at: {datetime.now()}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(generate_page_views())
