"""
Scoring engines and component scorers for technical analysis.

Provides:
- Models: ReversalScore, OversoldScore, DivergenceResult, DivergenceType
- Component scorers: score_rsi, score_stochastic, score_macd_histogram, etc.
- Volume and ADX multipliers
- Reversal and oversold composite scorers
"""

from .components import (
    # ADX multiplier
    get_adx_multiplier,
    get_volume_multiplier,
    get_volume_ratio,
    # Bollinger scoring
    score_bollinger_position,
    # Consecutive days scoring
    score_consecutive_days,
    score_consecutive_red,
    # Divergence scoring
    score_divergence,
    # MACD scoring
    score_macd_histogram,
    # Price vs MA scoring
    score_price_vs_sma200,
    # RSI scoring
    score_rsi,
    score_rsi_oversold,
    # SMA distance scoring
    score_sma200_distance,
    # Stochastic scoring
    score_stochastic,
    score_stochastic_oversold,
    # Volume scoring
    score_volume_spike,
    # Williams %R scoring
    score_williams_r,
    score_williams_r_oversold,
)
from .models import (
    DivergenceResult,
    DivergenceType,
    OversoldScore,
    ReversalScore,
)
from .weights import (
    BULLISH_WEIGHTS,
    OVERSOLD_WEIGHTS,
    REVERSAL_WEIGHTS,
)

__all__ = [
    # Models
    "DivergenceType",
    "DivergenceResult",
    "ReversalScore",
    "OversoldScore",
    # Component scorers
    "score_rsi",
    "score_rsi_oversold",
    "score_stochastic",
    "score_stochastic_oversold",
    "score_macd_histogram",
    "score_price_vs_sma200",
    "score_volume_spike",
    "score_williams_r",
    "score_williams_r_oversold",
    "score_divergence",
    "score_consecutive_days",
    "score_consecutive_red",
    "score_bollinger_position",
    "score_sma200_distance",
    # Multipliers
    "get_volume_multiplier",
    "get_volume_ratio",
    "get_adx_multiplier",
    # Weights
    "REVERSAL_WEIGHTS",
    "OVERSOLD_WEIGHTS",
    "BULLISH_WEIGHTS",
]

