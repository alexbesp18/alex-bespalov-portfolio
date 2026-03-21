#!/usr/bin/env python3
"""
SimplyMiles Scraper for AA Points Monitor.

Scrapes offer cards from SimplyMiles using Playwright with persistent browser context.
Requires prior authentication via scripts/setup_auth.py.

Usage:
    python scrapers/simplymiles.py         # Full scrape
    python scrapers/simplymiles.py --test  # Test run (no DB writes)
"""

import argparse
import asyncio
import logging
import random
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeout

from config.settings import get_settings
from core.database import get_database
from core.normalizer import normalize_merchant

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SIMPLYMILES_URL = "https://www.simplymiles.com/"
OFFERS_URL = "https://www.simplymiles.com/home"


async def random_delay(min_sec: float = 2.0, max_sec: float = 5.0):
    """Add random delay for anti-detection."""
    delay = random.uniform(min_sec, max_sec)
    await asyncio.sleep(delay)


async def is_logged_in(page: Page) -> bool:
    """
    Check if the user is logged into SimplyMiles.

    Returns:
        True if logged in, False otherwise
    """
    try:
        # Look for indicators of logged-in state
        # SimplyMiles shows "X OFFERS AVAILABLE" when logged in
        content = await page.content()

        if "OFFERS AVAILABLE" in content.upper():
            return True

        # Check for login button (indicates NOT logged in)
        login_button = await page.query_selector('a[href*="login"], button:has-text("Log in"), button:has-text("Sign in")')
        if login_button:
            return False

        # Check for offers grid/list
        offers = await page.query_selector('[class*="offer"], [class*="card"], [data-testid*="offer"]')
        if offers:
            return True

        return False

    except Exception as e:
        logger.warning(f"Error checking login status: {e}")
        return False


async def scroll_to_load_all(page: Page, max_scrolls: int = 20):
    """
    Scroll page to load all offers (handles infinite scroll).

    Args:
        page: Playwright page
        max_scrolls: Maximum number of scroll attempts
    """
    logger.info("Scrolling to load all offers...")

    previous_height = 0
    scroll_count = 0

    while scroll_count < max_scrolls:
        # Get current scroll height
        current_height = await page.evaluate("document.body.scrollHeight")

        if current_height == previous_height:
            # No new content loaded
            break

        previous_height = current_height

        # Scroll to bottom
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

        # Wait for potential new content
        await random_delay(1.0, 2.0)
        scroll_count += 1

    logger.info(f"Completed {scroll_count} scroll(s)")

    # Scroll back to top
    await page.evaluate("window.scrollTo(0, 0)")


def parse_offer_text(text: str) -> Dict[str, Any]:
    """
    Parse offer text to extract structured data.

    Handles actual SimplyMiles formats:
    - "135 miles + 135 Loyalty Points on a purchase of $5 or more" (flat bonus)
    - "4 miles + 4 Loyalty Points per $1 spent on any purchase" (per dollar)

    Args:
        text: Raw offer text

    Returns:
        Dict with offer_type, miles_amount, lp_amount, min_spend
    """
    result = {
        'offer_type': 'unknown',
        'miles_amount': 0,
        'lp_amount': 0,
        'min_spend': None
    }

    text = text.lower().strip()

    # Try flat bonus pattern: "X miles + X Loyalty Points on a purchase of $Y or more"
    flat_pattern = r'(\d+)\s*miles?\s*\+\s*(\d+)\s*loyalty\s*points?\s*on\s*a?\s*purchase\s*of\s*\$(\d+(?:\.\d+)?)'
    flat_match = re.search(flat_pattern, text)

    if flat_match:
        result['offer_type'] = 'flat_bonus'
        result['miles_amount'] = int(flat_match.group(1))
        result['lp_amount'] = int(flat_match.group(2))
        result['min_spend'] = float(flat_match.group(3))
        return result

    # Try per-dollar pattern: "X miles + X Loyalty Points per $1 spent"
    per_dollar_pattern = r'(\d+)\s*miles?\s*\+\s*(\d+)\s*loyalty\s*points?\s*per\s*\$1'
    per_dollar_match = re.search(per_dollar_pattern, text)

    if per_dollar_match:
        result['offer_type'] = 'per_dollar'
        result['miles_amount'] = int(per_dollar_match.group(1))
        result['lp_amount'] = int(per_dollar_match.group(2))
        result['min_spend'] = None  # Per-dollar offers don't have min spend
        return result

    # Fallback patterns for variations
    # Pattern with just "LP" abbreviation
    lp_flat_pattern = r'(\d+)\s*miles?\s*\+?\s*(\d+)?\s*lp?\s*on\s*(?:a\s*)?purchase\s*of\s*\$(\d+(?:\.\d+)?)'
    lp_flat_match = re.search(lp_flat_pattern, text)

    if lp_flat_match:
        result['offer_type'] = 'flat_bonus'
        result['miles_amount'] = int(lp_flat_match.group(1))
        result['lp_amount'] = int(lp_flat_match.group(2)) if lp_flat_match.group(2) else result['miles_amount']
        result['min_spend'] = float(lp_flat_match.group(3))
        return result

    lp_per_dollar_pattern = r'(\d+)\s*miles?\s*\+?\s*(\d+)?\s*lp?\s*per\s*\$1'
    lp_per_dollar_match = re.search(lp_per_dollar_pattern, text)

    if lp_per_dollar_match:
        result['offer_type'] = 'per_dollar'
        result['miles_amount'] = int(lp_per_dollar_match.group(1))
        result['lp_amount'] = int(lp_per_dollar_match.group(2)) if lp_per_dollar_match.group(2) else result['miles_amount']
        result['min_spend'] = None
        return result

    # Final fallback: try to extract any numbers
    numbers = re.findall(r'(\d+)', text)
    if numbers:
        result['miles_amount'] = int(numbers[0])
        result['lp_amount'] = int(numbers[1]) if len(numbers) > 1 else int(numbers[0])

        # Check for "per" to determine type
        if 'per' in text:
            result['offer_type'] = 'per_dollar'
        elif 'purchase' in text or 'spend' in text:
            result['offer_type'] = 'flat_bonus'
            # Try to find min spend
            spend_match = re.search(r'\$(\d+(?:\.\d+)?)', text)
            if spend_match:
                result['min_spend'] = float(spend_match.group(1))

    return result


def parse_expiration(text: str) -> Optional[str]:
    """
    Parse expiration date from offer text.

    Args:
        text: Text that may contain expiration date

    Returns:
        ISO format date string or None
    """
    if not text:
        return None

    text = text.lower().strip()

    # Common patterns: "Expires 12/31/2025", "Exp 12/31", "Valid through 12/31/2025"
    patterns = [
        r'expires?\s*:?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',
        r'valid\s*(?:through|until)\s*:?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',
        r'exp\s*:?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            month, day, year = match.groups()
            year = int(year)
            if year < 100:
                year += 2000

            try:
                dt = datetime(year, int(month), int(day))
                return dt.isoformat()
            except ValueError:
                continue

    return None


async def scrape_offers_from_page(page: Page) -> List[Dict[str, Any]]:
    """
    Scrape all offer cards from the current page.

    Uses verified selectors from discovery phase (2024-12-28).

    Args:
        page: Playwright page

    Returns:
        List of offer dictionaries
    """
    offers = []

    # Verified selectors from SimplyMiles inspection
    # Container: .offers-container .inner-container
    # Cards are in rows within columns

    try:
        # Wait for offers container to load
        await page.wait_for_selector('.offers-container', timeout=10000)
    except PlaywrightTimeout:
        logger.warning("Offers container not found")
        return offers

    # Get all offer cards using verified selector structure
    # Each row contains columns with cards
    rows = await page.query_selector_all('.offers-container .inner-container .row')

    for row in rows:
        # Find card columns within each row
        cols = await row.query_selector_all('[class*="col"]')

        for col in cols:
            card = await col.query_selector('.card')
            if not card:
                continue

            try:
                # Merchant name: .card-title
                merchant_el = await card.query_selector('.card-title')
                merchant_name = await merchant_el.text_content() if merchant_el else None

                if not merchant_name:
                    continue

                merchant_name = merchant_name.strip()

                # Offer text: .card-body .font-bold
                offer_el = await card.query_selector('.card-body .font-bold')
                offer_text = await offer_el.text_content() if offer_el else ""
                offer_text = offer_text.strip() if offer_text else ""

                # Skip if no offer text or it's just a button
                if not offer_text or offer_text == "Activate offer":
                    continue

                # Expiring badge: .info-badge
                badge_el = await card.query_selector('.info-badge')
                badge_text = await badge_el.text_content() if badge_el else ""
                expiring_soon = 'expiring' in badge_text.lower() if badge_text else False

                # Expiration date: .card-footer p.txt-grey
                expiry_el = await card.query_selector('.card-footer p.txt-grey')
                expiry_text = await expiry_el.text_content() if expiry_el else ""
                expires_at = parse_expiration(expiry_text) if expiry_text else None

                # Parse offer details from text
                offer_data = parse_offer_text(offer_text)

                offer = {
                    'merchant_name': merchant_name,
                    'merchant_name_normalized': normalize_merchant(merchant_name),
                    'offer_type': offer_data['offer_type'],
                    'miles_amount': offer_data['miles_amount'],
                    'lp_amount': offer_data['lp_amount'],
                    'min_spend': offer_data['min_spend'],
                    'expires_at': expires_at,
                    'expiring_soon': expiring_soon,
                    'raw_text': offer_text[:500]
                }

                # Only add if we extracted meaningful data
                if offer['miles_amount'] > 0:
                    offers.append(offer)

            except Exception as e:
                logger.warning(f"Error parsing offer card: {e}")
                continue

    return offers


async def scrape_all_pages(page: Page) -> List[Dict[str, Any]]:
    """
    Scrape offers from all pagination pages.

    Args:
        page: Playwright page

    Returns:
        List of all offers from all pages
    """
    all_offers = []
    page_num = 1
    max_pages = 20  # Safety limit

    while page_num <= max_pages:
        logger.info(f"Scraping page {page_num}...")

        # Scrape current page
        page_offers = await scrape_offers_from_page(page)
        all_offers.extend(page_offers)

        logger.info(f"Page {page_num}: Found {len(page_offers)} offers")

        # Check for next page button
        try:
            # Find pagination and next page link
            pagination = await page.query_selector('.pagination')
            if not pagination:
                logger.info("No pagination found - single page")
                break

            # Find the next page link (page number = current + 1)
            next_page_num = page_num + 1
            next_link = await pagination.query_selector(f'.page-item:not(.active) .page-link:has-text("{next_page_num}")')

            if not next_link:
                # Try the "next" arrow button
                next_link = await pagination.query_selector('.page-item:last-child .page-link')
                if next_link:
                    # Check if it's disabled
                    parent = await next_link.evaluate('el => el.closest(".page-item").className')
                    if 'disabled' in parent:
                        next_link = None

            if not next_link:
                logger.info(f"No more pages after page {page_num}")
                break

            # Click next page
            await next_link.click()
            await random_delay(1.5, 3.0)

            # Wait for new content to load
            await page.wait_for_load_state('networkidle', timeout=15000)

            page_num += 1

        except Exception as e:
            logger.warning(f"Error navigating to next page: {e}")
            break

    return all_offers


async def scrape_offers(page: Page) -> List[Dict[str, Any]]:
    """
    Main function to scrape all offers (handles pagination).

    Args:
        page: Playwright page

    Returns:
        List of offer dictionaries
    """
    return await scrape_all_pages(page)


async def run_scraper(test_mode: bool = False) -> Dict[str, Any]:
    """
    Main scraper function.

    Args:
        test_mode: If True, don't write to database

    Returns:
        Dict with status and statistics
    """
    settings = get_settings()
    result = {
        'status': 'unknown',
        'offers_scraped': 0,
        'errors': [],
        'timestamp': datetime.now().isoformat()
    }

    async with async_playwright() as p:
        try:
            # Launch browser with persistent context
            logger.info(f"Launching browser with profile from {settings.browser_data_path}")

            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(settings.browser_data_path),
                headless=False,  # Must be headed - site detects headless
                viewport={"width": 1280, "height": 800},
                user_agent=settings.scraper.user_agent,
                args=[
                    "--disable-blink-features=AutomationControlled",
                ]
            )

            page = await context.new_page()

            # Navigate to offers page
            logger.info(f"Navigating to {OFFERS_URL}")
            await page.goto(OFFERS_URL, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)  # Give JS time to load offers

            await random_delay()

            # Check login status
            logged_in = await is_logged_in(page)

            if not logged_in:
                logger.error("Not logged in! Please run setup_auth.py first.")
                result['status'] = 'auth_required'
                result['errors'].append("Session expired - re-authentication required")

                # Send re-auth notification
                try:
                    from alerts.sender import send_reauth_notification
                    await send_reauth_notification()
                except Exception as e:
                    logger.warning(f"Could not send re-auth notification: {e}")

                await context.close()
                return result

            logger.info("Login confirmed. Scraping offers...")

            # Scroll to load all offers
            await scroll_to_load_all(page)

            # Scrape offers
            offers = await scrape_offers(page)

            logger.info(f"Scraped {len(offers)} offers")
            result['offers_scraped'] = len(offers)

            # Store in database (unless test mode)
            if not test_mode and offers:
                db = get_database()
                scraped_at = datetime.now().isoformat()

                # Clear old offers and insert new
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
                    except Exception as e:
                        logger.warning(f"Error inserting offer: {e}")
                        result['errors'].append(str(e))

                # Record successful scrape
                db.record_scraper_run(
                    scraper_name="simplymiles",
                    status="success",
                    items_scraped=len(offers)
                )

                logger.info(f"Stored {len(offers)} offers in database")

            elif test_mode:
                logger.info("Test mode - not writing to database")
                # Print sample offers
                for offer in offers[:5]:
                    logger.info(f"  - {offer['merchant_name']}: {offer['miles_amount']} miles ({offer['offer_type']})")

            result['status'] = 'success'
            await context.close()

        except PlaywrightTimeout as e:
            logger.error(f"Timeout error: {e}")
            result['status'] = 'timeout'
            result['errors'].append(str(e))

            # Record failure
            if not test_mode:
                db = get_database()
                db.record_scraper_run(
                    scraper_name="simplymiles",
                    status="failure",
                    error_message=str(e)
                )

        except Exception as e:
            logger.error(f"Scraper error: {e}")
            result['status'] = 'error'
            result['errors'].append(str(e))

            # Record failure
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
    parser = argparse.ArgumentParser(description="SimplyMiles Scraper")
    parser.add_argument("--test", action="store_true", help="Test mode (no DB writes)")
    args = parser.parse_args()

    logger.info("Starting SimplyMiles scraper...")

    result = asyncio.run(run_scraper(test_mode=args.test))

    logger.info(f"Scraper finished: {result['status']}")
    logger.info(f"Offers scraped: {result['offers_scraped']}")

    if result['errors']:
        logger.warning(f"Errors: {result['errors']}")

    # Exit with error code if failed
    if result['status'] not in ['success']:
        sys.exit(1)


if __name__ == "__main__":
    main()

