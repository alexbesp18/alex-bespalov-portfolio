"""Oversold Scorer — Weighted scoring for oversold stock detection.

This module computes a 1-10 oversold score based on 6 key technical indicators.
Each indicator is scored individually and combined using configurable weights.

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

import numpy as np
import pandas as pd

from .models import OversoldScore


# =============================================================================
# SCORING WEIGHTS (configurable)
# =============================================================================

WEIGHTS: Dict[str, float] = {
    "rsi": 0.30,
    "williams_r": 0.20,
    "stochastic": 0.15,
    "bollinger": 0.15,
    "sma200_distance": 0.10,
    "consecutive_red": 0.10,
}


# =============================================================================
# COMPONENT SCORING FUNCTIONS
# =============================================================================

def score_rsi(rsi: float) -> float:
    """Score RSI value for oversold condition.
    
    Lower RSI indicates more oversold condition, resulting in higher score.
    
    Args:
        rsi: RSI value (0-100 range).
        
    Returns:
        Score from 1.0 to 10.0.
    """
    if pd.isna(rsi):
        return 0.0
    
    thresholds = [
        (15, 10.0),
        (20, 9.0),
        (25, 8.0),
        (30, 6.0),
        (35, 4.5),
        (40, 3.0),
        (50, 2.0),
    ]
    
    for threshold, score in thresholds:
        if rsi < threshold:
            return score
    return 1.0


def score_williams_r(williams_r: float) -> float:
    """Score Williams %R for oversold condition.
    
    Williams %R ranges from -100 to 0. Values below -80 indicate oversold.
    
    Args:
        williams_r: Williams %R value (-100 to 0 range).
        
    Returns:
        Score from 1.0 to 10.0.
    """
    if pd.isna(williams_r):
        return 0.0
    
    thresholds = [
        (-95, 10.0),
        (-90, 8.0),
        (-85, 6.0),
        (-80, 4.0),
        (-70, 2.0),
    ]
    
    for threshold, score in thresholds:
        if williams_r < threshold:
            return score
    return 1.0


def score_stochastic(stoch_k: float) -> float:
    """Score Stochastic %K for oversold condition.
    
    Lower %K indicates more oversold condition. Below 20 is typically oversold.
    
    Args:
        stoch_k: Stochastic %K value (0-100 range).
        
    Returns:
        Score from 1.0 to 10.0.
    """
    if pd.isna(stoch_k):
        return 0.0
    
    thresholds = [
        (5, 10.0),
        (10, 9.0),
        (15, 7.0),
        (20, 5.0),
        (30, 3.0),
    ]
    
    for threshold, score in thresholds:
        if stoch_k < threshold:
            return score
    return 1.0


def score_bollinger_position(
    close: float,
    bb_lower: float,
    bb_middle: float,
) -> float:
    """Score price position relative to Bollinger Bands.
    
    Price below lower band indicates potential oversold condition.
    
    Args:
        close: Current closing price.
        bb_lower: Lower Bollinger Band value.
        bb_middle: Middle Bollinger Band (SMA20).
        
    Returns:
        Score from 1.0 to 10.0.
    """
    if pd.isna(close) or pd.isna(bb_lower) or pd.isna(bb_middle) or bb_middle == 0:
        return 0.0
    
    band_width = bb_middle - bb_lower
    if band_width <= 0:
        return 1.0
    
    if close < bb_lower:
        # Below lower band — very oversold
        distance_below = (bb_lower - close) / band_width
        if distance_below > 0.5:
            return 10.0
        elif distance_below > 0.25:
            return 9.0
        return 8.0
    
    # Above lower band — check proximity
    distance_above = (close - bb_lower) / band_width
    thresholds = [
        (0.2, 6.0),
        (0.4, 4.0),
        (0.6, 2.0),
    ]
    
    for threshold, score in thresholds:
        if distance_above < threshold:
            return score
    return 1.0


def score_sma200_distance(close: float, sma200: float) -> float:
    """Score how far price is below SMA200.
    
    Deeper below the 200-day moving average indicates more oversold.
    
    Args:
        close: Current closing price.
        sma200: 200-day simple moving average.
        
    Returns:
        Score from 1.0 to 10.0.
    """
    if pd.isna(close) or pd.isna(sma200) or sma200 == 0:
        return 0.0
    
    pct_below = ((sma200 - close) / sma200) * 100
    
    thresholds = [
        (30, 10.0),
        (20, 9.0),
        (15, 7.0),
        (10, 5.0),
        (5, 3.0),
        (0, 2.0),
    ]
    
    for threshold, score in thresholds:
        if pct_below > threshold:
            return score
    return 1.0  # Above SMA200


def score_consecutive_red(df: pd.DataFrame) -> float:
    """Score based on consecutive down days.
    
    More consecutive red (down) days indicates sustained selling pressure.
    
    Args:
        df: DataFrame with 'close' column sorted by date ascending.
        
    Returns:
        Score from 1.0 to 10.0.
    """
    if df is None or len(df) < 2:
        return 0.0
    
    count = 0
    closes = df["close"].values
    for i in range(len(closes) - 1, 0, -1):
        if closes[i] < closes[i - 1]:
            count += 1
        else:
            break
    
    thresholds = [
        (7, 10.0),
        (6, 9.0),
        (5, 7.0),
        (4, 5.0),
        (3, 3.0),
        (2, 2.0),
    ]
    
    for threshold, score in thresholds:
        if count >= threshold:
            return score
    return 1.0


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
        
        # Extract raw values with safe defaults
        raw = {
            "rsi": float(curr.get("RSI", 50) or 50),
            "williams_r": float(curr.get("WILLIAMS_R", -50) or -50),
            "stoch_k": float(curr.get("STOCH_K", 50) or 50),
            "close": float(curr.get("close", 0) or 0),
            "bb_lower": float(curr.get("BB_LOWER", 0) or 0),
            "bb_middle": float(curr.get("BB_MIDDLE", 0) or 0),
            "sma200": float(curr.get("SMA_200", 0) or 0),
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
