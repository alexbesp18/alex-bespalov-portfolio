#!/usr/bin/env python3
"""True Value Oversold Report — structural integrity filter for oversold names.

A separate report alongside the existing oversold email. Surfaces only
oversold stocks that pass a 3-stage gate filter ensuring defensible hold theses.

Usage:
    python true_value.py --verbose              # Console table only
    python true_value.py --email                # Send email report
    python true_value.py --dry-run --verbose    # Print HTML, don't send
    python true_value.py --top 10 --email       # Cap at 10 names

Copyright 2024 Alex Bespalov. MIT License.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.fetcher import TwelveDataFetcher
from src.true_value_scorer import TrueValueScorer
from src.true_value_notifier import TrueValueNotifier
from src.true_value_models import TrueValueResult

# Reuse ticker discovery from oversold module (no side effects)
from oversold import get_cached_tickers


def setup_logging(verbose: bool = False) -> logging.Logger:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger("TRUE_VALUE")


def print_table(results: list, total_scanned: int) -> None:
    """Print ASCII table to console."""
    print()
    print("=" * 96)
    print(f"{'TRUE VALUE OVERSOLD':^96}")
    print("=" * 96)

    header = (
        f"{'#':>3} {'Ticker':<7} {'TV Score':>8} {'Tier':<22}"
        f" {'RSI':>5} {'LT':>4} {'SMA':<9} {'OBV':<13} {'1M%':>6} {'1Y%':>6}"
    )
    print(header)
    print("-" * 96)

    for i, r in enumerate(results, 1):
        sma_short = r.sma_alignment[:8]
        obv_short = r.obv_trend[:12]
        pct_1y = f"{r.pct_1y:+.1f}" if r.pct_1y != 0.0 else "N/A"
        row = (
            f"{i:>3} {r.ticker:<7} {r.true_value_score:>8.1f} {r.tier.value:<22}"
            f" {r.mt_rsi:>5.1f} {r.lt_score:>4.1f} {sma_short:<9} {obv_short:<13}"
            f" {r.pct_1m:>+5.1f}% {pct_1y:>5}%"
        )
        print(row)

    print("=" * 96)
    print(f"Scanned: {total_scanned} | Passed gate: {len(results)}")
    print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="True Value Oversold Report — structural integrity filter"
    )
    parser.add_argument("--email", action="store_true", help="Send email report")
    parser.add_argument(
        "--top", "-n", type=int, default=15, help="Max results (default: 15)"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Debug logging")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print HTML to stdout, don't send"
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()
    logger = setup_logging(args.verbose)

    # Resolve paths
    base_dir = Path(__file__).parent.resolve()
    cache_dir = base_dir.parent / "007-ticker-analysis" / "data" / "twelve_data"

    # Load tickers from 007 cache
    tickers = get_cached_tickers(cache_dir)
    if not tickers:
        logger.error(f"No cached tickers found in {cache_dir}")
        return 1

    logger.info(f"Loaded {len(tickers)} tickers from cache")
    total_scanned = len(tickers)

    # Fetch OHLCV data
    api_key = os.environ.get("TWELVE_DATA_API_KEY")
    if not api_key:
        logger.error("TWELVE_DATA_API_KEY not set. Check your .env file.")
        return 1

    fetcher = TwelveDataFetcher(api_key)
    logger.info("Fetching time series data...")
    raw_data = fetcher.fetch_batch_time_series(tickers)

    # Score
    scorer = TrueValueScorer()
    results = scorer.score_batch(raw_data, tickers)

    # Cap at --top
    results = results[: args.top]

    # Console output
    print_table(results, total_scanned)

    if args.verbose and results:
        print("Component breakdown:")
        for r in results:
            print(
                f"  {r.ticker}: oversold={r.oversold_component} "
                f"structure={r.structure_component} "
                f"accum={r.accumulation_component} "
                f"reversal={r.reversal_component}"
            )
        print()

    # Email / dry-run
    if args.email or args.dry_run:
        resend_key = os.environ.get("RESEND_API_KEY", "")
        notifier = TrueValueNotifier(resend_key)

        html, count = notifier.format_email_body(results, total_scanned)
        top_symbols = [r.ticker for r in results[:3]]
        subject = notifier.format_subject(count, top_symbols)

        if args.dry_run:
            print(f"Subject: {subject}\n")
            print(html)
            return 0

        if not resend_key:
            logger.warning("RESEND_API_KEY not set. Skipping email.")
        elif notifier.send_email(subject, html):
            logger.info(f"Email sent: {count} candidates")
        else:
            logger.warning("Failed to send email")

    return 0


if __name__ == "__main__":
    sys.exit(main())
