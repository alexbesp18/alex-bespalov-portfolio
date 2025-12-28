"""
Divergence detection utilities.

Provides:
- Swing point detection (highs and lows)
- RSI and OBV divergence detection
- Combined divergence with confluence bonus
"""

# Re-export models from scoring
from ..scoring.models import DivergenceResult, DivergenceType
from .divergence import (
    detect_combined_divergence,
    detect_divergence_enhanced,
    detect_obv_divergence,
    detect_rsi_divergence,
)
from .swing_points import (
    find_swing_highs,
    find_swing_lows,
    find_swing_points,
    get_recent_swing_highs,
    get_recent_swing_lows,
)

__all__ = [
    # Models
    "DivergenceType",
    "DivergenceResult",
    # Swing points
    "find_swing_lows",
    "find_swing_highs",
    "find_swing_points",
    "get_recent_swing_lows",
    "get_recent_swing_highs",
    # Divergence detection
    "detect_divergence_enhanced",
    "detect_combined_divergence",
    "detect_rsi_divergence",
    "detect_obv_divergence",
]

