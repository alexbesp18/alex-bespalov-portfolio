#!/usr/bin/env python3
"""
Run the hotel scraper.

Usage:
    python scripts/run_scraper.py              # Full scrape (all cities)
    python scripts/run_scraper.py --limit 50   # Top 50 cities only
    python scripts/run_scraper.py --test       # Test mode (no DB writes)
    python scripts/run_scraper.py --stats      # Show statistics only
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.table import Table

from config.settings import get_settings
from core.database import get_database
from scrapers.hotel_scraper import scrape_all_cities

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# Suppress httpx verbose logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
console = Console()


def show_stats():
    """Show current database statistics."""
    db = get_database()
    stats = db.get_stats()

    table = Table(title="Hotel Scraper Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Active Cities", str(stats['total_cities']))
    table.add_row("Cities with Agoda ID", str(stats['cities_with_agoda_id']))
    table.add_row("Total Hotels", str(stats['total_hotels']))
    table.add_row("Active Deals", str(stats['active_deals']))
    table.add_row("Average Yield", f"{stats['avg_yield']:.2f} LP/$")
    table.add_row("Best Yield", f"{stats['max_yield']:.2f} LP/$")

    console.print(table)


def show_top_deals(limit: int = 10):
    """Show top deals by yield."""
    db = get_database()
    deals = db.get_top_deals(limit=limit, min_yield=10)

    if not deals:
        console.print("[yellow]No deals found.[/yellow]")
        return

    table = Table(title=f"Top {limit} Deals by Yield")
    table.add_column("Hotel", style="cyan", max_width=30)
    table.add_column("City", style="white")
    table.add_column("Stars", style="yellow")
    table.add_column("Yield", style="green")
    table.add_column("Cost", style="white")
    table.add_column("Miles", style="magenta")
    table.add_column("Check-in", style="white")

    for deal in deals:
        stars = "★" * int(deal['stars']) if deal['stars'] else "-"
        table.add_row(
            deal['hotel_name'][:30],
            f"{deal['city_name']}, {deal['state']}",
            stars,
            f"{deal['yield_ratio']:.1f}",
            f"${deal['total_cost']:.0f}",
            f"{deal['total_miles']:,}",
            deal['check_in'][:10],
        )

    console.print(table)


async def main():
    parser = argparse.ArgumentParser(description="US Hotel Scraper")
    parser.add_argument("--limit", type=int, help="Limit number of cities to scrape")
    parser.add_argument("--concurrent", type=int, default=10, help="Max concurrent scrapes")
    parser.add_argument("--days", type=int, default=30, help="Days ahead to search")
    parser.add_argument("--test", action="store_true", help="Test mode (minimal scrape)")
    parser.add_argument("--stats", action="store_true", help="Show statistics only")
    parser.add_argument("--top", type=int, help="Show top N deals after scrape")
    parser.add_argument("--force", action="store_true", help="Force scrape all cities (ignore checkpoints)")
    parser.add_argument("--max-age", type=int, default=24, help="Re-scrape cities older than N hours (default: 24)")
    args = parser.parse_args()

    settings = get_settings()

    if args.stats:
        show_stats()
        show_top_deals(10)
        return

    # Check if cities are discovered
    db = get_database()
    stats = db.get_stats()

    if stats['cities_with_agoda_id'] == 0:
        console.print("[red]No cities with Agoda IDs found![/red]")
        console.print("Run [bold]python scripts/discover_cities.py[/bold] first.")
        return

    console.print(f"[bold cyan]Starting hotel scraper...[/bold cyan]")
    console.print(f"  Cities available: {stats['cities_with_agoda_id']}")
    console.print(f"  Days ahead: {args.days}")
    console.print(f"  Max concurrent: {args.concurrent}")
    console.print()

    # Run scraper
    limit = 5 if args.test else args.limit

    results = await scrape_all_cities(
        city_limit=limit,
        max_concurrent=args.concurrent,
        days_ahead=args.days,
        show_progress=True,
        force_all=args.force,
        max_age_hours=args.max_age,
    )

    console.print()
    console.print("[bold green]Scrape Complete![/bold green]")
    console.print(f"  Cities scraped: {results['cities_completed']}/{results['cities_total']}")
    console.print(f"  Hotels found: {results['hotels_found']}")
    console.print(f"  Deals stored: {results.get('deals_stored', results['deals_found'])}")

    if results['cities_failed'] > 0:
        console.print(f"  [yellow]Cities failed: {results['cities_failed']}[/yellow]")

    # Show top deals
    console.print()
    show_top_deals(args.top or 10)


if __name__ == "__main__":
    asyncio.run(main())
