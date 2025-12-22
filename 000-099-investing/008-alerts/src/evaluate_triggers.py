"""
evaluate_triggers.py — Signal evaluation with multi-condition logic.

Uses shared_core.triggers for core logic, this module provides
backward-compatible wrapper for 008-alerts.
"""

import logging
from typing import Dict, List, Any, Optional

# Import from shared_core
from shared_core.triggers.definitions import (
    PORTFOLIO_SIGNALS,
    WATCHLIST_SIGNALS,
)
from shared_core.triggers.conditions import (
    check_conditions,
    is_in_cooldown,
    is_suppressed,
)

logger = logging.getLogger(__name__)


def evaluate_ticker(
    ticker: str,
    flags: Dict[str, Any],
    list_type: str,  # 'portfolio' or 'watchlist'
    cooldowns: Dict[str, str],
    actioned: Dict[str, Any],
    last_run_signals: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Evaluate all signals for a ticker.
    
    Returns list of triggered signals with metadata.
    """
    signals_def = PORTFOLIO_SIGNALS if list_type == 'portfolio' else WATCHLIST_SIGNALS
    results = []
    
    for signal_name, signal_config in signals_def.items():
        # Check conditions
        if not check_conditions(flags, signal_config['conditions']):
            continue
        
        signal_key = f"{ticker}:{signal_name}"
        
        # Check cooldown
        if is_in_cooldown(signal_key, cooldowns, signal_config['cooldown_days']):
            logger.debug(f"Skipping {signal_key}: in cooldown")
            continue
        
        # Check suppression
        if is_suppressed(ticker, signal_name, actioned):
            logger.debug(f"Skipping {signal_key}: suppressed via actioned")
            continue
        
        # Check deduplication (same signal fired last run)
        if last_run_signals and signal_key in last_run_signals:
            logger.debug(f"Skipping {signal_key}: duplicate from last run")
            continue
        
        # Signal triggered!
        results.append({
            'ticker': ticker,
            'signal': signal_name,
            'action': signal_config['action'],
            'description': signal_config['description'],
            'cooldown_days': signal_config['cooldown_days'],
            'signal_key': signal_key,
            'flags': {
                'rsi': flags.get('rsi'),
                'score': flags.get('score'),
                'close': flags.get('close'),
            },
        })
    
    return results


# Re-export update_cooldowns from shared_core
from shared_core.triggers.conditions import update_cooldowns


if __name__ == "__main__":
    # Test
    print("Signal definitions loaded:")
    print(f"Portfolio: {list(PORTFOLIO_SIGNALS.keys())}")
    print(f"Watchlist: {list(WATCHLIST_SIGNALS.keys())}")
