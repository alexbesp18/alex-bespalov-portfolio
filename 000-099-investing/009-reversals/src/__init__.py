"""
009-reversals source module.

Re-exports commonly used modules from shared_core for convenience.
Project-specific code remains in this package.
"""

# Re-export from shared_core
from shared_core import (
    # Data Processing
    TechnicalCalculator,
    CacheAwareFetcher,
    process_ohlcv_data,
    add_standard_indicators,
    calculate_matrix,
    calculate_bullish_score,
    # State Management
    StateManager,
    ArchiveManager,
    Digest,
    ArchiveEntry,
    safe_read_json,
    safe_write_json,
    utc_now_iso,
    parse_iso_datetime,
    # Scoring
    DivergenceType,
    DivergenceResult,
    ReversalScore,
    # Triggers
    TriggerEngine,
    # Utils
    get_cached_tickers,
    check_time_guard,
    setup_logging,
)

from shared_core.scoring.components import (
    score_rsi,
    score_stochastic,
    score_macd_histogram,
    score_price_vs_sma200,
    score_volume_spike,
    score_williams_r,
    score_divergence,
    score_consecutive_days,
    get_volume_multiplier,
    get_adx_multiplier,
)

from shared_core.divergence import (
    find_swing_lows,
    find_swing_highs,
    detect_divergence_enhanced,
    detect_combined_divergence,
)

# Project-specific imports
from .fetcher import TwelveDataFetcher
from .calculator import TechnicalCalculator as ReversalsTechnicalCalculator
from .reversal_calculator import ReversalCalculator
from .notifier import Notifier

__all__ = [
    # shared_core
    "TechnicalCalculator",
    "CacheAwareFetcher",
    "process_ohlcv_data",
    "add_standard_indicators",
    "calculate_matrix",
    "calculate_bullish_score",
    "StateManager",
    "ArchiveManager",
    "Digest",
    "ArchiveEntry",
    "safe_read_json",
    "safe_write_json",
    "utc_now_iso",
    "parse_iso_datetime",
    "DivergenceType",
    "DivergenceResult",
    "ReversalScore",
    "TriggerEngine",
    "get_cached_tickers",
    "check_time_guard",
    "setup_logging",
    # Scoring components
    "score_rsi",
    "score_stochastic",
    "score_macd_histogram",
    "score_price_vs_sma200",
    "score_volume_spike",
    "score_williams_r",
    "score_divergence",
    "score_consecutive_days",
    "get_volume_multiplier",
    "get_adx_multiplier",
    # Divergence
    "find_swing_lows",
    "find_swing_highs",
    "detect_divergence_enhanced",
    "detect_combined_divergence",
    # Project-specific
    "TwelveDataFetcher",
    "ReversalsTechnicalCalculator",
    "ReversalCalculator",
    "Notifier",
]

