"""Oversold Screener package.

A local CLI tool for ranking stocks by oversold score.

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
    # Scoring Models
    OversoldScore as SharedOversoldScore,
    # Utils
    get_cached_tickers,
    setup_logging,
)

from shared_core.scoring.components import (
    score_rsi_oversold,
    score_williams_r_oversold,
    score_stochastic_oversold,
    score_bollinger_position,
    score_sma200_distance,
    score_consecutive_red,
)

from shared_core.scoring.weights import OVERSOLD_WEIGHTS

from shared_core.models import (
    TickerResult as SharedTickerResult,
    Watchlist as SharedWatchlist,
    ScanConfig as SharedScanConfig,
    OutputFormat as SharedOutputFormat,
)

# Project-specific models (for backward compatibility, alias to shared_core)
from .models import OversoldScore, TickerResult, Watchlist, ScanConfig, OutputFormat
from .oversold_scorer import OversoldScorer
from .calculator import TechnicalCalculator  # Override shared_core version
from .fetcher import TwelveDataFetcher

__all__ = [
    # shared_core re-exports
    "TechnicalCalculator",
    "CacheAwareFetcher",
    "process_ohlcv_data",
    "add_standard_indicators",
    "calculate_matrix",
    "calculate_bullish_score",
    "get_cached_tickers",
    "setup_logging",
    # Scoring
    "OVERSOLD_WEIGHTS",
    "score_bollinger_position",
    "score_sma200_distance",
    "score_consecutive_red",
    # Project-specific
    "OversoldScore",
    "TickerResult",
    "Watchlist",
    "ScanConfig",
    "OutputFormat",
    "OversoldScorer",
    "TwelveDataFetcher",
]
