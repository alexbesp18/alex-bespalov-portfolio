#!/usr/bin/env python3
"""
Discover Agoda place IDs for US cities.

Run this once to populate the cities table with place IDs.

Usage:
    python scripts/discover_cities.py           # Discover all MSAs
    python scripts/discover_cities.py --limit 50  # Top 50 only
    python scripts/discover_cities.py --test    # Test mode (dry run)
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / '.env')
except ImportError:
    pass

from rich.console import Console
from rich.table import Table

from core.city_discovery import discover_all_cities, get_all_msa_data
from core.database import get_database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
console = Console()


def show_status():
    """Show current city discovery status."""
    db = get_database()

    table = Table(title="City Discovery Status")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    total_msas = len(get_all_msa_data())
    stats = db.get_stats()

    table.add_row("Total US MSAs", str(total_msas))
    table.add_row("Cities in Database", str(stats['total_cities']))
    table.add_row("With Agoda Place ID", str(stats['cities_with_agoda_id']))
    table.add_row("Missing Place ID", str(stats['total_cities'] - stats['cities_with_agoda_id']))

    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="Discover Agoda place IDs for US cities")
    parser.add_argument("--limit", type=int, help="Limit number of cities to discover")
    parser.add_argument("--test", action="store_true", help="Test mode (show status only)")
    parser.add_argument("--status", action="store_true", help="Show current status")
    args = parser.parse_args()

    if args.status or args.test:
        show_status()
        return

    console.print("[bold cyan]Starting city registration...[/bold cyan]")

    results = discover_all_cities(limit=args.limit)

    console.print()
    console.print("[bold green]Registration Complete![/bold green]")
    console.print(f"  Total processed: {results['total']}")
    console.print(f"  With Agoda IDs: {results['discovered']}")
    console.print(f"  Missing IDs: {results['missing']}")

    show_status()


if __name__ == "__main__":
    main()
