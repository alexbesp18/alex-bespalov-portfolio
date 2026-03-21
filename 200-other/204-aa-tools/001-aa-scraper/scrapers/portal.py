#!/usr/bin/env python3
"""
AAdvantage eShopping Portal Scraper for AA Points Monitor.

Scrapes merchant rates from the public eShopping portal.
Primary method: Cartera API (discovered 2024-12-28) - fast and reliable.
Fallback: Playwright HTML scraping if API fails.

Usage:
    python scrapers/portal.py         # Full scrape
    python scrapers/portal.py --test  # Test run (no DB writes)
    python scrapers/portal.py --api   # Force API only (no fallback)
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

import httpx

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeout

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

PORTAL_BASE_URL = "https://www.aadvantageeshopping.com"
STORES_URL = f"{PORTAL_BASE_URL}/b____.htm"  # All stores page

# Cartera API (discovered 2024-12-28 via network inspection)
CARTERA_API_URL = "https://api.cartera.com/content/v4/merchants/all"
CARTERA_PARAMS = {
    'brand_id': '251',  # AAdvantage eShopping
    'app_key': '9ec260e91abc101aaec68280da6a5487',
    'app_id': '672b9fbb',
    'limit': '2000',  # Get all merchants
    'sort_by': 'name',
    'fields': 'name,type,id,showRebate,rebate,clickUrl,offers',
}


async def random_delay(min_sec: float = 1.0, max_sec: float = 3.0):
    """Add random delay for rate limiting."""
    delay = random.uniform(min_sec, max_sec)
    await asyncio.sleep(delay)


async def scrape_via_cartera_api() -> List[Dict[str, Any]]:
    """
    Scrape merchant data via the Cartera API.

    This is the primary scraping method - fast and reliable.
    Discovered 2024-12-28 via network traffic inspection.

    Returns:
        List of merchant dictionaries
    """
    stores = []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(CARTERA_API_URL, params=CARTERA_PARAMS)

            if response.status_code != 200:
                logger.warning(f"Cartera API returned status {response.status_code}")
                return stores

            data = response.json()
            merchants = data.get('response', [])
            total = data.get('metadata', {}).get('total', len(merchants))

            logger.info(f"Cartera API returned {len(merchants)} merchants (total: {total})")

            for merchant in merchants:
                try:
                    name = merchant.get('name', '')
                    if not name or not merchant.get('showRebate', True):
                        continue

                    rebate = merchant.get('rebate', {})
                    miles_value = rebate.get('value', 0)
                    currency = rebate.get('currency', '')

                    # Only include per-dollar rates (miles/$)
                    # Skip flat bonus offers for now
                    if 'miles/$' not in currency and 'mile/$' not in currency:
                        # Flat bonus (e.g., "600 miles") - still include but note it
                        if miles_value > 100:  # Likely flat bonus, not per-dollar
                            continue

                    is_elevated = rebate.get('isElevation', False)
                    is_extra = rebate.get('isExtraRewards', False)

                    # Build click URL
                    click_url = merchant.get('clickUrl', '')
                    if click_url and not click_url.startswith('http'):
                        click_url = PORTAL_BASE_URL + click_url

                    store = {
                        'merchant_name': name,
                        'merchant_name_normalized': normalize_merchant(name),
                        'miles_per_dollar': float(miles_value) if miles_value else 1.0,
                        'is_bonus_rate': is_elevated or is_extra,
                        'category': None,  # Not provided in this API response
                        'url': click_url if click_url else None
                    }

                    stores.append(store)

                except Exception as e:
                    logger.debug(f"Error parsing merchant: {e}")
                    continue

    except httpx.TimeoutException:
        logger.warning("Cartera API timeout")
    except Exception as e:
        logger.warning(f"Cartera API error: {e}")

    return stores


def parse_miles_rate(text: str) -> Optional[float]:
    """
    Parse miles per dollar rate from text.

    Handles actual eShopping portal formats:
    - "Earn 2 miles/$"
    - "Earn 0.5 mile/$"
    - "Now 4 miles/$" (elevated rate)
    - "Up to 4,900 miles" (flat bonus)
    - "Earn 600 miles" (flat bonus)

    Args:
        text: Text containing rate info

    Returns:
        Miles per dollar as float, or None
    """
    if not text:
        return None

    text = text.lower().strip()

    # Remove commas from numbers (e.g., "4,900")
    text = text.replace(',', '')

    # Pattern: "X miles/$" or "X mile/$" (per-dollar rate)
    match = re.search(r'(\d+(?:\.\d+)?)\s*miles?/\$', text)
    if match:
        return float(match.group(1))

    # Pattern: "Earn X miles/$" or "Now X miles/$"
    match = re.search(r'(?:earn|now|was)\s*(\d+(?:\.\d+)?)\s*miles?/\$', text)
    if match:
        return float(match.group(1))

    # Pattern: "X mi/$"
    match = re.search(r'(\d+(?:\.\d+)?)\s*mi/\$', text)
    if match:
        return float(match.group(1))

    # Pattern: flat bonus "X miles" (not per dollar) - return None for these
    # as they need different handling
    if re.search(r'(\d+)\s*miles?(?!\s*/)', text) and '/$' not in text:
        # This is a flat bonus, not a per-dollar rate
        # Return the value but mark somehow? For now return the number
        match = re.search(r'(\d+(?:\.\d+)?)\s*miles?', text)
        if match:
            return float(match.group(1))

    # Pattern: "Xpt/$" or "X point/$"
    match = re.search(r'(\d+(?:\.\d+)?)\s*(?:pt|points?)(?:\s*/\s*\$)?', text)
    if match:
        return float(match.group(1))

    # Pattern: "X per dollar"
    match = re.search(r'(\d+(?:\.\d+)?)\s*per\s*dollar', text)
    if match:
        return float(match.group(1))

    # Pattern: just a number followed by X (like "5X")
    match = re.search(r'(\d+(?:\.\d+)?)\s*x', text)
    if match:
        return float(match.group(1))

    return None


def is_bonus_rate(text: str) -> bool:
    """
    Check if the rate appears to be a bonus/elevated rate.

    Args:
        text: Text from rate element

    Returns:
        True if bonus rate detected
    """
    if not text:
        return False

    text = text.lower()
    bonus_indicators = ['bonus', 'elevated', 'special', 'limited time', 'up to', 'double', 'triple']

    return any(indicator in text for indicator in bonus_indicators)


def parse_store_card(element) -> Optional[Dict[str, Any]]:
    """
    Parse a store card element.

    Args:
        element: BeautifulSoup element for a store card

    Returns:
        Dict with store data or None
    """
    try:
        # Try to find merchant name
        name_el = element.select_one('h2, h3, h4, .store-name, .merchant-name, [class*="name"], .title')
        merchant_name = name_el.get_text(strip=True) if name_el else None

        if not merchant_name:
            # Try getting from link text or alt text
            link = element.select_one('a')
            if link:
                merchant_name = link.get_text(strip=True) or link.get('title', '')

            img = element.select_one('img')
            if not merchant_name and img:
                merchant_name = img.get('alt', '')

        if not merchant_name:
            return None

        # Get rate info
        rate_el = element.select_one('.rate, .miles, .earning, [class*="rate"], [class*="miles"], [class*="earn"]')
        rate_text = rate_el.get_text(strip=True) if rate_el else element.get_text(strip=True)

        miles_rate = parse_miles_rate(rate_text)

        if miles_rate is None:
            # Default to 1 if we can't parse
            miles_rate = 1.0

        # Check for bonus indicator
        bonus = is_bonus_rate(element.get_text())

        # Get category
        category_el = element.select_one('.category, [class*="category"]')
        category = category_el.get_text(strip=True) if category_el else None

        # Get store URL
        link = element.select_one('a[href*="/s__"]')
        url = link.get('href', '') if link else None
        if url and not url.startswith('http'):
            url = PORTAL_BASE_URL + url

        return {
            'merchant_name': merchant_name,
            'merchant_name_normalized': normalize_merchant(merchant_name),
            'miles_per_dollar': miles_rate,
            'is_bonus_rate': bonus,
            'category': category,
            'url': url
        }

    except Exception as e:
        logger.warning(f"Error parsing store card: {e}")
        return None


async def scrape_stores_page(html: str) -> List[Dict[str, Any]]:
    """
    Parse stores from HTML page.

    Uses verified selectors from discovery phase (2024-12-28).
    The eShopping portal uses 'mn_' prefixed classes.

    Args:
        html: Page HTML

    Returns:
        List of store dictionaries
    """
    stores = []
    soup = BeautifulSoup(html, 'lxml')

    # Verified selectors from eShopping portal inspection
    # The portal uses mn_ (merchant network) prefixed classes

    # Method 1: Find all rebate elements with merchant info
    rebate_elements = soup.select('.mn_rebateV4')
    logger.info(f"Found {len(rebate_elements)} rebate elements")

    for rebate in rebate_elements:
        try:
            # Navigate up to find the merchant container
            parent = rebate.find_parent(['li', 'div', 'td'])
            if not parent:
                continue

            # Find merchant name link
            name_link = parent.select_one('a')
            if not name_link:
                continue

            merchant_name = name_link.get_text(strip=True)
            if not merchant_name or len(merchant_name) < 2:
                continue

            # Get rate values
            old_value = rebate.select_one('.mn_elevationOldValue')
            new_value = rebate.select_one('.mn_elevationNewValue')

            # Prefer new value (current rate), fall back to old
            rate_text = ''
            is_elevated = False

            if new_value:
                rate_text = new_value.get_text(strip=True)
            if old_value:
                is_elevated = True
                if not rate_text:
                    rate_text = old_value.get_text(strip=True)

            # Parse the rate
            miles_rate = parse_miles_rate(rate_text)

            # Check for tiered rates
            tiered = rebate.select_one('.mn_rebateTiered, .mn_tieredPrefix')
            if tiered:
                is_elevated = True  # Tiered rates are typically promotional

            # Get store URL
            url = name_link.get('href', '')
            if url and not url.startswith('http'):
                url = PORTAL_BASE_URL + url

            store = {
                'merchant_name': merchant_name,
                'merchant_name_normalized': normalize_merchant(merchant_name),
                'miles_per_dollar': miles_rate if miles_rate else 1.0,
                'is_bonus_rate': is_elevated,
                'category': None,  # Category not easily available in list view
                'url': url if url else None
            }

            stores.append(store)

        except Exception as e:
            logger.warning(f"Error parsing rebate element: {e}")
            continue

    # If no rebate elements found, try fallback selectors
    if not stores:
        logger.warning("No stores found with mn_ selectors. Trying fallback...")

        # Fallback: look for store links
        store_links = soup.select('a[href*="/s__"]')
        logger.info(f"Found {len(store_links)} store links")

        for link in store_links:
            parent = link.parent
            if parent:
                store_data = parse_store_card(parent)
                if store_data:
                    stores.append(store_data)

    # Remove duplicates by merchant name
    seen = set()
    unique_stores = []
    for store in stores:
        if store['merchant_name_normalized'] not in seen:
            seen.add(store['merchant_name_normalized'])
            unique_stores.append(store)

    logger.info(f"Parsed {len(unique_stores)} unique stores")
    return unique_stores


async def scrape_with_playwright(page: Page) -> List[Dict[str, Any]]:
    """
    Scrape stores using Playwright to render JavaScript content.

    Args:
        page: Playwright page

    Returns:
        List of all stores
    """
    stores = []

    try:
        logger.info(f"Navigating to {STORES_URL}")
        await page.goto(STORES_URL, wait_until='networkidle', timeout=60000)

        # Wait for store elements to load
        try:
            await page.wait_for_selector('.mn_rebateV4', timeout=15000)
        except PlaywrightTimeout:
            logger.warning("Timeout waiting for mn_rebateV4 elements")

        # Additional wait for JavaScript to finish rendering
        await asyncio.sleep(2)

        # Get the rendered HTML
        html = await page.content()

        # Parse with BeautifulSoup
        stores = await scrape_stores_page(html)

        logger.info(f"Scraped {len(stores)} stores from page")

    except PlaywrightTimeout as e:
        logger.error(f"Playwright timeout: {e}")
    except Exception as e:
        logger.error(f"Error scraping with Playwright: {e}")

    return stores


async def run_scraper(test_mode: bool = False, api_only: bool = False) -> Dict[str, Any]:
    """
    Main scraper function.

    Primary method: Cartera API (fast, reliable)
    Fallback: Playwright HTML scraping

    Args:
        test_mode: If True, don't write to database
        api_only: If True, don't fall back to Playwright

    Returns:
        Dict with status and statistics
    """
    settings = get_settings()
    result = {
        'status': 'unknown',
        'stores_scraped': 0,
        'method': 'unknown',
        'errors': [],
        'timestamp': datetime.now().isoformat()
    }

    stores = []

    # Try Cartera API first (primary method)
    logger.info("Attempting Cartera API scrape...")
    stores = await scrape_via_cartera_api()

    if stores:
        result['method'] = 'cartera_api'
        logger.info(f"Cartera API returned {len(stores)} stores")
    elif not api_only:
        # Fallback to Playwright
        logger.info("Cartera API failed, falling back to Playwright...")
        result['method'] = 'playwright_fallback'

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent=settings.scraper.user_agent
            )
            page = await context.new_page()

            try:
                stores = await scrape_with_playwright(page)
            finally:
                await context.close()
                await browser.close()
    else:
        logger.warning("Cartera API failed and api_only=True, no fallback")
        result['errors'].append("Cartera API failed and fallback disabled")

    result['stores_scraped'] = len(stores)
    logger.info(f"Total stores scraped: {len(stores)} via {result['method']}")

    if not stores:
        logger.warning("No stores scraped!")
        result['status'] = 'no_data'
        result['errors'].append("No stores found")
        return result

    # Store in database (unless test mode)
    if not test_mode:
        db = get_database()
        scraped_at = datetime.now().isoformat()

        # Clear old rates and insert new
        db.clear_portal_rates()

        for store in stores:
            try:
                db.insert_portal_rate(
                    merchant_name=store['merchant_name'],
                    merchant_name_normalized=store['merchant_name_normalized'],
                    miles_per_dollar=store['miles_per_dollar'],
                    is_bonus_rate=store['is_bonus_rate'],
                    category=store.get('category'),
                    url=store.get('url'),
                    scraped_at=scraped_at
                )

                # Record discovery for "New This Week" tracking
                # Portal yield = miles_per_dollar + 1 (CC bonus)
                total_yield = store['miles_per_dollar'] + 1
                db.upsert_discovery(
                    deal_type='portal',
                    deal_identifier=store['merchant_name_normalized'],
                    yield_value=total_yield
                )
            except Exception as e:
                logger.warning(f"Error inserting store: {e}")
                result['errors'].append(str(e))

        # Record successful scrape
        db.record_scraper_run(
            scraper_name="portal",
            status="success",
            items_scraped=len(stores)
        )

        logger.info(f"Stored {len(stores)} stores in database")

    else:
        logger.info("Test mode - not writing to database")
        # Print sample stores
        logger.info("\nTop 15 stores by rate:")
        sorted_stores = sorted(stores, key=lambda x: x['miles_per_dollar'], reverse=True)
        for store in sorted_stores[:15]:
            bonus = "(BONUS)" if store['is_bonus_rate'] else ""
            logger.info(f"  - {store['merchant_name']}: {store['miles_per_dollar']} mi/$ {bonus}")

    result['status'] = 'success'
    return result


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(description="eShopping Portal Scraper")
    parser.add_argument("--test", action="store_true", help="Test mode (no DB writes)")
    parser.add_argument("--api", action="store_true", help="API only (no Playwright fallback)")
    args = parser.parse_args()

    logger.info("Starting Portal scraper...")

    result = asyncio.run(run_scraper(test_mode=args.test, api_only=args.api))

    logger.info(f"Scraper finished: {result['status']}")
    logger.info(f"Stores scraped: {result['stores_scraped']}")
    logger.info(f"Method used: {result.get('method', 'unknown')}")

    if result['errors']:
        logger.warning(f"Errors: {result['errors']}")

    # Exit with error code if failed
    if result['status'] not in ['success']:
        sys.exit(1)


if __name__ == "__main__":
    main()

