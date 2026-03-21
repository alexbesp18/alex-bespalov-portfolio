#!/usr/bin/env python3
"""
AAdvantage Hotels Scraper for AA Points Monitor.

Scrapes hotel deals from aadvantagehotels.com for priority cities.
Searches 90 days ahead with weekend-heavy sampling.

Uses REST API (discovered from older scripts) - no browser needed.

Usage:
    python scrapers/hotels.py         # Full scrape
    python scrapers/hotels.py --test  # Test run (no DB writes)
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings
from config.cities import PRIORITY_CITIES, get_search_dates, City
from core.database import get_database
from core.scorer import calculate_deal_score
from core.hotels_api import (
    HEADERS,
    HOTELS_BASE_URL,
    random_delay,
    create_search_request,
    get_search_results,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# Suppress httpx verbose logging (logs every HTTP request at INFO level)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def parse_hotel_result(
    hotel_data: Dict,
    city: City,
    check_in: datetime,
    check_out: datetime
) -> Optional[Dict[str, Any]]:
    """
    Parse a hotel result from the API response.

    Args:
        hotel_data: Raw hotel data from API
        city: City being searched
        check_in: Check-in date
        check_out: Check-out date

    Returns:
        Processed hotel dict or None
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
        total_miles = max(base_miles, bonus_miles)  # Premium miles is the higher tier

        if total_miles <= 0:
            return None

        # Calculate metrics
        nights = (check_out - check_in).days
        nightly_rate = total_cost / nights if nights > 0 else total_cost
        yield_ratio = total_miles / total_cost if total_cost > 0 else 0

        deal_score = calculate_deal_score(
            base_yield=yield_ratio,
            min_spend=total_cost,
            is_austin=city.is_local
        )

        # Build hotel URL
        hotel_id = hotel.get('id', '')
        url = f"{HOTELS_BASE_URL}/hotel/{hotel_id}" if hotel_id else None

        return {
            'hotel_name': hotel_name,
            'city': city.name,
            'state': city.state,
            'neighborhood': hotel.get('neighborhoodName', ''),
            'stars': hotel.get('stars', 0),
            'rating': hotel.get('rating', 0),
            'review_count': hotel.get('numberOfReviews', 0),
            'check_in': check_in.isoformat(),
            'check_out': check_out.isoformat(),
            'nightly_rate': nightly_rate,
            'base_miles': base_miles,
            'bonus_miles': bonus_miles,
            'total_miles': total_miles,
            'total_cost': total_cost,
            'yield_ratio': yield_ratio,
            'deal_score': deal_score,
            'url': url
        }

    except (ValueError, TypeError, KeyError) as e:
        logger.debug(f"Error parsing hotel: {e}")
        return None


def search_hotels(
    client: httpx.Client,
    city: City,
    check_in: datetime,
    check_out: datetime
) -> List[Dict[str, Any]]:
    """
    Search for hotels in a city for given dates.

    Args:
        client: httpx client
        city: City object
        check_in: Check-in date
        check_out: Check-out date

    Returns:
        List of hotel deal dictionaries
    """
    hotels = []

    # Step 1: Create search request to get UUID
    search_uuid = create_search_request(client, city, check_in, check_out)
    if not search_uuid:
        logger.warning(f"Could not create search for {city.name}")
        return hotels

    random_delay(0.1, 0.3)

    # Step 2: Get search results
    results = get_search_results(client, search_uuid)
    if not results:
        logger.warning(f"Could not get results for {city.name}")
        return hotels

    # Step 3: Parse results
    for hotel_data in results.get('results', []):
        parsed = parse_hotel_result(hotel_data, city, check_in, check_out)
        if parsed:
            hotels.append(parsed)

    logger.debug(f"Found {len(hotels)} hotels for {city.name} on {check_in.date()}")
    return hotels


def get_adaptive_dates(
    city: City,
    default_dates: List[tuple],
    max_dates: int = 10,
    use_matrix: bool = True
) -> List[tuple]:
    """
    Select dates adaptively based on yield matrix data.

    Uses the comprehensive yield matrix (1,176 combinations from discovery)
    to prioritize high-yield (day_of_week, advance_days) combinations.
    Falls back to default dates if no matrix data available.

    Args:
        city: City to search
        default_dates: Default date list from get_search_dates()
        max_dates: Maximum number of dates to return
        use_matrix: Whether to use yield matrix (True) or historical data (False)

    Returns:
        List of (check_in, check_out) tuples, prioritized by predicted yield
    """
    db = get_database()
    today = datetime.now()

    if use_matrix:
        # Get best slots from the yield matrix (uses discovery data)
        priority_slots = db.get_priority_search_dates(city.name, duration=1, limit=max_dates * 2)

        if priority_slots:
            # Map priority slots to actual dates from default_dates
            scored_dates = []

            for check_in, check_out in default_dates:
                day_of_week = check_in.weekday()
                advance_days = (check_in - today).days
                duration = (check_out - check_in).days

                # Get prediction from matrix
                prediction = db.get_matrix_yield_prediction(
                    city.name, day_of_week, duration, advance_days
                )

                if prediction:
                    # Weight by both yield and stability
                    stability = prediction.get('yield_stability') or 0.8
                    score = prediction['avg_yield'] * (0.5 + 0.5 * stability)
                else:
                    # Unknown combo - use neutral score
                    score = 10.0

                scored_dates.append((score, check_in, check_out))

            # Sort by score (highest first) and take top dates
            scored_dates.sort(key=lambda x: x[0], reverse=True)
            adaptive_dates = [(check_in, check_out) for _, check_in, check_out in scored_dates[:max_dates]]

            logger.debug(f"Adaptive dates for {city.name}: prioritized by yield matrix (top score: {scored_dates[0][0]:.1f})")
            return adaptive_dates

    # Fallback: use legacy yield_history if matrix not available
    best_slots = db.get_best_yield_slots(city.name, limit=20, min_deals=1)

    if not best_slots:
        logger.debug(f"No yield data for {city.name}, using default dates")
        return default_dates[:max_dates]

    # Score each available date by historical yield prediction
    scored_dates = []

    for check_in, check_out in default_dates:
        day_of_week = check_in.weekday()
        advance_days = (check_in - today).days

        # Find matching slot in history
        prediction = None
        for slot in best_slots:
            if slot['day_of_week'] == day_of_week:
                if abs(slot['advance_days'] - advance_days) <= 7:
                    prediction = slot['avg_yield']
                    break

        if prediction is None:
            prediction = db.get_yield_prediction(city.name, day_of_week, advance_days)

        score = prediction if prediction else 10.0
        scored_dates.append((score, check_in, check_out))

    scored_dates.sort(key=lambda x: x[0], reverse=True)
    adaptive_dates = [(check_in, check_out) for _, check_in, check_out in scored_dates[:max_dates]]

    logger.debug(f"Adaptive dates for {city.name}: prioritized by historical yield")
    return adaptive_dates


def record_yield_history(city: City, hotels: List[Dict], check_in: datetime):
    """
    Record yield statistics for this search to build historical patterns.

    Args:
        city: City searched
        hotels: List of hotel results
        check_in: Check-in date searched
    """
    if not hotels:
        return

    db = get_database()
    today = datetime.now()

    day_of_week = check_in.weekday()
    advance_days = (check_in - today).days

    yields = [h['yield_ratio'] for h in hotels if h.get('yield_ratio', 0) > 0]

    if not yields:
        return

    avg_yield = sum(yields) / len(yields)
    max_yield = max(yields)

    db.record_hotel_yield(
        city=city.name,
        day_of_week=day_of_week,
        advance_days=advance_days,
        avg_yield=avg_yield,
        max_yield=max_yield,
        deal_count=len(yields)
    )


def scrape_city(
    client: httpx.Client,
    city: City,
    dates: List[tuple],
    use_adaptive: bool = True
) -> List[Dict[str, Any]]:
    """
    Scrape hotels for a city across multiple date ranges.

    Args:
        client: httpx client
        city: City to search
        dates: List of (check_in, check_out) tuples
        use_adaptive: Whether to use adaptive date selection

    Returns:
        List of hotel deals
    """
    all_hotels = []

    # Use adaptive date selection if enabled
    search_dates = get_adaptive_dates(city, dates) if use_adaptive else dates[:10]

    for check_in, check_out in search_dates:
        random_delay(0.3, 0.8)

        hotels = search_hotels(client, city, check_in, check_out)
        all_hotels.extend(hotels)

        # Record yield history for future adaptive selection
        if hotels:
            record_yield_history(city, hotels, check_in)
            logger.debug(f"Found {len(hotels)} hotels in {city.name} for {check_in.date()}")

    # Deduplicate by hotel name + date
    seen = set()
    unique_hotels = []
    for hotel in all_hotels:
        key = f"{hotel['hotel_name']}_{hotel['check_in']}"
        if key not in seen:
            seen.add(key)
            unique_hotels.append(hotel)

    # Sort by deal score
    unique_hotels.sort(key=lambda x: x['deal_score'], reverse=True)

    return unique_hotels


def run_scraper(test_mode: bool = False) -> Dict[str, Any]:
    """
    Main scraper function using REST API.

    Args:
        test_mode: If True, don't write to database

    Returns:
        Dict with status and statistics
    """
    get_settings()
    result = {
        'status': 'unknown',
        'hotels_scraped': 0,
        'cities_searched': 0,
        'errors': [],
        'timestamp': datetime.now().isoformat()
    }

    # Generate search dates (90 days ahead, weekend-heavy)
    search_dates = get_search_dates(days_ahead=90, weekend_heavy=True)
    logger.info(f"Generated {len(search_dates)} date ranges to search")

    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        all_hotels = []

        for city in PRIORITY_CITIES:
            try:
                logger.info(f"Searching {city.display_name}...")

                hotels = scrape_city(client, city, search_dates)
                all_hotels.extend(hotels)
                result['cities_searched'] += 1

                logger.info(f"Found {len(hotels)} unique deals in {city.name}")

            except Exception as e:
                logger.error(f"Error scraping {city.name}: {e}")
                result['errors'].append(f"{city.name}: {str(e)}")

        # Get top deals overall
        all_hotels.sort(key=lambda x: x['deal_score'], reverse=True)
        top_nationwide = all_hotels[:20]

        result['hotels_scraped'] = len(all_hotels)
        logger.info(f"Total hotels scraped: {len(all_hotels)}")

        # Store in database
        if not test_mode and all_hotels:
            db = get_database()
            scraped_at = datetime.now().isoformat()

            # Clear old deals
            db.clear_hotel_deals()

            stored = 0
            for hotel in all_hotels:
                try:
                    db.insert_hotel_deal(
                        hotel_name=hotel['hotel_name'],
                        city=hotel['city'],
                        state=hotel['state'],
                        check_in=hotel['check_in'],
                        check_out=hotel['check_out'],
                        nightly_rate=hotel['nightly_rate'],
                        base_miles=hotel['base_miles'],
                        bonus_miles=hotel['bonus_miles'],
                        total_miles=hotel['total_miles'],
                        total_cost=hotel['total_cost'],
                        yield_ratio=hotel['yield_ratio'],
                        deal_score=hotel['deal_score'],
                        url=hotel.get('url'),
                        scraped_at=scraped_at
                    )

                    # Update hotel yield baseline for deviation-based alerting
                    check_in_dt = datetime.fromisoformat(hotel['check_in'])
                    db.update_hotel_baseline(
                        hotel_name=hotel['hotel_name'],
                        city=hotel['city'],
                        day_of_week=check_in_dt.weekday(),
                        star_rating=hotel.get('stars', 3),
                        yield_ratio=hotel['yield_ratio']
                    )

                    # Record discovery for "New This Week" tracking
                    deal_identifier = f"{hotel['hotel_name']}_{hotel['city']}"
                    db.upsert_discovery(
                        deal_type='hotel',
                        deal_identifier=deal_identifier,
                        yield_value=hotel['yield_ratio']
                    )

                    stored += 1
                except Exception as e:
                    logger.warning(f"Error inserting hotel: {e}")

            # Record successful scrape
            db.record_scraper_run(
                scraper_name="hotels",
                status="success",
                items_scraped=stored
            )

            logger.info(f"Stored {stored} hotel deals in database")

        elif test_mode:
            logger.info("Test mode - not writing to database")
            logger.info("\nTop 10 Deals Nationwide:")
            for hotel in top_nationwide[:10]:
                logger.info(f"  - {hotel['hotel_name']}, {hotel['city']}: "
                           f"{hotel['yield_ratio']:.1f} mi/$ "
                           f"(${hotel['total_cost']:.0f} -> {hotel['total_miles']:,} miles)")

        result['status'] = 'success'

    return result


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(description="AAdvantage Hotels Scraper")
    parser.add_argument("--test", action="store_true", help="Test mode (no DB writes)")
    args = parser.parse_args()

    logger.info("Starting Hotels scraper...")

    result = run_scraper(test_mode=args.test)

    logger.info(f"Scraper finished: {result['status']}")
    logger.info(f"Hotels scraped: {result['hotels_scraped']}")
    logger.info(f"Cities searched: {result['cities_searched']}")

    if result['errors']:
        logger.warning(f"Errors: {result['errors']}")

    if result['status'] != 'success':
        sys.exit(1)


if __name__ == "__main__":
    main()
