#!/usr/bin/env python3
"""
Run Export - Download Google Sheets tabs as CSV to ~/Downloads.

Waits for today's data to appear in tech_analysis_clean before exporting.
Designed to run via macOS launchd after the daily cache-refresh workflow.

Usage:
    python run_export.py --verbose
    python run_export.py --verbose --no-wait
    python run_export.py --output-dir /tmp/csv-test --verbose
    python run_export.py --dry-run --verbose
"""

import argparse
import csv
import datetime as dt
import re
import sys
import time
from pathlib import Path

from core import load_config, SheetManager

EXPORT_TABS = ["tech_analysis_clean", "Price movement"]
FRESHNESS_TAB = "tech_analysis_clean"
POLL_INTERVAL = 900  # 15 minutes
MAX_RETRIES = 8      # 2 hours total


def parse_args():
    parser = argparse.ArgumentParser(
        description='Export Google Sheets tabs as CSV to ~/Downloads'
    )
    parser.add_argument('--config', '-c', default='config.json',
                        help='Path to configuration file (default: config.json)')
    parser.add_argument('--output-dir', '-o',
                        default=str(Path.home() / 'Downloads'),
                        help='Output directory (default: ~/Downloads)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Print detailed progress')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Read sheets but do not write CSVs')
    parser.add_argument('--no-wait', action='store_true',
                        help='Skip freshness check, export immediately')
    return parser.parse_args()


def sanitize_name(tab_name: str) -> str:
    return re.sub(r'[^a-z0-9_]', '_', tab_name.lower()).strip('_')


def is_data_fresh(sm: SheetManager, today: str, verbose: bool) -> bool:
    rows = sm.read_tab_values(FRESHNESS_TAB)
    if len(rows) < 2:
        if verbose:
            print(f"   ⚠️  {FRESHNESS_TAB}: no data rows")
        return False

    header = rows[0]
    updated_idx = header.index('Updated') if 'Updated' in header else 3
    last_row = rows[-1]

    if updated_idx < len(last_row):
        last_updated = last_row[updated_idx]
        is_fresh = last_updated.startswith(today)
        if verbose:
            print(f"   Last row Updated: {last_updated} "
                  f"({'✅ fresh' if is_fresh else '⏳ stale'})")
        return is_fresh

    if verbose:
        print(f"   ⚠️  Updated column missing in last row")
    return False


def wait_for_fresh_data(
    sm: SheetManager, today: str, verbose: bool
) -> bool:
    for attempt in range(1, MAX_RETRIES + 1):
        if verbose:
            print(f"\n🔍 Freshness check {attempt}/{MAX_RETRIES}...")
        if is_data_fresh(sm, today, verbose):
            return True
        if attempt < MAX_RETRIES:
            if verbose:
                print(f"   Waiting {POLL_INTERVAL // 60} minutes...")
            time.sleep(POLL_INTERVAL)
    return False


def main():
    args = parse_args()

    script_dir = Path(__file__).parent
    config = load_config(str(script_dir / args.config))
    gs = config.google_sheets

    if args.verbose:
        print("=" * 50)
        print("CSV EXPORT")
        print("=" * 50)

    sm = SheetManager(gs.credentials_file, gs.spreadsheet_name, verbose=args.verbose)
    today = dt.date.today().isoformat()

    if not args.no_wait:
        if not wait_for_fresh_data(sm, today, args.verbose):
            print(f"❌ Data not updated for {today} after "
                  f"{MAX_RETRIES * POLL_INTERVAL // 60} minutes. Skipping export.")
            sys.exit(1)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for tab in EXPORT_TABS:
        if args.verbose:
            print(f"\n📊 Reading '{tab}'...")
        rows = sm.read_tab_values(tab)
        if args.verbose:
            print(f"   {len(rows) - 1} data rows")

        if args.dry_run:
            continue

        filename = f"{sanitize_name(tab)}.csv"
        path = out_dir / filename
        with open(path, 'w', newline='') as f:
            csv.writer(f).writerows(rows)
        if args.verbose:
            print(f"   ✅ Saved: {path}")

    if args.verbose:
        print(f"\n{'=' * 50}")
        print("COMPLETE")
        print("=" * 50)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
