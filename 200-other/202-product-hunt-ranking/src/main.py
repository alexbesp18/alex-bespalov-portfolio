"""Product Hunt Weekly Ranking Pipeline.

Scrapes top products, enriches with Grok AI, saves to Supabase.
"""

import datetime
import urllib.request
import logging
from typing import List, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings
from src.utils.parsing import parse_products
from src.models import Product
from src.db import PHSupabaseClient
from src.analysis import PHGrokAnalyzer

# Setup Logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_current_week_info() -> tuple[str, int, int, datetime.date]:
    """
    Get current week URL and metadata.

    Returns:
        Tuple of (url, week_number, year, week_date)
    """
    today = datetime.datetime.now()
    year = today.year
    week = today.isocalendar()[1]

    # Get Monday of current week as week_date
    week_date = today.date() - datetime.timedelta(days=today.weekday())

    url = f"https://www.producthunt.com/leaderboard/weekly/{year}/{week}"
    logger.info(f"Target URL: {url}")
    return url, week, year, week_date


def get_week_url(year: int, week: int) -> tuple[str, datetime.date]:
    """
    Construct URL and week_date for a specific week.

    Args:
        year: Year
        week: ISO week number

    Returns:
        Tuple of (url, week_date)
    """
    # Calculate the Monday of the given ISO week
    jan4 = datetime.date(year, 1, 4)
    start_of_week1 = jan4 - datetime.timedelta(days=jan4.weekday())
    week_date = start_of_week1 + datetime.timedelta(weeks=week - 1)

    url = f"https://www.producthunt.com/leaderboard/weekly/{year}/{week}"
    return url, week_date


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60)
)
def fetch_html(url: str) -> str:
    """
    Fetches HTML content from the given URL with robust headers and retry logic.
    Raises exception on failure to trigger retry.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as response:
        result: str = response.read().decode('utf-8')
        return result


def run_pipeline(
    year: Optional[int] = None,
    week: Optional[int] = None,
    skip_if_exists: bool = True
) -> bool:
    """
    Run the full pipeline: scrape, enrich, save.

    Args:
        year: Override year (default: current)
        week: Override week (default: current)
        skip_if_exists: Skip if week already in DB

    Returns:
        True if successful
    """
    # Initialize clients
    if not settings.supabase_url or not settings.supabase_key:
        logger.error("Supabase credentials not configured")
        return False

    db = PHSupabaseClient(settings.supabase_url, settings.supabase_key)

    # Get week info
    if year and week:
        url, week_date = get_week_url(year, week)
    else:
        url, week, year, week_date = get_current_week_info()

    logger.info(f"Processing Week {week}, {year} (date: {week_date})")

    # Check if already exists
    if skip_if_exists and db.week_exists(week_date):
        logger.info(f"Week {week_date} already exists in DB, skipping")
        return True

    # Fetch HTML
    try:
        html = fetch_html(url)
    except Exception as e:
        logger.error(f"Failed to fetch {url} after retries: {e}")
        return False

    if not html:
        logger.error("No HTML returned. Aborting.")
        return False

    # Parse products
    products: List[Product] = parse_products(html, limit=10)
    if not products:
        logger.warning("No products found in HTML.")
        return False

    logger.info(f"Scraped {len(products)} products")

    # Initialize Grok analyzer if API key available
    analyzer: Optional[PHGrokAnalyzer] = None
    if settings.xai_api_key:
        analyzer = PHGrokAnalyzer(
            api_key=settings.xai_api_key,
            model=settings.grok_model,
            verbose=True
        )

    # Enrich products with Grok
    if analyzer:
        logger.info("Enriching products with Grok AI...")
        enriched = analyzer.enrich_products_batch(
            products=products,
            week_date=week_date,
            week_number=week,
            year=year
        )
    else:
        # Fallback: create enriched products without AI
        logger.warning("No XAI_API_KEY, saving raw products without enrichment")
        from src.db.models import EnrichedProduct
        enriched = [
            EnrichedProduct(
                week_date=week_date,
                week_number=week,
                year=year,
                rank=p.rank,
                name=p.name,
                description=p.description,
                upvotes=p.upvotes,
                url=str(p.url),
            )
            for p in products
        ]

    # Save to Supabase
    saved_count = db.save_products(enriched)
    logger.info(f"Saved {saved_count} products to Supabase")

    # Generate and save weekly insights
    if analyzer and enriched:
        logger.info("Generating weekly insights...")
        insights = analyzer.generate_weekly_insights(
            products=enriched,
            week_date=week_date,
            week_number=week,
            year=year
        )
        db.save_insights(insights)
        logger.info(f"Saved insights for week {week_date}")

    return True


def main() -> None:
    """Main entry point for weekly pipeline."""
    logger.info("Starting Product Hunt Extraction Job")
    success = run_pipeline()
    if success:
        logger.info("Pipeline completed successfully")
    else:
        logger.error("Pipeline failed")


if __name__ == "__main__":
    main()
