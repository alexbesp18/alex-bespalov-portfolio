"""
Date permutation rotation system for maximizing yield discovery.

Uses time-of-day patterns to run 3x daily with different search windows:
- Morning (2am): Near-term bookings (1-21 days)
- Afternoon (10am): Mid-term bookings (15-45 days)
- Evening (6pm): Long-term bookings (30-60 days)

Each run covers all stay lengths (1-7 nights) for maximum coverage.
"""

from datetime import datetime, timedelta
from typing import List, Tuple

import pytz

# Use Central Time consistently (matches Railway cron and auto_pattern_scrape.py)
CT = pytz.timezone('America/Chicago')

# Time-of-day patterns for 3x daily runs
# Each pattern focuses on a different booking window with overlap for continuity
RUN_PATTERNS = {
    'morning': {   # 2am - Near-term focus
        'name': 'morning_near_term',
        'stay_lengths': [1, 2, 3, 4, 5, 6, 7],
        'day_targets': None,
        'advance_window': (1, 21),
        'max_dates': 500,
    },
    'afternoon': {  # 10am - Mid-term focus
        'name': 'afternoon_mid_term',
        'stay_lengths': [1, 2, 3, 4, 5, 6, 7],
        'day_targets': None,
        'advance_window': (15, 45),
        'max_dates': 500,
    },
    'evening': {    # 6pm - Long-term focus
        'name': 'evening_long_term',
        'stay_lengths': [1, 2, 3, 4, 5, 6, 7],
        'day_targets': None,
        'advance_window': (30, 60),
        'max_dates': 500,
    },
}

# Legacy day-of-week patterns (kept for backward compatibility)
ROTATION_PATTERNS = {
    0: RUN_PATTERNS['morning'],   # Monday
    1: RUN_PATTERNS['morning'],   # Tuesday
    2: RUN_PATTERNS['afternoon'], # Wednesday
    3: RUN_PATTERNS['afternoon'], # Thursday
    4: RUN_PATTERNS['evening'],   # Friday
    5: RUN_PATTERNS['evening'],   # Saturday
    6: {  # Sunday: Full comprehensive scan
        'name': 'comprehensive',
        'stay_lengths': [1, 2, 3, 4, 5, 6, 7],
        'day_targets': None,
        'advance_window': (1, 60),
        'max_dates': 500,
    },
}


def get_pattern_for_day(day_of_week: int) -> dict:
    """Get the search pattern for a given day of the week."""
    return ROTATION_PATTERNS[day_of_week]


def generate_dates_for_pattern(pattern: dict) -> List[Tuple[datetime, datetime]]:
    """
    Generate search dates based on the day's pattern.

    Returns list of (check_in, check_out) tuples.
    """
    dates = []
    # BUG 5 FIX: Use Central Time consistently with auto_pattern_scrape.py
    today = datetime.now(CT).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)

    advance_min, advance_max = pattern['advance_window']
    stay_lengths = pattern['stay_lengths']
    day_targets = pattern['day_targets']
    max_dates = pattern['max_dates']

    for day_offset in range(advance_min, advance_max + 1):
        check_in = today + timedelta(days=day_offset)

        # Filter by target days if specified
        if day_targets and check_in.weekday() not in day_targets:
            continue

        for nights in stay_lengths:
            check_out = check_in + timedelta(days=nights)
            dates.append((check_in, check_out))

    # Sort by check-in date and limit
    dates.sort(key=lambda x: (x[0], x[1] - x[0]))
    return dates[:max_dates]


def get_todays_search_dates() -> List[Tuple[datetime, datetime]]:
    """
    Get the search dates for today based on day-of-week rotation.

    This is the main entry point for the rotation system.
    """
    # BUG 5 FIX: Use Central Time consistently
    today = datetime.now(CT)
    day_of_week = today.weekday()

    pattern = get_pattern_for_day(day_of_week)
    dates = generate_dates_for_pattern(pattern)

    return dates


def get_pattern_name() -> str:
    """Get the name of today's pattern for logging."""
    # BUG 5 FIX: Use Central Time consistently
    day_of_week = datetime.now(CT).weekday()
    return ROTATION_PATTERNS[day_of_week]['name']


def get_pattern_by_name(pattern_name: str) -> dict:
    """
    Get a pattern by name (morning, afternoon, evening).

    Used by --pattern argument in daily_scrape.py for 3x daily runs.
    """
    if pattern_name not in RUN_PATTERNS:
        raise ValueError(f"Unknown pattern: {pattern_name}. Valid: {list(RUN_PATTERNS.keys())}")
    return RUN_PATTERNS[pattern_name]


def get_search_dates_for_pattern(pattern_name: str) -> List[Tuple[datetime, datetime]]:
    """
    Get search dates for a specific named pattern.

    Args:
        pattern_name: 'morning', 'afternoon', or 'evening'

    Returns:
        List of (check_in, check_out) date pairs
    """
    pattern = get_pattern_by_name(pattern_name)
    return generate_dates_for_pattern(pattern)


if __name__ == '__main__':
    import sys

    # Allow testing specific pattern via command line
    if len(sys.argv) > 1:
        pattern_name = sys.argv[1]
        print(f"Pattern: {pattern_name}")
        dates = get_search_dates_for_pattern(pattern_name)
    else:
        print(f"Today's pattern: {get_pattern_name()}")
        dates = get_todays_search_dates()

    print(f"Generated {len(dates)} date pairs")
    print(f"Stay lengths: 1-7 nights")

    # Show date range
    if dates:
        first_checkin = dates[0][0]
        last_checkin = dates[-1][0]
        print(f"Check-in range: {first_checkin.strftime('%Y-%m-%d')} to {last_checkin.strftime('%Y-%m-%d')}")

    # Show sample
    for i, (check_in, check_out) in enumerate(dates[:5]):
        nights = (check_out - check_in).days
        print(f"  {i+1}. {check_in.strftime('%Y-%m-%d')} ({nights}N)")
    if len(dates) > 5:
        print(f"  ... and {len(dates) - 5} more")

    # Show all pattern summaries
    print("\n--- All Patterns ---")
    for name, pattern in RUN_PATTERNS.items():
        window = pattern['advance_window']
        stays = pattern['stay_lengths']
        max_combos = (window[1] - window[0] + 1) * len(stays)
        print(f"  {name}: {window[0]}-{window[1]} days, {len(stays)} stay lengths, ~{max_combos} combos")
