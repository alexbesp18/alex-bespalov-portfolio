#!/usr/bin/env python3
"""
Hotel Yield Discovery Engine for AA Points Monitor.

Exhaustively explores the hotel yield permutation space:
- 8 cities × 7 days × 3 durations × 7 advance windows = 1,176 combinations

Designed to run for ~1 hour and populate the yield matrix.
Supports resume if interrupted.

Usage:
    python scripts/hotel_discovery.py                    # Full discovery
    python scripts/hotel_discovery.py --resume SESSION   # Resume previous session
    python scripts/hotel_discovery.py --max-time 30      # Limit to 30 minutes
    python scripts/hotel_discovery.py --city Austin      # Single city only
    python scripts/hotel_discovery.py --verify           # Re-verify stale entries
    python scripts/hotel_discovery.py --health           # Show matrix health report
    python scripts/hotel_discovery.py --verify-count 100 # Verify up to 100 entries
"""

import argparse
import logging
import random
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from time import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.cities import PRIORITY_CITIES, City
from core.database import get_database
from core.hotel_scorer import calculate_matrix_stats, find_top_hotels
from core.verification import get_entries_needing_verification, get_matrix_health, format_health_report
from core.hotels_api import (
    HEADERS,
    random_delay,
    create_search_request,
    get_search_results,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# Suppress httpx verbose logging (logs every HTTP request at INFO level)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# ============== Configuration ==============

# Permutation dimensions
DAYS_OF_WEEK = [0, 1, 2, 3, 4, 5, 6]  # Mon-Sun
DURATIONS = [1, 2, 3]  # 1, 2, 3 nights
ADVANCE_DAYS = [7, 14, 21, 30, 45, 60, 90]  # Days ahead


def find_next_date_with_dow(target_dow: int, min_advance: int) -> datetime:
    """
    Find the next date matching the target day of week,
    at least min_advance days from now.

    Args:
        target_dow: 0-6 (Monday-Sunday)
        min_advance: Minimum days from today

    Returns:
        datetime for the target date
    """
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    target_date = today + timedelta(days=min_advance)

    # Find the next matching day of week
    while target_date.weekday() != target_dow:
        target_date += timedelta(days=1)

    return target_date


def generate_all_combinations(
    cities: Optional[List[str]] = None
) -> List[Tuple[str, int, int, int]]:
    """
    Generate all permutation combinations.

    Args:
        cities: Optional list of city names to limit to

    Returns:
        List of (city_name, day_of_week, duration, advance_days) tuples
    """
    combinations = []

    city_list = cities or [c.name for c in PRIORITY_CITIES]

    for city_name in city_list:
        for dow in DAYS_OF_WEEK:
            for duration in DURATIONS:
                for advance in ADVANCE_DAYS:
                    combinations.append((city_name, dow, duration, advance))

    return combinations


def get_city_by_name(name: str) -> Optional[City]:
    """Get City object by name."""
    for city in PRIORITY_CITIES:
        if city.name == name:
            return city
    return None


def parse_hotel_result(
    hotel_data: Dict,
    city: City,
    check_in: datetime,
    check_out: datetime
) -> Optional[Dict[str, Any]]:
    """Parse a hotel result from API response."""
    try:
        hotel = hotel_data.get('hotel', {})
        hotel_name = hotel.get('name', '')

        if not hotel_name:
            return None

        # Get pricing
        total_price = hotel_data.get('grandTotalPublishedPriceInclusiveWithFees', {})
        total_cost = float(total_price.get('amount', 0))

        if total_cost <= 0:
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

        # Get star rating
        stars = int(hotel.get('stars', 0))

        return {
            'hotel_name': hotel_name,
            'city': city.name,
            'state': city.state,
            'stars': stars,
            'check_in': check_in.isoformat(),
            'check_out': check_out.isoformat(),
            'nightly_rate': nightly_rate,
            'total_cost': total_cost,
            'total_miles': total_miles,
            'yield_ratio': yield_ratio,
        }

    except Exception as e:
        logger.debug(f"Parse error: {e}")
        return None


def search_hotels(
    client: httpx.Client,
    city: City,
    check_in: datetime,
    check_out: datetime
) -> List[Dict[str, Any]]:
    """Search for hotels and return parsed results."""
    hotels = []

    search_uuid = create_search_request(client, city, check_in, check_out)
    if not search_uuid:
        return hotels

    random_delay()

    results = get_search_results(client, search_uuid)
    if not results:
        return hotels

    for hotel_data in results.get('results', []):
        parsed = parse_hotel_result(hotel_data, city, check_in, check_out)
        if parsed:
            hotels.append(parsed)

    return hotels


def explore_combination(
    client: httpx.Client,
    city_name: str,
    day_of_week: int,
    duration: int,
    advance_days: int,
    db: Any
) -> Tuple[bool, int, Optional[str]]:
    """
    Explore a single combination and save to matrix.

    Returns:
        Tuple of (success, hotels_found, error_message)
    """
    city = get_city_by_name(city_name)
    if not city:
        return False, 0, f"Unknown city: {city_name}"

    # Calculate check-in/out dates
    check_in = find_next_date_with_dow(day_of_week, advance_days)
    check_out = check_in + timedelta(days=duration)

    try:
        hotels = search_hotels(client, city, check_in, check_out)

        if not hotels:
            # No results - still record as explored
            stats = calculate_matrix_stats([])
            db.upsert_yield_matrix_entry(
                city=city_name,
                day_of_week=day_of_week,
                duration=duration,
                advance_days=advance_days,
                stats=stats,
                top_premium=None,
                top_budget=None
            )
            return True, 0, None

        # Calculate stats
        stats = calculate_matrix_stats(hotels)

        # Find top hotels
        top_premium, top_budget = find_top_hotels(hotels, city_name, city.is_local)

        # Save to matrix
        db.upsert_yield_matrix_entry(
            city=city_name,
            day_of_week=day_of_week,
            duration=duration,
            advance_days=advance_days,
            stats=stats,
            top_premium=top_premium,
            top_budget=top_budget
        )

        return True, len(hotels), None

    except Exception as e:
        return False, 0, str(e)


def run_discovery(
    session_id: str,
    cities: Optional[List[str]] = None,
    max_time_minutes: int = 60,
    shuffle: bool = True,
    specific_combinations: Optional[List[Tuple[str, int, int, int]]] = None
) -> Dict[str, Any]:
    """
    Run the discovery engine.

    Args:
        session_id: Unique session identifier
        cities: Optional list of cities to explore (default: all)
        max_time_minutes: Maximum runtime in minutes
        shuffle: Whether to randomize combination order
        specific_combinations: Optional list of (city, dow, duration, advance) tuples
                               to verify instead of generating all combinations

    Returns:
        Dict with results summary
    """
    db = get_database()
    start_time = time()
    max_seconds = max_time_minutes * 60

    # Get combinations to explore
    if specific_combinations:
        # Verification mode: use provided combinations
        all_combinations = specific_combinations
        total_combinations = len(all_combinations)
        # Don't filter by completed for verification - we want to re-verify
        remaining = list(all_combinations)
        completed = set()
    else:
        # Discovery mode: generate all combinations
        all_combinations = generate_all_combinations(cities)
        total_combinations = len(all_combinations)
        # Get already completed combinations (for resume)
        completed = db.get_completed_combinations(session_id)
        # Filter to remaining
        remaining = [c for c in all_combinations if c not in completed]

    if shuffle:
        random.shuffle(remaining)

    logger.info(f"Discovery session: {session_id}")
    logger.info(f"Total combinations: {total_combinations}")
    logger.info(f"Already completed: {len(completed)}")
    logger.info(f"Remaining: {len(remaining)}")
    logger.info(f"Max runtime: {max_time_minutes} minutes")

    results = {
        'session_id': session_id,
        'total_combinations': total_combinations,
        'completed_before': len(completed),
        'explored_now': 0,
        'hotels_found': 0,
        'errors': 0,
        'elapsed_seconds': 0,
    }

    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        for i, (city_name, dow, duration, advance) in enumerate(remaining):
            # Check time limit
            elapsed = time() - start_time
            if elapsed >= max_seconds:
                logger.info(f"Time limit reached ({max_time_minutes} min)")
                break

            # Progress update every 20 combinations
            if i > 0 and i % 20 == 0:
                pct = (len(completed) + i) / total_combinations * 100
                logger.info(f"Progress: {len(completed) + i}/{total_combinations} ({pct:.1f}%)")

            # Explore this combination
            dow_name = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][dow]
            logger.debug(f"Exploring: {city_name}, {dow_name}, {duration}n, {advance}d ahead")

            random_delay()

            success, hotels_count, error = explore_combination(
                client, city_name, dow, duration, advance, db
            )

            # Record progress
            db.record_discovery_attempt(
                session_id=session_id,
                city=city_name,
                day_of_week=dow,
                duration=duration,
                advance_days=advance,
                status='success' if success else 'error',
                hotels_found=hotels_count,
                error_message=error
            )

            results['explored_now'] += 1
            results['hotels_found'] += hotels_count

            if not success:
                results['errors'] += 1
                logger.warning(f"Error: {city_name}/{dow}/{duration}/{advance}: {error}")

    results['elapsed_seconds'] = time() - start_time

    # Final stats
    final_completed = len(completed) + results['explored_now']
    final_pct = final_completed / total_combinations * 100

    logger.info("=" * 60)
    logger.info("DISCOVERY COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Session: {session_id}")
    logger.info(f"Explored this run: {results['explored_now']}")
    logger.info(f"Hotels found: {results['hotels_found']}")
    logger.info(f"Errors: {results['errors']}")
    logger.info(f"Total progress: {final_completed}/{total_combinations} ({final_pct:.1f}%)")
    logger.info(f"Elapsed time: {results['elapsed_seconds'] / 60:.1f} minutes")

    # Print matrix stats
    matrix_stats = db.get_matrix_stats()
    logger.info(f"Matrix entries: {matrix_stats.get('entries_with_data', 0)}")
    logger.info(f"Average yield: {matrix_stats.get('overall_avg_yield', 0):.1f} LP/$")
    logger.info(f"Best yield ever: {matrix_stats.get('best_yield_ever', 0):.1f} LP/$")

    return results


def print_top_discoveries(limit: int = 10):
    """Print the top discoveries from the matrix."""
    db = get_database()

    logger.info("\n" + "=" * 60)
    logger.info("TOP DISCOVERIES (Premium Hotels)")
    logger.info("=" * 60)

    top_entries = db.get_top_matrix_entries(min_stars=4, limit=limit)

    for entry in top_entries:
        dow_name = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][entry['day_of_week']]
        premium_yield = entry.get('top_premium_yield') or entry.get('avg_yield') or 0
        hotel_name = entry.get('top_premium_hotel') or 'Various'
        stars = entry.get('top_premium_stars') or 0

        logger.info(
            f"{entry['city']:12} {dow_name:3} {entry['duration']}n {entry['advance_days']:2}d ahead | "
            f"{premium_yield:5.1f} LP/$ | {'★' * stars} {hotel_name[:30]}"
        )


def run_verification(max_entries: int = 50, max_time_minutes: int = 30):
    """
    Re-verify stale/unstable matrix entries.

    Instead of exploring new combinations, this re-tests entries that:
    - Haven't been verified in 7+ days
    - Have low yield stability (<85%)
    - Have been verified fewer than 2 times
    """
    logger.info("=" * 60)
    logger.info("VERIFICATION MODE - Re-testing stale/unstable entries")
    logger.info("=" * 60)

    # Get entries needing verification
    entries = get_entries_needing_verification(limit=max_entries)

    if not entries:
        logger.info("No entries need verification!")
        return {'verified': 0, 'errors': 0}

    logger.info(f"Found {len(entries)} entries needing verification")

    # Convert to combinations format
    combinations = [
        (e.city, e.day_of_week, e.duration, e.advance_days)
        for e in entries
    ]

    # Create verification session
    session_id = f"verify_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    logger.info(f"Verification session: {session_id}")

    # Run discovery on these specific combinations
    results = run_discovery(
        session_id=session_id,
        max_time_minutes=max_time_minutes,
        shuffle=False,
        specific_combinations=combinations
    )

    logger.info("")
    logger.info("=" * 60)
    logger.info("VERIFICATION COMPLETE")
    logger.info(f"Re-verified: {results['explored_now']} entries")
    logger.info(f"Errors: {results['errors']}")
    logger.info("=" * 60)

    return results


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(description="Hotel Yield Discovery Engine")
    parser.add_argument("--resume", type=str, help="Resume previous session by ID")
    parser.add_argument("--max-time", type=int, default=60, help="Max runtime in minutes")
    parser.add_argument("--city", type=str, help="Explore single city only")
    parser.add_argument("--no-shuffle", action="store_true", help="Don't randomize order")
    parser.add_argument("--top", type=int, default=0, help="Just print top N discoveries")
    parser.add_argument("--verify", action="store_true", help="Re-verify stale/unstable entries")
    parser.add_argument("--health", action="store_true", help="Show matrix health report")
    parser.add_argument("--verify-count", type=int, default=50, help="Max entries to verify")
    args = parser.parse_args()

    # Show health report
    if args.health:
        health = get_matrix_health()
        print(format_health_report(health))
        return

    # Just print top discoveries
    if args.top > 0:
        print_top_discoveries(args.top)
        return

    # Verification mode
    if args.verify:
        run_verification(
            max_entries=args.verify_count,
            max_time_minutes=args.max_time
        )
        return

    # Session ID
    if args.resume:
        session_id = args.resume
        logger.info(f"Resuming session: {session_id}")
    else:
        session_id = f"discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        logger.info(f"New session: {session_id}")

    # City filter
    cities = [args.city] if args.city else None

    # Run discovery
    results = run_discovery(
        session_id=session_id,
        cities=cities,
        max_time_minutes=args.max_time,
        shuffle=not args.no_shuffle
    )

    # Print top discoveries
    print_top_discoveries(10)

    # Exit code
    if results['errors'] > results['explored_now'] * 0.5:
        logger.error("Too many errors - check API connectivity")
        sys.exit(1)


if __name__ == "__main__":
    main()
