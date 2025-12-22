"""
Scoring engines and component scorers for technical analysis.

Provides:
- Models: ReversalScore, OversoldScore, DivergenceResult, DivergenceType
- Component scorers: score_rsi, score_stochastic, score_macd_histogram, etc.
- Volume and ADX multipliers
- Reversal and oversold composite scorers
"""

from .models import (
    DivergenceType,
    DivergenceResult,
    ReversalScore,
    OversoldScore,
)
from .components import (
    # RSI scoring
    score_rsi,
    score_rsi_oversold,
    # Stochastic scoring
    score_stochastic,
    score_stochastic_oversold,
    # MACD scoring
    score_macd_histogram,
    # Price vs MA scoring
    score_price_vs_sma200,
    # Volume scoring
    score_volume_spike,
    get_volume_multiplier,
    get_volume_ratio,
    # Williams %R scoring
    score_williams_r,
    score_williams_r_oversold,
    # Divergence scoring
    score_divergence,
    # Consecutive days scoring
    score_consecutive_days,
    score_consecutive_red,
    # Bollinger scoring
    score_bollinger_position,
    # SMA distance scoring
    score_sma200_distance,
    # ADX multiplier
    get_adx_multiplier,
)
from .weights import (
    REVERSAL_WEIGHTS,
    OVERSOLD_WEIGHTS,
    BULLISH_WEIGHTS,
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

