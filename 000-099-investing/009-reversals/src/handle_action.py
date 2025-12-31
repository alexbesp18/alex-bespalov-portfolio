"""
handle_action.py — Process GitHub Issue "ACTIONED" events.

Parses issue title like "ACTIONED:NVDA:SELL_ALERT" and:
1. Adds to actioned.json with 30-day suppression
2. Moves ticker between portfolio/watchlist based on action type
"""

import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def load_json(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {}


def save_json(path: Path, data: dict):
    path.write_text(json.dumps(data, indent=2))


def parse_action_title(title: str) -> Optional[tuple]:
    """
    Parse "ACTIONED:TICKER:SIGNAL" format.
    Returns (ticker, signal) or None.
    """
    if not title.startswith("ACTIONED:"):
        return None
    
    parts = title.split(":")
    if len(parts) < 3:
        return None
    
    _, ticker, signal = parts[0], parts[1].strip(), parts[2].strip()
    return ticker, signal


def add_to_actioned(actioned: dict, ticker: str, signal: str, suppress_days: int = 30):
    """Add ticker:signal to suppressed list."""
    if 'suppressed' not in actioned:
        actioned['suppressed'] = []
    
    expires = (datetime.now() + timedelta(days=suppress_days)).strftime("%Y-%m-%d")
    
    # Remove existing entry for same ticker:signal
    actioned['suppressed'] = [
        e for e in actioned['suppressed']
        if not (e.get('ticker') == ticker and e.get('signal') == signal)
    ]
    
    # Add new entry
    actioned['suppressed'].append({
        'ticker': ticker,
        'signal': signal,
        'actioned_date': datetime.now().strftime("%Y-%m-%d"),
        'expires': expires,
    })


def move_ticker(portfolio: dict, watchlist: dict, ticker: str, from_list: str):
    """
    Move ticker between lists based on action.
    - SELL: portfolio -> watchlist
    - BUY: watchlist -> portfolio
    """
    if from_list == 'portfolio':
        # Remove from portfolio, add to watchlist
        if ticker in portfolio.get('tickers', []):
            portfolio['tickers'].remove(ticker)
        if ticker not in watchlist.get('tickers', []):
            watchlist.setdefault('tickers', []).append(ticker)
    else:
        # Remove from watchlist, add to portfolio
        if ticker in watchlist.get('tickers', []):
            watchlist['tickers'].remove(ticker)
        if ticker not in portfolio.get('tickers', []):
            portfolio.setdefault('tickers', []).append(ticker)


def handle_action(title: str, config_dir: Path):
    """
    Main handler for ACTIONED issues.
    
    Args:
        title: Issue title like "ACTIONED:NVDA:SELL_ALERT"
        config_dir: Path to config directory
    """
    parsed = parse_action_title(title)
    if not parsed:
        logger.error(f"Invalid action title: {title}")
        return False
    
    ticker, signal = parsed
    logger.info(f"Processing action: ticker={ticker}, signal={signal}")
    
    # Load files
    portfolio_path = config_dir / "portfolio.json"
    watchlist_path = config_dir / "watchlist.json"
    actioned_path = config_dir / "actioned.json"
    
    portfolio = load_json(portfolio_path)
    watchlist = load_json(watchlist_path)
    actioned = load_json(actioned_path)
    
    # Add to suppressed
    add_to_actioned(actioned, ticker, signal)
    save_json(actioned_path, actioned)
    logger.info(f"Added {ticker}:{signal} to actioned.json (30-day suppression)")
    
    # Move ticker based on signal type
    is_sell = signal.startswith("SELL")
    is_buy = signal.startswith("BUY")
    
    in_portfolio = ticker in portfolio.get('tickers', [])
    in_watchlist = ticker in watchlist.get('tickers', [])
    
    if is_sell and in_portfolio:
        move_ticker(portfolio, watchlist, ticker, 'portfolio')
        logger.info(f"Moved {ticker}: portfolio -> watchlist")
    elif is_buy and in_watchlist:
        move_ticker(portfolio, watchlist, ticker, 'watchlist')
        logger.info(f"Moved {ticker}: watchlist -> portfolio")
    
    # Save updated lists
    save_json(portfolio_path, portfolio)
    save_json(watchlist_path, watchlist)
    
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python handle_action.py 'ACTIONED:TICKER:SIGNAL'")
        sys.exit(1)
    
    title = sys.argv[1]
    config_dir = Path(__file__).parent.parent / "config"
    
    success = handle_action(title, config_dir)
    sys.exit(0 if success else 1)
