"""
Centralized configuration constants for shared_core.

This module provides named constants for magic numbers used throughout
the codebase. Constants are grouped by domain for easy discovery.

Usage:
    from shared_core.config.constants import TrendThresholds, RateLimits

    if price > sma200 * TrendThresholds.STRONG_UPTREND_MULTIPLIER:
        ...
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class RateLimits:
    """Rate limiting configuration for API calls."""

    # Twelve Data free tier limits
    TWELVE_DATA_REQUESTS_PER_MINUTE: int = 8
    TWELVE_DATA_DEFAULT_DELAY: float = 7.5  # 60 / 8 seconds

    # Retry configuration
    DEFAULT_RETRY_ATTEMPTS: int = 3
    RETRY_MIN_WAIT: int = 4
    RETRY_MAX_WAIT: int = 10


@dataclass(frozen=True)
class TrendThresholds:
    """Thresholds for trend classification."""

    # Price vs SMA200 thresholds
    STRONG_UPTREND_MULTIPLIER: float = 1.10  # price > sma200 * 1.10
    STRONG_DOWNTREND_MULTIPLIER: float = 0.90  # price < sma200 * 0.90

    # OBV trend thresholds
    OBV_UP_MULTIPLIER: float = 1.02  # obv > obv_sma * 1.02
    OBV_DOWN_MULTIPLIER: float = 0.98  # obv < obv_sma * 0.98


@dataclass(frozen=True)
class VolatilityThresholds:
    """Thresholds for volatility classification."""

    LOW_PERCENTILE: float = 0.25
    NORMAL_PERCENTILE: float = 0.50
    HIGH_PERCENTILE: float = 0.75
    # EXTREME is anything above HIGH_PERCENTILE


@dataclass(frozen=True)
class RSIThresholds:
    """RSI thresholds for overbought/oversold detection."""

    OVERSOLD: int = 30
    OVERBOUGHT: int = 70
    EXTREME_OVERSOLD: int = 20
    EXTREME_OVERBOUGHT: int = 80

    # For divergence detection
    BULLISH_DIVERGENCE_MAX: int = 40
    BEARISH_DIVERGENCE_MIN: int = 60


@dataclass(frozen=True)
class StochasticThresholds:
    """Stochastic %K thresholds."""

    OVERSOLD: int = 20
    OVERBOUGHT: int = 80


@dataclass(frozen=True)
class DefaultPeriods:
    """Default periods for technical indicators.

    Note: These are industry-standard defaults. Individual functions
    accept period parameters to override these when needed.
    """

    RSI: int = 14
    MACD_FAST: int = 12
    MACD_SLOW: int = 26
    MACD_SIGNAL: int = 9
    BOLLINGER: int = 20
    ATR: int = 14
    STOCH_K: int = 14
    STOCH_D: int = 3
    ADX: int = 14
    WILLIAMS_R: int = 14
    ROC: int = 14
    VWAP: int = 20
    OBV_SMA: int = 20

    # Moving averages
    SMA_SHORT: int = 20
    SMA_MEDIUM: int = 50
    SMA_LONG: int = 200


@dataclass(frozen=True)
class CacheConfig:
    """Cache configuration."""

    # Default data fetch size
    DEFAULT_OUTPUT_SIZE: int = 365

    # Relative paths to look for cache (from project root)
    CACHE_SUBDIRS: Tuple[str, ...] = (
        "007-ticker-analysis/data/twelve_data",
        "../007-ticker-analysis/data/twelve_data",
    )


@dataclass(frozen=True)
class ScoringWeights:
    """Weights for scoring calculations."""

    # Oversold score weights
    OVERSOLD_RSI: float = 0.30
    OVERSOLD_WILLIAMS: float = 0.20
    OVERSOLD_STOCH: float = 0.15
    OVERSOLD_BB: float = 0.15
    OVERSOLD_SMA200: float = 0.10
    OVERSOLD_RED_DAYS: float = 0.10

    # Reversal score weights
    REVERSAL_RSI: float = 0.20
    REVERSAL_STOCH: float = 0.15
    REVERSAL_STOCH_CROSS: float = 0.15
    REVERSAL_MACD: float = 0.20
    REVERSAL_VOLUME: float = 0.10
    REVERSAL_DIVERGENCE: float = 0.20


# Convenience exports for common use cases
RATE_LIMITS = RateLimits()
TREND_THRESHOLDS = TrendThresholds()
VOLATILITY_THRESHOLDS = VolatilityThresholds()
RSI_THRESHOLDS = RSIThresholds()
STOCHASTIC_THRESHOLDS = StochasticThresholds()
DEFAULT_PERIODS = DefaultPeriods()
CACHE_CONFIG = CacheConfig()
SCORING_WEIGHTS = ScoringWeights()
