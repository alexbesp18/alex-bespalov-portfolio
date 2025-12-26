"""Oversold Scorer — Weighted scoring for oversold stock detection.

This module computes a 1-10 oversold score based on 6 key technical indicators.
Each indicator is scored individually and combined using configurable weights.

Now uses shared_core.scoring for most component scoring functions.

Indicators and Weights:
    - RSI (30%): Relative Strength Index, oversold below 30
    - Williams %R (20%): Momentum oscillator, oversold below -80
    - Stochastic %K (15%): Price momentum, oversold below 20
    - Bollinger Position (15%): Price vs lower band
    - SMA200 Distance (10%): How far below the 200-day moving average
    - Consecutive Red Days (10%): Sequential down days

Example:
    >>> from src.oversold_scorer import OversoldScorer
    >>> scorer = OversoldScorer()
    >>> result = scorer.score(df)
    >>> print(f"Score: {result.final_score}")
"""

from typing import Dict, Optional

import pandas as pd

from .models import OversoldScore

# Import scoring functions from shared_core
from shared_core.scoring.components import (
    score_rsi_oversold,
    score_williams_r_oversold,
    score_stochastic_oversold,
    score_bollinger_position,
    score_sma200_distance,
    score_consecutive_red,
)
from shared_core.scoring.weights import OVERSOLD_WEIGHTS as WEIGHTS

# Alias for backward compatibility with local code
score_rsi = score_rsi_oversold
score_williams_r = score_williams_r_oversold
score_stochastic = score_stochastic_oversold


# =============================================================================
# MAIN SCORER CLASS
# =============================================================================

class OversoldScorer:
    """Computes oversold score (1-10) based on technical indicators.
    
    The scorer uses 6 weighted indicators to compute a composite score.
    Higher scores indicate more oversold conditions.
    
    Attributes:
        weights: Dictionary mapping indicator names to their weights.
        
    Example:
        >>> scorer = OversoldScorer()
        >>> result = scorer.score(df)
        >>> if result.final_score >= 7.0:
        ...     print("Significantly oversold!")
    """
    
    def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
        """Initialize the scorer with optional custom weights.
        
        Args:
            weights: Optional custom weights. Must sum to 1.0.
                     Defaults to module-level WEIGHTS if not provided.
        """
        self.weights = weights or WEIGHTS
    
    def score(self, df: pd.DataFrame) -> OversoldScore:
        """Calculate the oversold score for a DataFrame.
        
        Args:
            df: DataFrame with calculated technical indicators.
                Required columns: RSI, WILLIAMS_R, STOCH_K, close,
                BB_LOWER, BB_MIDDLE, SMA_200.
        
        Returns:
            OversoldScore with final_score, components breakdown,
            and raw indicator values.
            
        Raises:
            Returns zero score if df is None or has insufficient data.
        """
        if df is None or len(df) < 50:
            return OversoldScore(
                final_score=0.0,
                components={},
                raw_values={},
            )
        
        curr = df.iloc[-1]
        
        # Calculate 52-week high and % off high
        high_52w = float(df['high'].max()) if 'high' in df.columns else 0
        close_price = float(curr.get("close", 0) or 0)
        pct_from_high = ((high_52w - close_price) / high_52w * 100) if high_52w > 0 else 0
        
        # Extract raw values with safe defaults
        raw = {
            "rsi": float(curr.get("RSI", 50) or 50),
            "williams_r": float(curr.get("WILLIAMS_R", -50) or -50),
            "stoch_k": float(curr.get("STOCH_K", 50) or 50),
            "close": close_price,
            "bb_lower": float(curr.get("BB_LOWER", 0) or 0),
            "bb_middle": float(curr.get("BB_MIDDLE", 0) or 0),
            "sma200": float(curr.get("SMA_200", 0) or 0),
            "high_52w": high_52w,
            "pct_from_high": pct_from_high,
        }
        
        # Calculate component scores
        components = {
            "rsi": score_rsi(raw["rsi"]),
            "williams_r": score_williams_r(raw["williams_r"]),
            "stochastic": score_stochastic(raw["stoch_k"]),
            "bollinger": score_bollinger_position(
                raw["close"], raw["bb_lower"], raw["bb_middle"]
            ),
            "sma200_distance": score_sma200_distance(raw["close"], raw["sma200"]),
            "consecutive_red": score_consecutive_red(df),
        }
        
        # Compute weighted sum
        total = sum(
            components[key] * self.weights[key]
            for key in self.weights
        )
        
        # Clamp to valid range
        final_score = max(1.0, min(10.0, total))
        
        return OversoldScore(
            final_score=round(final_score, 1),
            components=components,
            raw_values={k: round(v, 2) for k, v in raw.items()},
        )
