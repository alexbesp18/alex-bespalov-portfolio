#!/usr/bin/env python3
"""
SimplyMiles Authentication Setup Script.

Opens a browser for manual login to SimplyMiles.
Saves the session (cookies, localStorage) to browser_data/ for automated scraping.

Usage:
    python scripts/setup_auth.py

After running, log into SimplyMiles with your AA credentials.
The browser will stay open until you press Enter in the terminal.
Your session will be saved for automated scraping.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright

from config.settings import get_settings


SIMPLYMILES_URL = "https://www.simplymiles.com/"


async def setup_auth():
    """Open browser for manual SimplyMiles login."""
    settings = get_settings()
    browser_data_path = settings.browser_data_path

    print("=" * 60)
    print("SimplyMiles Authentication Setup")
    print("=" * 60)
    print()
    print(f"Browser data will be saved to: {browser_data_path}")
    print()
    print("Instructions:")
    print("1. A browser window will open to SimplyMiles")
    print("2. Log in with your AA credentials")
    print("3. Make sure you can see your offers (142 offers available)")
    print("4. Return to this terminal and press Enter to save & close")
    print()

    async with async_playwright() as p:
        # Launch browser with persistent context
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(browser_data_path),
            headless=False,  # Need visible browser for manual login
            viewport={"width": 1280, "height": 800},
            args=[
                "--disable-blink-features=AutomationControlled",
            ]
        )

        # Open SimplyMiles
        page = await context.new_page()

        print(f"Opening {SIMPLYMILES_URL}...")
        await page.goto(SIMPLYMILES_URL)

        # Wait for user to complete login
        print()
        print("Browser opened. Complete the login process, then return here.")
        input("Press Enter when you're logged in and can see your offers...")

        # Check if logged in
        logged_in = False
        try:
            # Look for offers count indicator
            offers_text = await page.text_content("body", timeout=5000)
            if "OFFERS AVAILABLE" in offers_text.upper():
                print()
                print("SUCCESS! Login detected.")
                print("Session saved to browser_data/")
                logged_in = True
            else:
                print()
                print("Warning: Could not confirm login status.")
                print("Session saved anyway - test with the scraper.")
        except Exception as e:
            print(f"Note: Could not verify login status: {e}")
            print("Session saved anyway - test with the scraper.")

        # Export cookies to JSON for VPS deployment
        print()
        print("Exporting cookies to JSON for VPS...")
        try:
            import json
            cookies = await context.cookies(["https://www.simplymiles.com"])
            cookies_file = project_root / "simplymiles_cookies.json"
            with open(cookies_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            print(f"Exported {len(cookies)} cookies to simplymiles_cookies.json")
        except Exception as e:
            print(f"Warning: Could not export cookies: {e}")

        await context.close()

    # Record authentication timestamp
    print()
    print("Recording authentication timestamp...")
    try:
        from scripts.session_keepalive import record_auth_success
        record_auth_success()
        print("Session tracking updated")
    except Exception as e:
        print(f"Note: Could not update session tracking: {e}")

    print()
    print("=" * 60)
    print("Setup complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Test the scraper: python scrapers/simplymiles_api.py --test")
    print("2. If it works, you're ready for automated scraping")
    print("3. If not, run this setup script again")
    print()


def main():
    """Entry point."""
    try:
        asyncio.run(setup_auth())
    except KeyboardInterrupt:
        print("\nSetup cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during setup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

