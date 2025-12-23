"""
Data processing utilities for OHLCV data.

Provides:
- process_ohlcv: Convert API response to DataFrame with indicators
- calculate_matrix: Generate binary flags for dashboards
- calculate_bullish_score: Compute 1-10 bullish score
- bollinger_bands_with_width: Bollinger Bands with bandwidth
"""

from .process_ohlcv import (
    process_ohlcv_data,
    add_standard_indicators,
    bollinger_bands_with_width,
)
from .flags_matrix import calculate_matrix, filter_by_flags
from .bullish_score import (
    calculate_bullish_score,
    calculate_bullish_score_detailed,
)

__all__ = [
    "process_ohlcv_data",
    "add_standard_indicators",
    "bollinger_bands_with_width",
    "calculate_matrix",
    "filter_by_flags",
    "calculate_bullish_score",
    "calculate_bullish_score_detailed",
]

