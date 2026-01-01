"""Product Hunt Weekly Ranking Pipeline.

Scrapes top products, enriches with Grok AI, saves to Supabase,
and optionally sends weekly digest email.
"""

import datetime
import logging

from src.analysis import PHGrokAnalyzer
from src.analytics.aggregations import aggregate_category_trends, get_solo_builder_pick
from src.config import settings
from src.db import PHSupabaseClient
from src.db.models import EnrichedProduct, PHWeeklyInsights
from src.models import Product
from src.notifications import send_weekly_digest
from src.utils.http import fetch_html
from src.utils.parsing import parse_products

# Setup Logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
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


def run_pipeline(
    year: int | None = None,
    week: int | None = None,
    skip_if_exists: bool = True,
    send_email: bool = True,
) -> bool:
    """
    Run the full pipeline: scrape, enrich, save, and optionally email.

    Args:
        year: Override year (default: current)
        week: Override week (default: current)
        skip_if_exists: Skip if week already in DB
        send_email: Send weekly digest email after success

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
    products: list[Product] = parse_products(html, limit=10)
    if not products:
        logger.warning("No products found in HTML.")
        return False

    logger.info(f"Scraped {len(products)} products")

    # Initialize Grok analyzer if API key available
    analyzer: PHGrokAnalyzer | None = None
    if settings.xai_api_key:
        analyzer = PHGrokAnalyzer(
            api_key=settings.xai_api_key, model=settings.grok_model, verbose=True
        )

    # Enrich products with Grok
    insights: PHWeeklyInsights | None = None
    enriched: list[EnrichedProduct]

    if analyzer:
        logger.info("Enriching products with Grok AI...")
        enriched = analyzer.enrich_products_batch(
            products=products, week_date=week_date, week_number=week, year=year
        )
    else:
        # Fallback: create enriched products without AI
        logger.warning("No XAI_API_KEY, saving raw products without enrichment")
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
            products=enriched, week_date=week_date, week_number=week, year=year
        )
        db.save_insights(insights)
        logger.info(f"Saved insights for week {week_date}")

    # Aggregate category trends for analytics
    if enriched:
        logger.info("Aggregating category trends...")
        trends = aggregate_category_trends(enriched, week_date, db.client)
        logger.info(f"Aggregated {len(trends)} category trends")

    # Find solo builder pick
    solo_pick = get_solo_builder_pick(enriched) if enriched else None
    if solo_pick:
        logger.info(f"Solo Builder Pick: {solo_pick.name}")

    # Send weekly digest email
    if send_email and enriched:
        logger.info("Sending weekly digest email...")
        email_sent = send_weekly_digest(
            products=enriched,
            insights=insights,
            week_date=week_date,
            solo_pick=solo_pick,
        )
        if email_sent:
            logger.info("Weekly digest email sent successfully")
        else:
            logger.warning("Weekly digest email not sent (check RESEND_API_KEY)")

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
