"""
Scoring weight presets for different analysis types.

Each preset defines how much weight each indicator contributes
to the final composite score.
"""

from typing import Dict

# Reversal scoring weights (used in 009-reversals)
REVERSAL_WEIGHTS: Dict[str, float] = {
    'rsi': 0.20,
    'stochastic': 0.15,
    'macd_hist': 0.15,
    'price_sma200': 0.15,
    'volume': 0.10,
    'divergence': 0.15,
    'consecutive': 0.05,
    'williams_r': 0.05,
}

# Oversold scoring weights (used in 010-oversold)
OVERSOLD_WEIGHTS: Dict[str, float] = {
    "rsi": 0.30,
    "williams_r": 0.20,
    "stochastic": 0.15,
    "bollinger": 0.15,
    "sma200_distance": 0.10,
    "consecutive_red": 0.10,
}

# Bullish scoring weights (used in 008-alerts, 009-reversals, 010-oversold)
BULLISH_WEIGHTS: Dict[str, float] = {
    'trend': 0.25,      # Price vs SMAs
    'ma_stack': 0.20,   # 20>50>200 ordering
    'macd': 0.15,       # MACD histogram
    'rsi': 0.15,        # RSI position
    'obv': 0.15,        # OBV trend
    'adx': 0.10,        # ADX strength
}

