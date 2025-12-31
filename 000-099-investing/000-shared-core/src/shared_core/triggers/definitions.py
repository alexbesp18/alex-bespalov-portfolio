"""
Signal definitions for portfolio and watchlist alerts — TIGHTENED v3.

Defines conditions, cooldowns, and actions for each signal type.

Key Changes:
- Raised score thresholds (BUY_REVERSAL: 6→8, BUY_OVERSOLD_BOUNCE: 5→7)
- Added volume requirements for buy signals
- Added conviction level filter (HIGH only for most actionable signals)
- Tightened RSI ranges
"""

from typing import Any, Dict

# Portfolio signals - for stocks you already own
PORTFOLIO_SIGNALS: Dict[str, Dict[str, Any]] = {
    'BUY_MORE_PULLBACK': {
        'conditions': {
            'above_SMA200': True,
            'rsi_min': 35,           # Tightened from 40 - want more pullback
            'rsi_max': 50,           # Tightened from 55
            'score_min': 8,
            'volume_min': 1.0,       # NEW: require at least average volume
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
            'volume_min': 1.5,       # Require 1.5x volume for breakout
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
# TIGHTENED: All BUY signals now require higher scores and volume
WATCHLIST_SIGNALS: Dict[str, Dict[str, Any]] = {
    'BUY_REVERSAL': {
        'conditions': {
            'crosses_above_SMA200': True,
            'rsi_min': 45,           # Tightened from 50 - want recovery momentum
            'score_min': 8,          # TIGHTENED from 6
            'volume_min': 1.2,       # NEW: require above-average volume
            'conviction': 'HIGH',    # NEW: require HIGH conviction
        },
        'cooldown_days': 0,  # Event-based
        'action': 'BUY',
        'description': 'Catch the turn back into uptrend (HIGH conviction only)',
    },
    'BUY_OVERSOLD_BOUNCE': {
        'conditions': {
            'rsi_crosses_above_30': True,
            'above_SMA50': True,
            'score_min': 7,          # TIGHTENED from 5
            'volume_min': 1.0,       # NEW: require at least average volume
        },
        'cooldown_days': 0,  # Event-based
        'action': 'BUY',
        'description': 'Mean reversion from oversold',
    },
    'BUY_PULLBACK': {
        'conditions': {
            'above_SMA200': True,
            'rsi_min': 35,           # Tightened from 40
            'rsi_max': 45,           # Tightened from 50
            'score_min': 8,          # TIGHTENED from 7
            'volume_min': 1.0,       # NEW
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
            'volume_min': 1.5,       # Require strong volume
        },
        'cooldown_days': 10,
        'action': 'BUY',
        'description': 'Join momentum breakout',
    },
}

# HIGH conviction reversal signal - THE actionable BUY NOW signal
REVERSAL_SIGNALS: Dict[str, Dict[str, Any]] = {
    'UPSIDE_REVERSAL_HIGH': {
        'conditions': {
            'reversal_score_min': 8.0,
            'conviction': 'HIGH',
            'volume_min': 1.2,
            'adx_max': 35,
        },
        'cooldown_days': 7,
        'action': 'BUY',
        'description': 'HIGH conviction upside reversal — BUY NOW',
    },
    'DOWNSIDE_REVERSAL_HIGH': {
        'conditions': {
            'reversal_score_min': 8.0,
            'conviction': 'HIGH',
            'volume_min': 1.2,
            'adx_max': 35,
        },
        'cooldown_days': 7,
        'action': 'SELL',
        'description': 'HIGH conviction downside reversal — SELL NOW',
    },
}

# All signals combined - for running all alerts on all tickers
ALL_SIGNALS: Dict[str, Dict[str, Any]] = {
    **PORTFOLIO_SIGNALS,
    **WATCHLIST_SIGNALS,
    **REVERSAL_SIGNALS,
}

# Default filters for different modes
SIGNAL_FILTERS = {
    'actionable_only': {
        'conviction_min': 'HIGH',
        'volume_min': 1.2,
    },
    'developing': {
        'conviction_min': 'MEDIUM',
        'volume_min': 1.0,
    },
    'all': {
        'conviction_min': 'LOW',
        'volume_min': 0.0,
    },
}
