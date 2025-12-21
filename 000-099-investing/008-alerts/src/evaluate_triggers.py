"""
evaluate_triggers.py — Signal evaluation with multi-condition logic.

PORTFOLIO Signals:
- BUY_MORE_PULLBACK, BUY_MORE_BREAKOUT
- SELL_WARNING, SELL_WATCH, SELL_ALERT

WATCHLIST Signals:
- BUY_REVERSAL, BUY_OVERSOLD_BOUNCE, BUY_PULLBACK, BUY_BREAKOUT
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


# Signal definitions per spec
PORTFOLIO_SIGNALS = {
    'BUY_MORE_PULLBACK': {
        'conditions': {
            'above_SMA200': True,
            'rsi_min': 40,
            'rsi_max': 55,
            'score_min': 8,
        },
        'cooldown_days': 5,
        'action': 'BUY',
        'description': 'Add to winner on healthy pullback',
    },
    'BUY_MORE_BREAKOUT': {
        'conditions': {
            'above_SMA200': True,
            'rsi_crosses_above_60': True,
            'rsi_max': 75,
            'score_min': 8,
            'new_20day_high': True,
            'volume_above_1.5x_avg': True,
        },
        'cooldown_days': 10,
        'action': 'BUY',
        'description': 'Add on confirmed breakout with volume',
    },
    'SELL_WARNING': {
        'conditions': {
            'crosses_below_SMA200': True,
            'score_max': 5,
        },
        'cooldown_days': 0,  # Event-based, no cooldown
        'action': 'SELL',
        'description': 'Early alert on trend break',
    },
    'SELL_WATCH': {
        'conditions': {
            'below_SMA200': True,
            'score_max': 4,
        },
        'cooldown_days': 5,
        'action': 'SELL',
        'description': 'Sustained weakness below trend',
    },
    'SELL_ALERT': {
        'conditions': {
            'below_SMA200': True,
            'rsi_max': 35,
            'score_max': 4,
        },
        'cooldown_days': 5,
        'action': 'SELL',
        'description': 'Act soon — momentum confirming breakdown',
    },
}

WATCHLIST_SIGNALS = {
    'BUY_REVERSAL': {
        'conditions': {
            'crosses_above_SMA200': True,
            'rsi_min': 50,
            'score_min': 6,
        },
        'cooldown_days': 0,  # Event-based
        'action': 'BUY',
        'description': 'Catch the turn back into uptrend',
    },
    'BUY_OVERSOLD_BOUNCE': {
        'conditions': {
            'rsi_crosses_above_30': True,
            'above_SMA50': True,
            'score_min': 5,
        },
        'cooldown_days': 0,  # Event-based
        'action': 'BUY',
        'description': 'Mean reversion from oversold',
    },
    'BUY_PULLBACK': {
        'conditions': {
            'above_SMA200': True,
            'rsi_min': 40,
            'rsi_max': 50,
            'score_min': 7,
        },
        'cooldown_days': 5,
        'action': 'BUY',
        'description': 'Enter on dip in established uptrend',
    },
    'BUY_BREAKOUT': {
        'conditions': {
            'above_SMA200': True,
            'rsi_crosses_above_60': True,
            'rsi_max': 75,
            'score_min': 8,
            'new_20day_high': True,
            'volume_above_1.5x_avg': True,
        },
        'cooldown_days': 10,
        'action': 'BUY',
        'description': 'Join momentum breakout',
    },
}


def check_conditions(flags: Dict[str, Any], conditions: Dict[str, Any]) -> bool:
    """
    Check if all conditions are met.
    
    Condition types:
    - Boolean flags: exact match
    - rsi_min/rsi_max: RSI range
    - score_min/score_max: Score range
    """
    rsi = flags.get('rsi', 50)
    score = flags.get('score', 0)
    
    for key, expected in conditions.items():
        if key == 'rsi_min':
            if rsi < expected:
                return False
        elif key == 'rsi_max':
            if rsi > expected:
                return False
        elif key == 'score_min':
            if score < expected:
                return False
        elif key == 'score_max':
            if score > expected:
                return False
        else:
            # Boolean flag
            if flags.get(key) != expected:
                return False
    
    return True


def is_in_cooldown(signal_key: str, cooldowns: Dict[str, str], cooldown_days: int) -> bool:
    """Check if a signal is in cooldown period."""
    if cooldown_days == 0:
        return False
    
    expiry_str = cooldowns.get(signal_key)
    if not expiry_str:
        return False
    
    try:
        expiry = datetime.fromisoformat(expiry_str)
        return datetime.now() < expiry
    except ValueError:
        return False


def is_suppressed(ticker: str, signal_name: str, actioned: Dict[str, Any]) -> bool:
    """Check if a signal is suppressed via actioned.json."""
    suppressed = actioned.get('suppressed', [])
    today = datetime.now().date()
    
    for entry in suppressed:
        if entry.get('ticker') != ticker or entry.get('signal') != signal_name:
            continue
        
        expires_str = entry.get('expires')
        if expires_str:
            try:
                expires = datetime.fromisoformat(expires_str).date()
                if today < expires:
                    return True
            except ValueError:
                pass
    
    return False


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


def update_cooldowns(cooldowns: Dict[str, str], triggered_signals: List[Dict[str, Any]]) -> Dict[str, str]:
    """Update cooldowns for triggered signals."""
    for signal in triggered_signals:
        cooldown_days = signal.get('cooldown_days', 0)
        if cooldown_days > 0:
            signal_key = signal['signal_key']
            expiry = datetime.now() + timedelta(days=cooldown_days)
            cooldowns[signal_key] = expiry.isoformat()
    return cooldowns


if __name__ == "__main__":
    # Test
    print("Signal definitions loaded:")
    print(f"Portfolio: {list(PORTFOLIO_SIGNALS.keys())}")
    print(f"Watchlist: {list(WATCHLIST_SIGNALS.keys())}")
