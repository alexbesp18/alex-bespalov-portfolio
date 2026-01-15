#!/usr/bin/env python3
"""
main.py — Trading Alert System orchestration.

Usage:
    python main.py                 # Main run (fetch, compute, evaluate, email)
    python main.py --dry-run       # Main run without sending email
    python main.py --reminder      # Send reminder email (no fetch)
    python main.py --action TITLE  # Process actioned issue
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Use shared_core utilities
from shared_core import (
    setup_logging,
    get_cached_tickers,
    safe_read_json,
    safe_write_json,
    archive_daily_indicators,
)
from shared_core.triggers.conditions import update_cooldowns

from src.fetch_prices import PriceFetcher
from src.compute_flags import process_ticker_data, compute_flags
from src.evaluate_triggers import evaluate_ticker
from src.send_email import EmailSender, format_main_email, format_reminder_email
from src.handle_action import handle_action

# Configure logging
logger = setup_logging("TRADING_ALERTS")


def load_json(path: Path) -> dict:
    """Load JSON from path using shared_core utility."""
    return safe_read_json(str(path)) or {}


def save_json(path: Path, data: dict):
    """Save JSON to path using shared_core utility."""
    safe_write_json(str(path), data)


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Trading Alert System")
    parser.add_argument("--dry-run", action="store_true", help="Don't send email")
    parser.add_argument("--reminder", action="store_true", help="Send reminder email only")
    parser.add_argument("--action", type=str, help="Process actioned issue: ACTIONED:TICKER:SIGNAL")
    args = parser.parse_args()

    base_dir = Path(__file__).parent
    config_dir = base_dir / "config"
    state_dir = base_dir / "state"

    # Handle action mode
    if args.action:
        success = handle_action(args.action, config_dir)
        sys.exit(0 if success else 1)

    # Load config files
    # portfolio.json: Optional override - tickers here use PORTFOLIO_SIGNALS only
    # actioned.json: Suppressed signals
    portfolio = load_json(config_dir / "portfolio.json")
    actioned = load_json(config_dir / "actioned.json")

    # Load state files
    last_run = load_json(state_dir / "last_run.json")
    cooldowns = load_json(state_dir / "cooldowns.json")

    # Default: use cached tickers from 007-ticker-analysis
    cache_dir = base_dir.parent / "007-ticker-analysis" / "data" / "twelve_data"

    # Get API keys
    td_api_key = os.environ.get("TWELVE_DATA_API_KEY")
    resend_api_key = os.environ.get("RESEND_API_KEY")
    email_from = os.environ.get("SENDER_EMAIL")
    email_to = os.environ.get("NOTIFICATION_EMAILS", "")
    email_recipients = [e.strip() for e in email_to.split(",") if e.strip()]

    if not td_api_key:
        logger.error("TWELVE_DATA_API_KEY not set")
        sys.exit(1)

    # Initialize email sender
    email_sender = EmailSender(resend_api_key, email_from, email_recipients)

    # Reminder mode: send based on saved state
    if args.reminder:
        last_signals = last_run.get('signals', [])

        if not last_signals:
            logger.info("No signals from last run. Skipping reminder.")
            return

        date_str = last_run.get('date', datetime.now().strftime('%Y-%m-%d'))
        body = format_reminder_email(last_signals, date_str)
        subject = f"Reminder — Trading Signals from {date_str}"

        if args.dry_run:
            logger.info("Dry Run - Reminder Email:")
            logger.info(body)
        else:
            email_sender.send(subject, body)
        return

    # Main run: fetch, compute, evaluate
    # Get all tickers from cache
    all_tickers = get_cached_tickers(str(cache_dir))

    if not all_tickers:
        logger.warning("No tickers found in cache. Check 007-ticker-analysis cache.")
        return

    # Portfolio tickers (optional override) - these get PORTFOLIO_SIGNALS only
    portfolio_tickers = set(portfolio.get('tickers', []))

    if portfolio_tickers:
        logger.info(f"Portfolio override: {len(portfolio_tickers)} tickers with portfolio-only signals")

    logger.info(f"Starting scan for {len(all_tickers)} tickers (all signals on all by default)...")

    # Fetch price data
    fetcher = PriceFetcher(td_api_key)
    raw_data = fetcher.fetch_all_tickers(all_tickers)

    # Process each ticker
    all_signals = []
    no_signal_tickers = []
    new_state = {}
    archive_data = []  # Full indicator data for Supabase

    for ticker in all_tickers:
        data = raw_data.get(ticker)
        if not data:
            logger.warning(f"No data for {ticker}")
            continue

        # Process data
        df = process_ticker_data(data)
        if df is None:
            logger.warning(f"Could not process data for {ticker}")
            continue

        # Get previous state for event detection
        prev_state = last_run.get('flags', {}).get(ticker)

        # Compute flags
        flags = compute_flags(df, prev_state)
        new_state[ticker] = flags

        # Collect full indicator data for archiving
        curr = df.iloc[-1]
        archive_data.append({
            'symbol': ticker,
            'close': float(curr['close']),
            'rsi': float(curr.get('rsi')) if curr.get('rsi') is not None else None,
            'stoch_k': None,  # Not computed in 008-alerts
            'stoch_d': None,
            'williams_r': None,
            'roc': None,
            'macd': float(curr.get('macd')) if curr.get('macd') is not None else None,
            'macd_signal': float(curr.get('macd_signal')) if curr.get('macd_signal') is not None else None,
            'macd_hist': float(curr.get('macd_hist')) if curr.get('macd_hist') is not None else None,
            'adx': None,
            'sma_20': float(curr.get('sma20')) if curr.get('sma20') is not None else None,
            'sma_50': float(curr.get('sma50')) if curr.get('sma50') is not None else None,
            'sma_200': float(curr.get('sma200')) if curr.get('sma200') is not None else None,
            'volume': int(curr.get('volume')) if curr.get('volume') is not None else None,
            'volume_ratio': float(curr.get('volume_ratio')) if curr.get('volume_ratio') is not None else None,
            'bullish_score': flags.get('score'),
            # NEW: Component breakdown for historical analysis
            'bullish_components': flags.get('score_components'),
        })

        # Determine signal mode:
        # - 'portfolio' if explicitly in portfolio.json (PORTFOLIO_SIGNALS only)
        # - 'all' otherwise (ALL_SIGNALS - both buy and sell)
        list_type = 'portfolio' if ticker in portfolio_tickers else 'all'

        # Get last run signals for deduplication
        last_signals_for_ticker = [
            s['signal_key']
            for s in last_run.get('signals', [])
            if s.get('ticker') == ticker
        ]

        # Evaluate triggers
        signals = evaluate_ticker(
            ticker, flags, list_type, cooldowns, actioned, last_signals_for_ticker
        )

        if signals:
            all_signals.extend(signals)
            logger.info(f"Signals for {ticker}: {[s['signal'] for s in signals]}")
        else:
            no_signal_tickers.append(ticker)

    # Update cooldowns
    cooldowns = update_cooldowns(cooldowns, all_signals)
    save_json(state_dir / "cooldowns.json", cooldowns)

    # Save state for next run
    save_json(state_dir / "last_run.json", {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'flags': new_state,
        'signals': all_signals,
    })

    # Archive to Supabase (non-blocking)
    try:
        archived = archive_daily_indicators(archive_data, score_type="bullish")
        if archived > 0:
            logger.info(f"Archived {archived} indicators to Supabase")
    except Exception as e:
        logger.warning(f"Failed to archive to Supabase: {e}")

    # Send email if there are signals
    if all_signals:
        date_str = datetime.now().strftime('%Y-%m-%d')
        body = format_main_email(all_signals, no_signal_tickers, date_str)

        sell_count = len([s for s in all_signals if s['action'] == 'SELL'])
        buy_count = len([s for s in all_signals if s['action'] == 'BUY'])
        subject = f"Trading Signals — {date_str} ({buy_count} BUY, {sell_count} SELL)"

        if args.dry_run:
            logger.info("Dry Run - Main Email:")
            logger.info(body)
        else:
            email_sender.send(subject, body)
    else:
        logger.info("No new signals today.")


if __name__ == "__main__":
    main()
