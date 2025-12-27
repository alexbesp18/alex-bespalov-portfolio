"""
Configuration module for shared_core.

Provides centralized constants and configuration values.
"""

from .constants import (
    # Rate limiting
    RateLimits,
    RATE_LIMITS,
    # Trend analysis
    TrendThresholds,
    TREND_THRESHOLDS,
    # Volatility
    VolatilityThresholds,
    VOLATILITY_THRESHOLDS,
    # RSI
    RSIThresholds,
    RSI_THRESHOLDS,
    # Stochastic
    StochasticThresholds,
    STOCHASTIC_THRESHOLDS,
    # Default periods
    DefaultPeriods,
    DEFAULT_PERIODS,
    # Cache
    CacheConfig,
    CACHE_CONFIG,
    # Scoring
    ScoringWeights,
    SCORING_WEIGHTS,
)

__all__ = [
    # Classes
    'RateLimits',
    'TrendThresholds',
    'VolatilityThresholds',
    'RSIThresholds',
    'StochasticThresholds',
    'DefaultPeriods',
    'CacheConfig',
    'ScoringWeights',
    # Instances
    'RATE_LIMITS',
    'TREND_THRESHOLDS',
    'VOLATILITY_THRESHOLDS',
    'RSI_THRESHOLDS',
    'STOCHASTIC_THRESHOLDS',
    'DEFAULT_PERIODS',
    'CACHE_CONFIG',
    'SCORING_WEIGHTS',
]
