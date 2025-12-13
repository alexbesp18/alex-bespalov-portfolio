"""
Backfill Script: Fetch historical Product Hunt weekly rankings.

This script fetches the top 10 products for each of the last N weeks
and appends them to your Google Sheet.

Usage:
    python -m src.backfill

The script respects rate limits by pausing between requests.
"""

import datetime
import time
import logging
from typing import List

from src.main import fetch_html, save_to_gsheet
from src.utils.parsing import parse_products
from src.models import Product
from src.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_week_url(year: int, week: int) -> str:
    """Construct URL for a specific year/week."""
    return f"https://www.producthunt.com/leaderboard/weekly/{year}/{week}"

def get_week_start_date(year: int, week: int) -> str:
    """Get the Monday date for a given ISO week number."""
    # ISO week date: Monday of week 1 is the Monday of the week containing Jan 4
    jan4 = datetime.date(year, 1, 4)
    week1_monday = jan4 - datetime.timedelta(days=jan4.weekday())
    target_monday = week1_monday + datetime.timedelta(weeks=week - 1)
    return target_monday.strftime("%Y-%m-%d")

def backfill(weeks_back: int = 10) -> None:
    """
    Fetch historical data for the last N weeks.
    
    Args:
        weeks_back: Number of weeks to go back (default: 10)
    """
    today = datetime.date.today()
    current_year = today.year
    current_week = today.isocalendar()[1]
    
    logger.info(f"Starting backfill for {weeks_back} weeks (current: {current_year}/W{current_week})")
    
    all_products: List[Product] = []
    
    for i in range(weeks_back, 0, -1):  # Go from oldest to newest
        target_week = current_week - i
        target_year = current_year
        
        # Handle year boundary
        if target_week <= 0:
            target_year -= 1
            target_week += 52  # Approximate, good enough for this use case
        
        url = get_week_url(target_year, target_week)
        week_date = get_week_start_date(target_year, target_week)
        
        logger.info(f"Fetching Week {target_week} of {target_year} ({week_date})...")
        
        try:
            html = fetch_html(url)
            products = parse_products(html, limit=10, week_date=week_date)
            
            if products:
                logger.info(f"  Found {len(products)} products")
                all_products.extend(products)
            else:
                logger.warning(f"  No products found for week {target_week}")
                
        except Exception as e:
            logger.error(f"  Failed to fetch week {target_week}: {e}")
        
        # Rate limiting: be nice to Product Hunt servers
        time.sleep(2)
    
    if all_products:
        logger.info(f"Total products fetched: {len(all_products)}")
        logger.info("Saving to Google Sheet...")
        save_to_gsheet(all_products)
        logger.info("Backfill complete!")
    else:
        logger.warning("No products were fetched. Nothing to save.")

if __name__ == "__main__":
    backfill(weeks_back=10)
