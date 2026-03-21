"""
Shared Hotels API utilities for AA Points Monitor.

Consolidates common hotel API functions used by both:
- scrapers/hotels.py (production scraper)
- scripts/hotel_discovery.py (yield matrix exploration)
"""

import logging
import random
from datetime import datetime
from time import sleep
from typing import Dict, Optional
from urllib.parse import quote

import httpx

from config.cities import City

logger = logging.getLogger(__name__)

HOTELS_BASE_URL = "https://www.aadvantagehotels.com"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
}


def random_delay(min_sec: float = 0.5, max_sec: float = 1.5):
    """Add random delay for rate limiting."""
    delay = random.uniform(min_sec, max_sec)
    sleep(delay)


def format_date(date: datetime) -> str:
    """Format date as MM/DD/YYYY for API."""
    return f"{date.month:02}/{date.day:02}/{date.year}"


def create_search_request(
    client: httpx.Client,
    city: City,
    check_in: datetime,
    check_out: datetime,
    timeout: float = 30.0
) -> Optional[str]:
    """
    Create a search request and get the search UUID.

    Args:
        client: httpx client
        city: City to search
        check_in: Check-in date
        check_out: Check-out date
        timeout: Request timeout in seconds

    Returns:
        Search UUID or None if failed
    """
    check_in_str = quote(format_date(check_in), safe='')
    check_out_str = quote(format_date(check_out), safe='')
    place_id = quote(city.agoda_place_id, safe='') if city.agoda_place_id else ''
    query = quote(city.search_query, safe='')

    url = (
        f"{HOTELS_BASE_URL}/rest/aadvantage-hotels/searchRequest?"
        f"adults=2&checkIn={check_in_str}&checkOut={check_out_str}&children=0"
        f"&currency=USD&language=en&locationType=CITY&mode=earn&numberOfChildren=0"
        f"&placeId={place_id}&program=aadvantage&promotion&query={query}"
        f"&rooms=1&source=AGODA"
    )

    try:
        response = client.get(url, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            return data.get('uuid')
        else:
            logger.debug(f"Search request failed: {response.status_code}")
            return None
    except Exception as e:
        logger.debug(f"Search request error: {e}")
        return None


def get_search_results(
    client: httpx.Client,
    search_uuid: str,
    page_size: int = 45,
    timeout: float = 30.0
) -> Optional[Dict]:
    """
    Get search results using the search UUID.

    Args:
        client: httpx client
        search_uuid: UUID from create_search_request
        page_size: Number of results per page
        timeout: Request timeout in seconds

    Returns:
        Results dict or None if failed
    """
    url = f"{HOTELS_BASE_URL}/rest/aadvantage-hotels/search/{search_uuid}?pageSize={page_size}&pageNumber=1"

    try:
        response = client.get(url, timeout=timeout)
        if response.status_code == 200:
            return response.json()
        else:
            logger.debug(f"Search results failed: {response.status_code}")
            return None
    except Exception as e:
        logger.debug(f"Search results error: {e}")
        return None


def create_client() -> httpx.Client:
    """Create an httpx client with standard hotel API headers."""
    return httpx.Client(headers=HEADERS, follow_redirects=True)
