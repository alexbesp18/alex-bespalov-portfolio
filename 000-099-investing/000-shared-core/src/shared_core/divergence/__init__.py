"""
Divergence detection utilities.

Provides:
- Swing point detection (highs and lows)
- RSI and OBV divergence detection
- Combined divergence with confluence bonus
"""

from .swing_points import (
    find_swing_lows,
    find_swing_highs,
    find_swing_points,
    get_recent_swing_lows,
    get_recent_swing_highs,
)
from .divergence import (
    detect_divergence_enhanced,
    detect_combined_divergence,
    detect_rsi_divergence,
    detect_obv_divergence,
)

# Re-export models from scoring
from ..scoring.models import DivergenceType, DivergenceResult

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

