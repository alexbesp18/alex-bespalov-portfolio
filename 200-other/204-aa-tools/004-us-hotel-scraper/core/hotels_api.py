"""
AAdvantage Hotels API wrapper.

Provides async methods for interacting with the hotels API.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx

from .http_client import fetch_with_client, random_delay

logger = logging.getLogger(__name__)

HOTELS_BASE_URL = "https://www.aadvantagehotels.com"


def format_date(date: datetime) -> str:
    """Format date as MM/DD/YYYY for API."""
    return f"{date.month:02}/{date.day:02}/{date.year}"


async def lookup_place_id(
    client: httpx.AsyncClient,
    city_name: str,
    state: str,
) -> Optional[str]:
    """
    Look up Agoda place ID for a city.

    Args:
        client: HTTP client
        city_name: City name
        state: State abbreviation

    Returns:
        Agoda place ID (e.g., "AGODA_CITY|4542") or None
    """
    query = f"{city_name} ({state}), United States"
    url = f"{HOTELS_BASE_URL}/rest/aadvantage-hotels/places"

    try:
        data = await fetch_with_client(
            client,
            url,
            params={"query": query},
            max_retries=2,
        )

        if not data:
            # Try without state
            data = await fetch_with_client(
                client,
                url,
                params={"query": f"{city_name}, United States"},
                max_retries=2,
            )

        if data and isinstance(data, list) and len(data) > 0:
            # Find the best match (prefer CITY type)
            for place in data:
                if place.get('type') == 'CITY':
                    return place.get('id')

            # Fallback to first result
            return data[0].get('id')

        return None

    except Exception as e:
        logger.debug(f"Place lookup failed for {city_name}, {state}: {e}")
        return None


async def create_search_request(
    client: httpx.AsyncClient,
    place_id: str,
    city_query: str,
    check_in: datetime,
    check_out: datetime,
    adults: int = 2,
) -> Optional[str]:
    """
    Create a search request and get the search UUID.

    Args:
        client: HTTP client
        place_id: Agoda place ID
        city_query: City search query string
        check_in: Check-in date
        check_out: Check-out date

    Returns:
        Search UUID or None if failed
    """
    check_in_str = quote(format_date(check_in), safe='')
    check_out_str = quote(format_date(check_out), safe='')
    place_id_encoded = quote(place_id, safe='') if place_id else ''
    query_encoded = quote(city_query, safe='')

    url = (
        f"{HOTELS_BASE_URL}/rest/aadvantage-hotels/searchRequest?"
        f"adults={adults}&checkIn={check_in_str}&checkOut={check_out_str}&children=0"
        f"&currency=USD&language=en&locationType=CITY&mode=earn&numberOfChildren=0"
        f"&placeId={place_id_encoded}&program=aadvantage&promotion&query={query_encoded}"
        f"&rooms=1&source=AGODA"
    )

    try:
        data = await fetch_with_client(client, url, max_retries=3)
        if data:
            return data.get('uuid')
        return None
    except Exception as e:
        logger.debug(f"Search request failed: {e}")
        return None


async def get_search_results(
    client: httpx.AsyncClient,
    search_uuid: str,
    page_size: int = 45,
) -> Optional[Dict[str, Any]]:
    """
    Get search results using the search UUID.

    Args:
        client: HTTP client
        search_uuid: UUID from create_search_request
        page_size: Number of results per page

    Returns:
        Results dict or None if failed
    """
    url = (
        f"{HOTELS_BASE_URL}/rest/aadvantage-hotels/search/{search_uuid}"
        f"?pageSize={page_size}&pageNumber=1"
    )

    try:
        return await fetch_with_client(client, url, max_retries=3)
    except Exception as e:
        logger.debug(f"Search results failed: {e}")
        return None


def parse_hotel_result(
    hotel_data: Dict[str, Any],
    city_name: str,
    state: str,
    check_in: datetime,
    check_out: datetime,
) -> Optional[Dict[str, Any]]:
    """
    Parse a hotel result from the API response.

    Args:
        hotel_data: Raw hotel data from API
        city_name: City name
        state: State abbreviation
        check_in: Check-in date
        check_out: Check-out date

    Returns:
        Processed hotel dict or None if invalid
    """
    try:
        hotel = hotel_data.get('hotel', {})

        hotel_name = hotel.get('name', '')
        if not hotel_name:
            return None

        # Get pricing
        total_price = hotel_data.get('grandTotalPublishedPriceInclusiveWithFees', {})
        total_cost = float(total_price.get('amount', 0))

        if total_cost <= 0:
            # Try alternate price field
            alt_price = hotel_data.get('totalPriceUSD', {})
            total_cost = float(alt_price.get('amount', 0))

        if total_cost <= 0:
            return None

        # Get miles
        base_miles = int(hotel_data.get('rewards', 0))
        bonus_miles = int(hotel_data.get('roomTypeResultTeaser', {}).get('rewards', 0))
        total_miles = max(base_miles, bonus_miles)

        if total_miles <= 0:
            return None

        # Calculate metrics
        nights = (check_out - check_in).days
        nightly_rate = total_cost / nights if nights > 0 else total_cost
        yield_ratio = total_miles / total_cost if total_cost > 0 else 0

        # Build hotel URL
        hotel_id = hotel.get('id', '')
        url = f"{HOTELS_BASE_URL}/hotel/{hotel_id}" if hotel_id else None

        return {
            'hotel_name': hotel_name,
            'city_name': city_name,
            'state': state,
            'neighborhood': hotel.get('neighborhoodName', ''),
            'stars': hotel.get('stars', 0),
            'rating': hotel.get('rating', 0),
            'review_count': hotel.get('numberOfReviews', 0),
            'check_in': check_in.isoformat(),
            'check_out': check_out.isoformat(),
            'nights': nights,
            'nightly_rate': nightly_rate,
            'base_miles': base_miles,
            'bonus_miles': bonus_miles,
            'total_miles': total_miles,
            'total_cost': total_cost,
            'yield_ratio': yield_ratio,
            'url': url,
            'agoda_hotel_id': hotel_id,
        }

    except (ValueError, TypeError, KeyError) as e:
        logger.debug(f"Error parsing hotel: {e}")
        return None


async def search_hotels(
    client: httpx.AsyncClient,
    place_id: str,
    city_name: str,
    state: str,
    check_in: datetime,
    check_out: datetime,
    adults: int = 2,
) -> List[Dict[str, Any]]:
    """
    Search for hotels in a city for given dates.

    Args:
        client: HTTP client
        place_id: Agoda place ID
        city_name: City name
        state: State abbreviation
        check_in: Check-in date
        check_out: Check-out date

    Returns:
        List of hotel deal dictionaries
    """
    hotels = []
    city_query = f"{city_name} ({state}), United States"

    # Step 1: Create search request to get UUID
    search_uuid = await create_search_request(
        client, place_id, city_query, check_in, check_out, adults
    )
    if not search_uuid:
        logger.warning(f"Could not create search for {city_name}, {state}")
        return hotels

    await random_delay(0.1, 0.3)

    # Step 2: Get search results
    results = await get_search_results(client, search_uuid)
    if not results:
        logger.warning(f"Could not get results for {city_name}, {state}")
        return hotels

    # Step 3: Parse results
    for hotel_data in results.get('results', []):
        parsed = parse_hotel_result(hotel_data, city_name, state, check_in, check_out)
        if parsed:
            hotels.append(parsed)

    logger.debug(f"Found {len(hotels)} hotels for {city_name} on {check_in.date()}")
    return hotels
