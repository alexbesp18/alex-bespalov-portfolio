#!/usr/bin/env python3
"""
Quick Re-Authentication Script for SimplyMiles.

Streamlined re-auth process:
1. Opens browser to SimplyMiles
2. Waits for manual login completion
3. Validates new session
4. Records auth timestamp
5. Sends success confirmation email

Usage:
    python scripts/quick_reauth.py

For VPS with Xvfb:
    export DISPLAY=:99
    python scripts/quick_reauth.py
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright

from config.settings import get_settings

SIMPLYMILES_URL = "https://www.simplymiles.com/"


async def quick_reauth():
    """Streamlined re-authentication process."""
    settings = get_settings()
    browser_data_path = settings.browser_data_path

    print("=" * 60)
    print("SimplyMiles Quick Re-Authentication")
    print("=" * 60)
    print()
    print(f"Browser data: {browser_data_path}")
    print()
    print("INSTRUCTIONS:")
    print("1. Browser window will open to SimplyMiles")
    print("2. Log in with your AA credentials")
    print("3. Make sure you can see your offers")
    print("4. Return here and press Enter to save & verify")
    print()

    # Check if DISPLAY is set (for VPS)
    import os
    display = os.environ.get('DISPLAY')
    if display:
        print(f"Using DISPLAY={display}")
    else:
        print("Note: No DISPLAY set. If on VPS, run: export DISPLAY=:99")
    print()

    async with async_playwright() as p:
        # Launch browser with persistent context
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(browser_data_path),
            headless=False,
            viewport={"width": 1280, "height": 800},
            args=[
                "--disable-blink-features=AutomationControlled",
            ]
        )

        page = await context.new_page()

        print(f"Opening {SIMPLYMILES_URL}...")
        try:
            await page.goto(SIMPLYMILES_URL, timeout=30000)
        except Exception as e:
            print(f"Warning: Page load issue: {e}")
            print("The browser should still be open. Please navigate manually if needed.")

        print()
        print("=" * 60)
        print("BROWSER IS OPEN")
        print("Complete login, then return here and press Enter")
        print("=" * 60)
        input()

        # Verify login
        print("Verifying login status...")
        login_confirmed = False

        try:
            offers_text = await page.text_content("body", timeout=5000)
            if "OFFERS AVAILABLE" in offers_text.upper():
                login_confirmed = True
                print("SUCCESS! Login confirmed - offers detected")
            elif "offers" in offers_text.lower():
                login_confirmed = True
                print("SUCCESS! Login appears successful")
            else:
                print("Warning: Could not confirm login status")
                print("Session saved anyway - test with scraper")
        except Exception as e:
            print(f"Note: Could not verify login: {e}")
            print("Session saved anyway - test with scraper")

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

    # Validate with API call
    print()
    print("Validating session with API...")
    try:
        from scrapers.simplymiles_api import extract_cookies_from_browser, validate_session_quick

        cookies, xsrf = await extract_cookies_from_browser()
        if cookies:
            valid = await validate_session_quick(cookies, xsrf)
            if valid:
                print("API validation successful!")
                login_confirmed = True
            else:
                print("Warning: API validation failed")
                print("Session may not be fully active yet - try running scraper in a few minutes")
        else:
            print("Warning: No cookies found")
    except Exception as e:
        print(f"Note: Could not validate via API: {e}")

    # Send success notification if confirmed
    if login_confirmed:
        print()
        print("Sending success notification...")
        try:
            from alerts.sender import send_email
            success = send_email(
                subject="✅ AA Monitor: SimplyMiles Re-Auth Successful",
                html_content=f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #4caf50;">✅ SimplyMiles Re-Authentication Successful</h2>
                    <p>Your SimplyMiles session has been refreshed.</p>
                    <p><strong>Authenticated at:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>The scraper will resume normal operation on the next scheduled run.</p>
                </div>
                """,
                text_content=f"SimplyMiles re-auth successful at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            if success:
                print("Success notification sent!")
            else:
                print("Note: Could not send notification")
        except Exception as e:
            print(f"Note: Could not send notification: {e}")

    print()
    print("=" * 60)
    print("RE-AUTHENTICATION COMPLETE")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Test the scraper: python scrapers/simplymiles_api.py --test")
    print("2. If successful, normal scraping will resume automatically")
    print()

    return login_confirmed


def main():
    """Entry point."""
    try:
        success = asyncio.run(quick_reauth())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nRe-auth cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during re-auth: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
