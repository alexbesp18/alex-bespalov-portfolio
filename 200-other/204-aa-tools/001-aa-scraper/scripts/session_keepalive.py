#!/usr/bin/env python3
"""
Session Keep-Alive for SimplyMiles.

Periodically visits SimplyMiles to refresh the session and prevent expiry.
Designed to run as a cron job every 6 hours.

Usage:
    python scripts/session_keepalive.py         # Normal run
    python scripts/session_keepalive.py --test  # Dry run (check only, no refresh)

Cron (every 6 hours):
    0 */6 * * * cd /root/aa_scraper && python scripts/session_keepalive.py >> logs/keepalive.log 2>&1
"""

import argparse
import asyncio
import json
import logging
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import httpx

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright

from config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API endpoint for validation
API_URL = "https://www.simplymiles.com/get-pclo-and-rakuten-offers"
SIMPLYMILES_URL = "https://www.simplymiles.com/home"

# Session tracking file
SESSION_TRACKING_FILE = project_root / "data" / "session_tracking.json"


def load_session_tracking() -> Dict:
    """Load session tracking data."""
    if SESSION_TRACKING_FILE.exists():
        with open(SESSION_TRACKING_FILE) as f:
            return json.load(f)
    return {"last_auth": None, "last_keepalive": None, "last_successful_scrape": None}


def save_session_tracking(data: Dict):
    """Save session tracking data."""
    SESSION_TRACKING_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SESSION_TRACKING_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_session_age_days() -> Optional[float]:
    """Get session age in days since last auth."""
    tracking = load_session_tracking()
    last_auth = tracking.get("last_auth")

    if not last_auth:
        return None

    try:
        auth_dt = datetime.fromisoformat(last_auth)
        age = (datetime.now() - auth_dt).total_seconds() / 86400
        return age
    except:
        return None


def record_keepalive_success():
    """Record successful keepalive."""
    tracking = load_session_tracking()
    tracking["last_keepalive"] = datetime.now().isoformat()
    save_session_tracking(tracking)


def record_auth_success():
    """Record successful authentication (call from setup_auth.py)."""
    tracking = load_session_tracking()
    tracking["last_auth"] = datetime.now().isoformat()
    tracking["last_keepalive"] = datetime.now().isoformat()
    save_session_tracking(tracking)


def record_scrape_success():
    """Record successful scrape (call from simplymiles_api.py)."""
    tracking = load_session_tracking()
    tracking["last_successful_scrape"] = datetime.now().isoformat()
    save_session_tracking(tracking)


async def extract_cookies_from_browser() -> Tuple[Dict[str, str], Optional[str]]:
    """Extract cookies from persistent browser context."""
    settings = get_settings()

    try:
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(settings.browser_data_path),
                headless=True,
            )

            cookies = await context.cookies(["https://www.simplymiles.com"])
            await context.close()

        cookie_dict = {}
        xsrf_token = None

        for c in cookies:
            cookie_dict[c['name']] = c['value']
            if c['name'] == 'XSRF-TOKEN':
                xsrf_token = urllib.parse.unquote(c['value'])

        return cookie_dict, xsrf_token

    except Exception as e:
        logger.error(f"Failed to extract cookies: {e}")
        return {}, None


async def validate_session(cookies: Dict[str, str], xsrf_token: Optional[str]) -> bool:
    """
    Validate session by making a lightweight API call.

    Returns:
        True if session is valid
    """
    if not cookies:
        return False

    cookie_str = '; '.join(f"{k}={v}" for k, v in cookies.items())

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Cookie': cookie_str,
        'Referer': 'https://www.simplymiles.com/home',
        'Origin': 'https://www.simplymiles.com',
    }

    if xsrf_token:
        headers['X-XSRF-TOKEN'] = xsrf_token

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                API_URL,
                headers=headers,
                json={"page_type": "landing"}
            )

            if response.status_code == 200:
                data = response.json()
                offers = data.get('offers', [])
                logger.info(f"Session valid - API returned {len(offers)} offers")
                return len(offers) > 0
            else:
                logger.warning(f"API returned status {response.status_code}")
                return False

    except Exception as e:
        logger.error(f"Session validation failed: {e}")
        return False


def export_cookies_to_json(cookies: list) -> bool:
    """Export cookies to JSON file for VPS deployment."""
    cookies_file = project_root / "simplymiles_cookies.json"
    try:
        with open(cookies_file, 'w') as f:
            json.dump(cookies, f, indent=2)
        logger.info(f"Exported {len(cookies)} cookies to {cookies_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to export cookies: {e}")
        return False


async def refresh_session_via_browser() -> bool:
    """
    Refresh session by visiting SimpleMiles in browser.
    This triggers cookie refresh on the backend.
    Also exports fresh cookies to JSON for VPS use.

    Returns:
        True if refresh successful
    """
    settings = get_settings()

    try:
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(settings.browser_data_path),
                headless=True,
            )

            page = await context.new_page()

            # Visit the home page to trigger session refresh
            logger.info(f"Visiting {SIMPLYMILES_URL} to refresh session...")
            response = await page.goto(SIMPLYMILES_URL, timeout=30000)

            if response and response.ok:
                # Wait for page to fully load and session to refresh
                await page.wait_for_timeout(3000)

                # Check if we're logged in by looking for offers
                try:
                    offers_text = await page.text_content("body", timeout=5000)
                    if "OFFERS AVAILABLE" in offers_text.upper() or "offers" in offers_text.lower():
                        logger.info("Session refresh successful - logged in state confirmed")

                        # Export fresh cookies to JSON for VPS
                        cookies = await context.cookies(["https://www.simplymiles.com"])
                        export_cookies_to_json(cookies)

                        await context.close()
                        return True
                except:
                    pass

                logger.warning("Could not confirm logged-in state after refresh")
                await context.close()
                return False
            else:
                logger.error(f"Page load failed: {response.status if response else 'No response'}")
                await context.close()
                return False

    except Exception as e:
        logger.error(f"Session refresh failed: {e}")
        return False


async def run_keepalive(test_mode: bool = False) -> Dict:
    """
    Run the session keepalive process.

    Args:
        test_mode: If True, only validate without refreshing

    Returns:
        Dict with results
    """
    result = {
        "timestamp": datetime.now().isoformat(),
        "session_valid": False,
        "refresh_attempted": False,
        "refresh_success": False,
        "session_age_days": get_session_age_days(),
        "status": "unknown"
    }

    # Extract cookies
    logger.info("Extracting session cookies...")
    cookies, xsrf_token = await extract_cookies_from_browser()

    if not cookies:
        logger.error("No cookies found - session requires re-authentication")
        result["status"] = "no_session"
        return result

    # Validate session
    logger.info("Validating session...")
    session_valid = await validate_session(cookies, xsrf_token)
    result["session_valid"] = session_valid

    if session_valid:
        if test_mode:
            logger.info("Test mode - session is valid, skipping refresh")
            result["status"] = "valid"
        else:
            # Refresh even if valid to extend expiry
            logger.info("Session valid - refreshing to extend expiry...")
            result["refresh_attempted"] = True
            result["refresh_success"] = await refresh_session_via_browser()

            if result["refresh_success"]:
                record_keepalive_success()
                result["status"] = "refreshed"
                logger.info("Session keepalive successful")
            else:
                result["status"] = "refresh_failed"
                logger.warning("Session refresh failed but session was still valid")
    else:
        logger.error("Session invalid - re-authentication required")
        result["status"] = "expired"

        # Send re-auth notification
        try:
            from alerts.sender import send_reauth_notification
            send_reauth_notification()
            logger.info("Re-auth notification sent")
        except Exception as e:
            logger.error(f"Failed to send re-auth notification: {e}")

    # Log session age warning
    age = result["session_age_days"]
    if age and age > 5:
        logger.warning(f"Session is {age:.1f} days old - consider proactive re-authentication")

    return result


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(description="SimplyMiles Session Keep-Alive")
    parser.add_argument("--test", action="store_true", help="Test mode (validate only)")
    args = parser.parse_args()

    logger.info("=" * 50)
    logger.info("SimplyMiles Session Keep-Alive")
    logger.info("=" * 50)

    result = asyncio.run(run_keepalive(test_mode=args.test))

    logger.info(f"Result: {result['status']}")
    logger.info(f"Session valid: {result['session_valid']}")
    if result['session_age_days']:
        logger.info(f"Session age: {result['session_age_days']:.1f} days")

    if result['status'] in ['expired', 'no_session']:
        sys.exit(1)


if __name__ == "__main__":
    main()
