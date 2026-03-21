#!/usr/bin/env python3
"""
Export hotel deals to CSV.

Usage:
    python scripts/export_csv.py                    # Export all deals
    python scripts/export_csv.py --min-yield 15    # Only yields >= 15
    python scripts/export_csv.py --output deals.csv # Custom filename
"""

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console

from core.database import get_database

console = Console()


def export_deals(
    output_path: str = "data/hotel_deals.csv",
    min_yield: float = 0,
    min_stars: int = 1,
    limit: int = 10000,
):
    """Export deals to CSV file."""
    db = get_database()

    deals = db.get_top_deals(
        limit=limit,
        min_yield=min_yield,
        min_stars=min_stars,
    )

    if not deals:
        console.print("[yellow]No deals found matching criteria.[/yellow]")
        return 0

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV
    fieldnames = [
        'hotel_name', 'city_name', 'state', 'stars', 'rating',
        'check_in', 'check_out', 'nights', 'nightly_rate', 'total_cost',
        'total_miles', 'yield_ratio', 'deal_score', 'url', 'scraped_at'
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for deal in deals:
            row = {k: deal.get(k, '') for k in fieldnames}
            writer.writerow(row)

    return len(deals)


def main():
    parser = argparse.ArgumentParser(description="Export hotel deals to CSV")
    parser.add_argument("--output", "-o", default="data/hotel_deals.csv",
                       help="Output CSV file path")
    parser.add_argument("--min-yield", type=float, default=0,
                       help="Minimum yield ratio")
    parser.add_argument("--min-stars", type=int, default=1,
                       help="Minimum star rating")
    parser.add_argument("--limit", type=int, default=10000,
                       help="Maximum number of deals")
    args = parser.parse_args()

    console.print(f"[cyan]Exporting deals to {args.output}...[/cyan]")

    count = export_deals(
        output_path=args.output,
        min_yield=args.min_yield,
        min_stars=args.min_stars,
        limit=args.limit,
    )

    console.print(f"[green]Exported {count} deals to {args.output}[/green]")


if __name__ == "__main__":
    main()
