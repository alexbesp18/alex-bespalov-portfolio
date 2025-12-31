"""
Backfill Script: Fetch historical Product Hunt weekly rankings.

This script fetches the top 10 products for each of the last N weeks
and saves them to Supabase with Grok AI enrichment.

Usage:
    python -m backfill.main
"""

import datetime
import logging
import time

from backfill.config.settings import WEEKS_BACK
from src.config import settings as app_settings
from src.main import run_pipeline

logging.basicConfig(
    level=getattr(logging, app_settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_iso_weeks_in_year(year: int) -> int:
    """Return the number of ISO weeks in a given year (52 or 53)."""
    # Dec 28 is always in the last ISO week of the year
    return datetime.date(year, 12, 28).isocalendar()[1]


def backfill(weeks_back: int = WEEKS_BACK, skip_existing: bool = True) -> None:
    """
    Fetch historical data for the last N weeks.

    Args:
        weeks_back: Number of weeks to go back (from config)
        skip_existing: Skip weeks that already exist in DB
    """
    today = datetime.date.today()
    current_year = today.year
    current_week = today.isocalendar()[1]

    logger.info(
        f"Starting backfill for {weeks_back} weeks (current: {current_year}/W{current_week})"
    )

    success_count = 0
    skip_count = 0
    fail_count = 0

    for i in range(weeks_back, 0, -1):  # Go from oldest to newest
        target_week = current_week - i
        target_year = current_year

        # Handle year boundary correctly (accounts for 52 or 53 week years)
        while target_week <= 0:
            target_year -= 1
            target_week += get_iso_weeks_in_year(target_year)

        logger.info(f"Processing Week {target_week} of {target_year}...")

        try:
            success = run_pipeline(
                year=target_year, week=target_week, skip_if_exists=skip_existing
            )

            if success:
                success_count += 1
            else:
                fail_count += 1

        except Exception as e:
            logger.error(f"Failed to process week {target_week}: {e}")
            fail_count += 1

        # Rate limiting: be nice to Product Hunt servers and Grok API
        time.sleep(3)

    logger.info(
        f"Backfill complete! Success: {success_count}, Skipped: {skip_count}, Failed: {fail_count}"
    )


if __name__ == "__main__":
    backfill()
