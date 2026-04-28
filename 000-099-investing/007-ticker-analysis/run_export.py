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
import fcntl
import os
import re
import sys
import tempfile
import time
from pathlib import Path

from core import load_config, SheetManager

# Force line-buffered stdout under launchd (no TTY = block-buffered by default)
sys.stdout.reconfigure(line_buffering=True)

LOCK_FILE = Path(tempfile.gettempdir()) / "sheet-export.lock"

EXPORT_TABS = ["tech_analysis_clean", "Price movement"]
FRESHNESS_TAB = "tech_analysis_clean"
POLL_INTERVAL = 900  # 15 minutes
MAX_RETRIES = 8      # 2 hours total
FRESHNESS_THRESHOLD = 0.8  # require ≥80% of rows stamped today (catches partial writes)


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


RETRYABLE_ERRORS = (
    ConnectionError, ConnectionResetError, TimeoutError, OSError,
)
RETRYABLE_MESSAGES = ("timeout", "connection reset", "connection aborted", "transport")


def _is_retryable(e: Exception) -> bool:
    """Check if an exception is a transient network error worth retrying."""
    if isinstance(e, RETRYABLE_ERRORS):
        return True
    msg = str(e).lower()
    return any(term in msg for term in RETRYABLE_MESSAGES)


def read_with_retry(sm: SheetManager, tab: str, verbose: bool,
                    max_retries: int = 3) -> list:
    """Read a sheet tab, retrying on transient network errors."""
    for attempt in range(max_retries):
        try:
            return sm.read_tab_values(tab)
        except Exception as e:
            if _is_retryable(e) and attempt < max_retries - 1:
                wait = 5 * (attempt + 1)
                if verbose:
                    print(f"   ⚠️  {type(e).__name__} reading '{tab}' "
                          f"(attempt {attempt + 1}/{max_retries}), "
                          f"retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise
    return []  # unreachable, but satisfies type checkers


def sanitize_name(tab_name: str) -> str:
    return re.sub(r'[^a-z0-9_]', '_', tab_name.lower()).strip('_')


def is_data_fresh(sm: SheetManager, today: str, verbose: bool) -> bool:
    rows = read_with_retry(sm, FRESHNESS_TAB, verbose)
    if len(rows) < 2:
        if verbose:
            print(f"   ⚠️  {FRESHNESS_TAB}: no data rows")
        return False

    header = rows[0]
    updated_idx = header.index('Updated') if 'Updated' in header else 3
    data = rows[1:]

    fresh = sum(
        1 for r in data
        if updated_idx < len(r) and r[updated_idx].startswith(today)
    )
    ratio = fresh / len(data) if data else 0
    is_fresh = ratio >= FRESHNESS_THRESHOLD
    if verbose:
        print(f"   Freshness: {fresh}/{len(data)} rows stamped {today} "
              f"({ratio:.0%}, threshold {FRESHNESS_THRESHOLD:.0%}) "
              f"{'✅ fresh' if is_fresh else '⏳ partial/stale'}")
    return is_fresh


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

    # Connect with retries — Google auth/API can drop connections transiently
    sm = None
    for attempt in range(3):
        try:
            sm = SheetManager(gs.credentials_file, gs.spreadsheet_name, verbose=args.verbose)
            break
        except Exception as e:
            if _is_retryable(e) and attempt < 2:
                wait = 10 * (attempt + 1)
                if args.verbose:
                    print(f"   ⚠️  {type(e).__name__} connecting to Sheets "
                          f"(attempt {attempt + 1}/3), retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise
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
        rows = read_with_retry(sm, tab, args.verbose)
        if args.verbose:
            print(f"   {len(rows) - 1} data rows")

        if args.dry_run:
            continue

        filename = f"{sanitize_name(tab)}.csv"
        path = out_dir / filename
        # Atomic write: write to temp file, then rename
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=str(out_dir), suffix='.csv.tmp', prefix=filename
        )
        try:
            with os.fdopen(tmp_fd, 'w', newline='') as f:
                csv.writer(f).writerows(rows)
            os.replace(tmp_path, path)
        except Exception:
            os.unlink(tmp_path)
            raise
        if args.verbose:
            print(f"   ✅ Saved: {path}")

    if args.verbose:
        print(f"\n{'=' * 50}")
        print("COMPLETE")
        print("=" * 50)


if __name__ == "__main__":
    try:
        lock_fd = open(LOCK_FILE, 'w')
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("⚠️  Another export is already running. Exiting.")
            sys.exit(0)
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
