#!/usr/bin/env python3
"""
Railway daily scrape job.

Runs 3x daily with different patterns:
- Morning (2am): Near-term bookings (1-21 days)
- Afternoon (10am): Mid-term bookings (15-45 days)
- Evening (6pm): Long-term bookings (30-60 days)

Usage:
    python railway/daily_scrape.py                  # Uses day-of-week pattern
    python railway/daily_scrape.py --pattern morning
    python railway/daily_scrape.py --pattern afternoon
    python railway/daily_scrape.py --pattern evening
"""

import argparse
import asyncio
import logging
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force Supabase mode
os.environ['DB_MODE'] = 'supabase'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def main(pattern: str = None):
    """Run daily scrape with date rotation."""
    from core.database import get_database
    from core.date_rotation import (
        get_todays_search_dates,
        get_pattern_name,
        get_search_dates_for_pattern,
        get_pattern_by_name,
    )
    from scrapers.hotel_scraper import scrape_all_cities

    logger.info("=" * 60)
    logger.info("US Hotel Scraper - Daily Run")
    logger.info("=" * 60)

    # Get database
    db = get_database()

    # Step 1: Clean expired deals
    logger.info("Step 1: Cleaning expired deals...")
    try:
        deleted = db.clear_old_deals(days_old=0)
        logger.info(f"Deleted {deleted} expired deals")
    except Exception as e:
        logger.warning(f"Error cleaning old deals: {e}")

    # Step 2: Get search dates based on pattern
    if pattern:
        # Use explicit pattern (for 3x daily runs)
        pattern_config = get_pattern_by_name(pattern)
        pattern_name = pattern_config['name']
        dates = get_search_dates_for_pattern(pattern)
        logger.info(f"Step 2: Using explicit pattern: {pattern}")
    else:
        # Use day-of-week rotation (legacy behavior)
        pattern_name = get_pattern_name()
        dates = get_todays_search_dates()
        logger.info(f"Step 2: Using day-of-week pattern: {pattern_name}")

    logger.info(f"Generated {len(dates)} date combinations to search")

    # Step 3: Scrape with custom dates
    logger.info("Step 3: Starting hotel scrape...")
    try:
        results = await scrape_all_cities(
            custom_dates=dates,
            show_progress=False,  # No progress bar in Railway logs
        )

        logger.info("=" * 60)
        logger.info("SCRAPE COMPLETE")
        logger.info(f"  Cities completed: {results.get('cities_completed', 0)}/{results.get('cities_total', 0)}")
        logger.info(f"  Cities failed: {results.get('cities_failed', 0)}")
        logger.info(f"  Hotels found: {results.get('hotels_found', 0)}")
        logger.info(f"  Deals stored: {results.get('deals_stored', 0)}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Scrape failed: {e}")
        raise

    # Step 4: Report stats
    logger.info("Step 4: Final statistics...")
    try:
        stats = db.get_stats()
        logger.info(f"  Total active deals: {stats.get('active_deals', 0)}")
        logger.info(f"  Average yield: {stats.get('avg_yield', 0)} LP/$")
        logger.info(f"  Max yield: {stats.get('max_yield', 0)} LP/$")
    except Exception as e:
        logger.warning(f"Error getting stats: {e}")

    logger.info("Daily scrape complete!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run hotel scraper with date rotation')
    parser.add_argument(
        '--pattern',
        choices=['morning', 'afternoon', 'evening'],
        default=None,
        help='Use specific pattern instead of day-of-week rotation'
    )
    args = parser.parse_args()

    asyncio.run(main(pattern=args.pattern))
