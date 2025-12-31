"""
Configuration module for shared_core.

Provides centralized constants and configuration values.
"""

from .constants import (
    CACHE_CONFIG,
    DEFAULT_PERIODS,
    RATE_LIMITS,
    RSI_THRESHOLDS,
    SCORING_WEIGHTS,
    STOCHASTIC_THRESHOLDS,
    TREND_THRESHOLDS,
    VOLATILITY_THRESHOLDS,
    # Cache
    CacheConfig,
    # Default periods
    DefaultPeriods,
    # Rate limiting
    RateLimits,
    # RSI
    RSIThresholds,
    # Scoring
    ScoringWeights,
    # Stochastic
    StochasticThresholds,
    # Trend analysis
    TrendThresholds,
    # Volatility
    VolatilityThresholds,
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
