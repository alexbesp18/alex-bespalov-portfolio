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
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from src.fetch_prices import PriceFetcher
from src.compute_flags import process_ticker_data, compute_flags
from src.evaluate_triggers import evaluate_ticker, update_cooldowns
from src.send_email import EmailSender, format_main_email, format_reminder_email
from src.handle_action import handle_action

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TRADING_ALERTS")


def load_json(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {}


def save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


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
    portfolio = load_json(config_dir / "portfolio.json")
    watchlist = load_json(config_dir / "watchlist.json")
    actioned = load_json(config_dir / "actioned.json")
    
    # Load state files
    last_run = load_json(state_dir / "last_run.json")
    cooldowns = load_json(state_dir / "cooldowns.json")
    
    # Get API keys
    td_api_key = os.environ.get("TWELVE_DATA_API_KEY")
    resend_api_key = os.environ.get("RESEND_API_KEY")
    email_from = os.environ.get("SENDER_EMAIL", "alexb@novaconsultpro.com")
    email_to = os.environ.get("NOTIFICATION_EMAILS", "ab00477@icloud.com,alexbespalovtx@gmail.com")
    email_recipients = [e.strip() for e in email_to.split(",") if e.strip()]
    
    if not td_api_key:
        logger.error("TWELVE_DATA_API_KEY not set")
        sys.exit(1)
    
    # Initialize email sender
    email_sender = EmailSender(resend_api_key, email_from, email_recipients)
    
    # Reminder mode: send based on saved state
    if args.reminder:
        last_signals = last_run.get('signals', {})
        portfolio_signals = last_signals.get('portfolio', [])
        watchlist_signals = last_signals.get('watchlist', [])
        
        if not portfolio_signals and not watchlist_signals:
            logger.info("No signals from last run. Skipping reminder.")
            return
        
        date_str = last_run.get('date', datetime.now().strftime('%Y-%m-%d'))
        body = format_reminder_email(portfolio_signals, watchlist_signals, date_str)
        subject = f"Reminder — Trading Signals from {date_str}"
        
        if args.dry_run:
            logger.info("Dry Run - Reminder Email:")
            logger.info(body)
        else:
            email_sender.send(subject, body)
        return
    
    # Main run: fetch, compute, evaluate
    all_tickers = (
        portfolio.get('tickers', []) + 
        watchlist.get('tickers', [])
    )
    
    if not all_tickers:
        logger.warning("No tickers configured. Check portfolio.json and watchlist.json")
        return
    
    logger.info(f"Starting scan for {len(all_tickers)} tickers...")
    
    # Fetch price data
    fetcher = PriceFetcher(td_api_key)
    raw_data = fetcher.fetch_all_tickers(all_tickers)
    
    # Process each ticker
    portfolio_signals = []
    watchlist_signals = []
    no_signal_tickers = []
    new_state = {}
    
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
        
        # Determine list type
        list_type = 'portfolio' if ticker in portfolio.get('tickers', []) else 'watchlist'
        
        # Get last run signals for deduplication
        last_signals_for_ticker = [
            s['signal_key'] 
            for s in last_run.get('signals', {}).get(list_type, [])
            if s.get('ticker') == ticker
        ]
        
        # Evaluate triggers
        signals = evaluate_ticker(
            ticker, flags, list_type, cooldowns, actioned, last_signals_for_ticker
        )
        
        if signals:
            if list_type == 'portfolio':
                portfolio_signals.extend(signals)
            else:
                watchlist_signals.extend(signals)
            logger.info(f"Signals for {ticker}: {[s['signal'] for s in signals]}")
        else:
            no_signal_tickers.append(ticker)
    
    # Update cooldowns
    all_signals = portfolio_signals + watchlist_signals
    cooldowns = update_cooldowns(cooldowns, all_signals)
    save_json(state_dir / "cooldowns.json", cooldowns)
    
    # Save state for next run
    save_json(state_dir / "last_run.json", {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'flags': new_state,
        'signals': {
            'portfolio': portfolio_signals,
            'watchlist': watchlist_signals,
        }
    })
    
    # Send email if there are signals
    if portfolio_signals or watchlist_signals:
        date_str = datetime.now().strftime('%Y-%m-%d')
        body = format_main_email(
            portfolio_signals, 
            watchlist_signals, 
            no_signal_tickers,
            date_str
        )
        
        sell_count = len([s for s in portfolio_signals if s['action'] == 'SELL'])
        buy_count = len([s for s in all_signals if s['action'] == 'BUY'])
        subject = f"Trading Signals — {date_str}"
        
        if args.dry_run:
            logger.info("Dry Run - Main Email:")
            logger.info(body)
        else:
            email_sender.send(subject, body)
    else:
        logger.info("No new signals today.")


if __name__ == "__main__":
    main()
