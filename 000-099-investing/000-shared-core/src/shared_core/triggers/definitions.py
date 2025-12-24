"""
Signal definitions for portfolio and watchlist alerts.

Defines conditions, cooldowns, and actions for each signal type.
"""

from typing import Dict, Any

# Portfolio signals - for stocks you already own
PORTFOLIO_SIGNALS: Dict[str, Dict[str, Any]] = {
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

# Watchlist signals - for stocks you're watching to buy
WATCHLIST_SIGNALS: Dict[str, Dict[str, Any]] = {
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

# All signals combined - for running all alerts on all tickers
ALL_SIGNALS: Dict[str, Dict[str, Any]] = {
    **PORTFOLIO_SIGNALS,
    **WATCHLIST_SIGNALS,
}

