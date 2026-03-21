#!/usr/bin/env python3
"""
SimplyMiles API Scraper for AA Points Monitor.

Uses the discovered JSON API instead of DOM scraping.
Much faster and more reliable than browser-based scraping.

Requires prior authentication via scripts/setup_auth.py to maintain cookies.

Usage:
    python scrapers/simplymiles_api.py         # Full scrape
    python scrapers/simplymiles_api.py --test  # Test run (no DB writes)
"""

import argparse
import asyncio
import logging
import re
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright

from config.settings import get_settings
from core.database import get_database
from core.normalizer import normalize_merchant

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# Suppress httpx verbose logging (logs every HTTP request at INFO level)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# API endpoint discovered via network capture
API_URL = "https://www.simplymiles.com/get-pclo-and-rakuten-offers"


def load_cookies_from_json() -> Tuple[Dict[str, str], Optional[str]]:
    """
    Load cookies from JSON file (for VPS deployment where browser context doesn't work).

    Returns:
        Tuple of (cookies dict, xsrf_token)
    """
    import json
    cookies_file = project_root / "simplymiles_cookies.json"

    if not cookies_file.exists():
        return {}, None

    with open(cookies_file) as f:
        cookies = json.load(f)

    cookie_dict = {}
    xsrf_token = None

    for c in cookies:
        cookie_dict[c['name']] = c['value']
        if c['name'] == 'XSRF-TOKEN':
            xsrf_token = urllib.parse.unquote(c['value'])

    logger.info(f"Loaded {len(cookie_dict)} cookies from JSON file")
    return cookie_dict, xsrf_token


async def extract_cookies_from_browser() -> Tuple[Dict[str, str], Optional[str]]:
    """
    Extract cookies and XSRF token from the persistent browser session.
    Falls back to JSON file if browser extraction fails.

    Returns:
        Tuple of (cookies dict, xsrf_token)
    """
    settings = get_settings()

    try:
        async with async_playwright() as p:
            # Use headless mode - just extracting cookies, no rendering
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

        if not cookie_dict:
            logger.warning("No cookies from browser, trying JSON file...")
            return load_cookies_from_json()

        return cookie_dict, xsrf_token

    except Exception as e:
        logger.warning(f"Browser extraction failed ({e}), trying JSON file...")
        return load_cookies_from_json()


def parse_offer_headline(headline: str) -> Dict[str, Any]:
    """
    Parse offer headline to extract miles, LP, and min_spend.

    Examples:
    - "135 miles + 135 Loyalty Points on a purchase of $5 or more"
    - "4 miles + 4 Loyalty Points per $1 spent on any purchase"

    Returns:
        Dict with offer_type, miles_amount, lp_amount, min_spend
    """
    result = {
        'offer_type': 'unknown',
        'miles_amount': 0,
        'lp_amount': 0,
        'min_spend': None
    }

    text = headline.lower().strip()

    # Flat bonus: "X miles + X Loyalty Points on a purchase of $Y or more"
    flat_pattern = r'(\d+)\s*miles?\s*\+\s*(\d+)\s*loyalty\s*points?\s*on\s*(?:a\s*)?purchase\s*of\s*\$(\d+(?:\.\d+)?)'
    flat_match = re.search(flat_pattern, text)

    if flat_match:
        result['offer_type'] = 'flat_bonus'
        result['miles_amount'] = int(flat_match.group(1))
        result['lp_amount'] = int(flat_match.group(2))
        result['min_spend'] = float(flat_match.group(3))
        return result

    # Per-dollar: "X miles + X Loyalty Points per $1 spent"
    per_dollar_pattern = r'(\d+)\s*miles?\s*\+\s*(\d+)\s*loyalty\s*points?\s*per\s*\$1'
    per_dollar_match = re.search(per_dollar_pattern, text)

    if per_dollar_match:
        result['offer_type'] = 'per_dollar'
        result['miles_amount'] = int(per_dollar_match.group(1))
        result['lp_amount'] = int(per_dollar_match.group(2))
        result['min_spend'] = None
        return result

    # Fallback: extract numbers
    miles_match = re.search(r'(\d+)\s*miles?', text)
    lp_match = re.search(r'(\d+)\s*loyalty\s*points?', text)
    spend_match = re.search(r'\$(\d+(?:\.\d+)?)', text)

    if miles_match:
        result['miles_amount'] = int(miles_match.group(1))
    if lp_match:
        result['lp_amount'] = int(lp_match.group(1))
    if spend_match:
        result['min_spend'] = float(spend_match.group(1))

    if 'per' in text:
        result['offer_type'] = 'per_dollar'
    elif result['min_spend']:
        result['offer_type'] = 'flat_bonus'

    return result


async def fetch_offers_via_api(cookies: Dict[str, str], xsrf_token: Optional[str]) -> List[Dict[str, Any]]:
    """
    Fetch all offers from the SimplyMiles API.

    Args:
        cookies: Session cookies
        xsrf_token: CSRF token

    Returns:
        List of parsed offer dictionaries
    """
    offers = []

    # Build headers
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

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            API_URL,
            headers=headers,
            json={"page_type": "landing"}
        )

        if response.status_code != 200:
            logger.error(f"API returned status {response.status_code}")
            return offers

        data = response.json()

        # Get all offers (not just featured)
        all_offers = data.get('offers', [])
        featured = data.get('featured_offers', [])

        logger.info(f"API returned {len(all_offers)} offers ({len(featured)} featured)")

        # Process all offers
        for offer_data in all_offers:
            try:
                merchant = offer_data.get('Merchant', {})
                merchant_name = merchant.get('Name', '')

                if not merchant_name:
                    continue

                # Parse offer details from headline
                headline = offer_data.get('Headline', offer_data.get('ShortDescription', ''))
                parsed = parse_offer_headline(headline)

                # Get expiration date
                expires_at = None
                end_date = offer_data.get('EventEndDate')
                if end_date:
                    try:
                        expires_at = datetime.strptime(end_date, '%Y-%m-%d').isoformat()
                    except:
                        pass

                # Check if expiring soon (within 48 hours)
                expiring_soon = False
                if expires_at:
                    try:
                        exp_dt = datetime.fromisoformat(expires_at)
                        hours_left = (exp_dt - datetime.now()).total_seconds() / 3600
                        expiring_soon = hours_left <= 48
                    except:
                        pass

                offer = {
                    'merchant_name': merchant_name,
                    'merchant_name_normalized': normalize_merchant(merchant_name),
                    'offer_type': parsed['offer_type'],
                    'miles_amount': parsed['miles_amount'],
                    'lp_amount': parsed['lp_amount'],
                    'min_spend': parsed['min_spend'],
                    'expires_at': expires_at,
                    'expiring_soon': expiring_soon,
                    'raw_text': headline[:500],
                    'category': merchant.get('Category', ''),
                    'offer_id': offer_data.get('OfferId', ''),
                }

                if offer['miles_amount'] > 0:
                    offers.append(offer)

            except Exception as e:
                logger.warning(f"Error parsing offer: {e}")
                continue

    return offers


async def validate_session_quick(cookies: Dict[str, str], xsrf_token: Optional[str]) -> bool:
    """
    Quick session validation before running full scrape.

    Returns:
        True if session appears valid
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
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                API_URL,
                headers=headers,
                json={"page_type": "landing"}
            )

            if response.status_code == 200:
                data = response.json()
                offers = data.get('offers', [])
                return len(offers) > 0
            return False

    except Exception as e:
        logger.warning(f"Session validation check failed: {e}")
        return False


def record_successful_scrape():
    """Record successful scrape for session tracking."""
    try:
        from scripts.session_keepalive import record_scrape_success
        record_scrape_success()
    except Exception as e:
        logger.debug(f"Could not record scrape success: {e}")


async def run_scraper(test_mode: bool = False) -> Dict[str, Any]:
    """
    Main scraper function using API.

    Args:
        test_mode: If True, don't write to database

    Returns:
        Dict with status and statistics
    """
    result = {
        'status': 'unknown',
        'offers_scraped': 0,
        'method': 'api',
        'errors': [],
        'timestamp': datetime.now().isoformat()
    }

    try:
        # Extract cookies from browser session
        logger.info("Extracting cookies from browser session...")
        cookies, xsrf_token = await extract_cookies_from_browser()

        if not cookies:
            logger.error("No cookies found! Run setup_auth.py first.")
            result['status'] = 'auth_required'
            result['errors'].append("No session cookies - re-authentication required")

            # Send re-auth notification immediately
            try:
                from alerts.sender import send_reauth_notification
                send_reauth_notification()
            except Exception as e:
                logger.warning(f"Could not send re-auth notification: {e}")

            return result

        if not xsrf_token:
            logger.warning("No XSRF token found - API call may fail")

        # Quick session validation before full scrape
        logger.info("Validating session...")
        if not await validate_session_quick(cookies, xsrf_token):
            logger.error("Session validation failed - session may be expired")
            result['status'] = 'session_expired'
            result['errors'].append("Session validation failed - re-authentication required")

            # Send re-auth notification
            try:
                from alerts.sender import send_reauth_notification
                send_reauth_notification()
            except Exception as e:
                logger.warning(f"Could not send re-auth notification: {e}")

            return result

        logger.info("Session valid - proceeding with scrape")

        # Fetch offers via API
        logger.info("Fetching offers via API...")
        offers = await fetch_offers_via_api(cookies, xsrf_token)

        if not offers:
            logger.error("No offers returned from API")
            result['status'] = 'no_data'
            result['errors'].append("API returned no offers - session may be expired")

            # Send re-auth notification
            try:
                from alerts.sender import send_reauth_notification
                await send_reauth_notification()
            except Exception as e:
                logger.warning(f"Could not send re-auth notification: {e}")

            return result

        logger.info(f"Fetched {len(offers)} offers via API")
        result['offers_scraped'] = len(offers)

        # Store in database
        if not test_mode:
            db = get_database()
            scraped_at = datetime.now().isoformat()

            db.clear_simplymiles_offers()

            for offer in offers:
                try:
                    db.insert_simplymiles_offer(
                        merchant_name=offer['merchant_name'],
                        merchant_name_normalized=offer['merchant_name_normalized'],
                        offer_type=offer['offer_type'],
                        miles_amount=offer['miles_amount'],
                        lp_amount=offer['lp_amount'],
                        min_spend=offer['min_spend'],
                        expires_at=offer['expires_at'],
                        expiring_soon=offer['expiring_soon'],
                        scraped_at=scraped_at
                    )

                    # Record discovery for "New This Week" tracking
                    yield_ratio = offer.get('yield_ratio', 0)
                    if yield_ratio <= 0 and offer['min_spend'] and offer['min_spend'] > 0:
                        total_miles = offer['miles_amount'] + offer['lp_amount']
                        yield_ratio = total_miles / offer['min_spend']
                    db.upsert_discovery(
                        deal_type='simplymiles',
                        deal_identifier=offer['merchant_name_normalized'],
                        yield_value=yield_ratio
                    )
                except Exception as e:
                    logger.warning(f"Error inserting offer: {e}")
                    result['errors'].append(str(e))

            db.record_scraper_run(
                scraper_name="simplymiles",
                status="success",
                items_scraped=len(offers)
            )

            logger.info(f"Stored {len(offers)} offers in database")

            # Record successful scrape for session tracking
            record_successful_scrape()

        else:
            logger.info("Test mode - not writing to database")
            logger.info("\nTop 10 offers by miles:")
            sorted_offers = sorted(offers, key=lambda x: x['miles_amount'], reverse=True)
            for offer in sorted_offers[:10]:
                logger.info(f"  - {offer['merchant_name']}: {offer['miles_amount']} miles ({offer['offer_type']})")

        result['status'] = 'success'

    except Exception as e:
        logger.error(f"Scraper error: {e}")
        result['status'] = 'error'
        result['errors'].append(str(e))

        if not test_mode:
            db = get_database()
            db.record_scraper_run(
                scraper_name="simplymiles",
                status="failure",
                error_message=str(e)
            )

    return result


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(description="SimplyMiles API Scraper")
    parser.add_argument("--test", action="store_true", help="Test mode (no DB writes)")
    args = parser.parse_args()

    logger.info("Starting SimplyMiles API scraper...")

    result = asyncio.run(run_scraper(test_mode=args.test))

    logger.info(f"Scraper finished: {result['status']}")
    logger.info(f"Offers scraped: {result['offers_scraped']}")
    logger.info(f"Method: {result.get('method', 'unknown')}")

    if result['errors']:
        logger.warning(f"Errors: {result['errors']}")

    if result['status'] not in ['success']:
        sys.exit(1)


if __name__ == "__main__":
    main()
