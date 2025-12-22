"""
Divergence detection algorithms.

Detects price/indicator divergences that may signal trend reversals.
"""

import pandas as pd

from ..scoring.models import DivergenceType, DivergenceResult
from .swing_points import find_swing_lows, find_swing_highs


def detect_divergence_enhanced(
    df: pd.DataFrame,
    lookback: int = 14,
    indicator: str = "RSI",
) -> DivergenceResult:
    """
    Enhanced divergence detection using actual swing points.
    
    Bullish divergence: Price makes lower low, indicator makes higher low
    Bearish divergence: Price makes higher high, indicator makes lower high
    
    Args:
        df: DataFrame with price and indicator data
        lookback: Number of bars to analyze
        indicator: Indicator column name ("RSI" or "OBV")
        
    Returns:
        DivergenceResult with type, strength, and description
        
    Example:
        >>> div = detect_divergence_enhanced(df, lookback=14, indicator="RSI")
        >>> if div.type == DivergenceType.BULLISH:
        ...     print("Bullish divergence detected!")
    """
    if len(df) < lookback:
        return DivergenceResult.none("Insufficient data")

    window = df.iloc[-lookback:]
    prices = window['close']

    ind_col = 'RSI' if indicator == "RSI" else ('OBV' if indicator == "OBV" else indicator)

    if ind_col not in window.columns:
        return DivergenceResult.none(f"{indicator} not available")

    ind_series = window[ind_col]

    # Find swing lows for bullish divergence
    price_lows = find_swing_lows(prices)

    if len(price_lows.dropna()) >= 2:
        p_lows = price_lows.dropna()
        p1_idx, p2_idx = p_lows.index[-2], p_lows.index[-1]
        p1, p2 = p_lows.iloc[-2], p_lows.iloc[-1]

        r1 = ind_series.loc[p1_idx] if p1_idx in ind_series.index else None
        r2 = ind_series.loc[p2_idx] if p2_idx in ind_series.index else None

        if r1 is not None and r2 is not None:
            if p2 < p1 and r2 > r1:
                strength = abs(r2 - r1)
                pct_price_drop = ((p1 - p2) / p1) * 100 if p1 != 0 else 0
                return DivergenceResult.bullish(
                    strength,
                    f"Bullish: Price -{pct_price_drop:.1f}%, {indicator} +{strength:.1f}"
                )

    # Find swing highs for bearish divergence
    price_highs = find_swing_highs(prices)

    if len(price_highs.dropna()) >= 2:
        p_highs = price_highs.dropna()
        p1_idx, p2_idx = p_highs.index[-2], p_highs.index[-1]
        p1, p2 = p_highs.iloc[-2], p_highs.iloc[-1]

        r1 = ind_series.loc[p1_idx] if p1_idx in ind_series.index else None
        r2 = ind_series.loc[p2_idx] if p2_idx in ind_series.index else None

        if r1 is not None and r2 is not None:
            if p2 > p1 and r2 < r1:
                strength = abs(r1 - r2)
                pct_price_rise = ((p2 - p1) / p1) * 100 if p1 != 0 else 0
                return DivergenceResult.bearish(
                    strength,
                    f"Bearish: Price +{pct_price_rise:.1f}%, {indicator} -{strength:.1f}"
                )

    return DivergenceResult.none("No divergence detected")


def detect_combined_divergence(
    df: pd.DataFrame,
    lookback: int = 14,
) -> DivergenceResult:
    """
    Check both RSI and OBV for divergence.
    
    Returns stronger signal if both agree (1.5x confluence bonus).
    
    Args:
        df: DataFrame with RSI and OBV columns
        lookback: Number of bars to analyze
        
    Returns:
        DivergenceResult with combined strength if both agree
    """
    rsi_div = detect_divergence_enhanced(df, lookback, "RSI")
    obv_div = detect_divergence_enhanced(df, lookback, "OBV")

    # Both bullish - confluence bonus
    if rsi_div.type == DivergenceType.BULLISH and obv_div.type == DivergenceType.BULLISH:
        combined_strength = (rsi_div.strength + obv_div.strength) / 2
        return DivergenceResult.bullish(
            combined_strength * 1.5,
            "STRONG Bullish (RSI + OBV confirmed)"
        )

    # Both bearish - confluence bonus
    if rsi_div.type == DivergenceType.BEARISH and obv_div.type == DivergenceType.BEARISH:
        combined_strength = (rsi_div.strength + obv_div.strength) / 2
        return DivergenceResult.bearish(
            combined_strength * 1.5,
            "STRONG Bearish (RSI + OBV confirmed)"
        )

    # Single signal
    if rsi_div.type != DivergenceType.NONE:
        return rsi_div
    if obv_div.type != DivergenceType.NONE:
        return obv_div

    return DivergenceResult.none("No divergence")


def detect_rsi_divergence(
    df: pd.DataFrame,
    lookback: int = 14,
) -> str:
    """
    Simple RSI divergence detection.
    
    Args:
        df: DataFrame with 'close' and 'RSI' columns
        lookback: Number of bars to analyze
        
    Returns:
        'bullish', 'bearish', or 'none'
    """
    if len(df) < lookback + 5:
        return 'none'

    recent = df.iloc[-lookback:]
    price_start = recent['close'].iloc[0]
    price_end = recent['close'].iloc[-1]
    rsi_start = recent['RSI'].iloc[0] if 'RSI' in recent.columns else 50
    rsi_end = recent['RSI'].iloc[-1] if 'RSI' in recent.columns else 50

    # Bullish divergence: price makes lower low, RSI makes higher low
    if price_end < price_start and rsi_end > rsi_start:
        return 'bullish'
    # Bearish divergence: price makes higher high, RSI makes lower high
    elif price_end > price_start and rsi_end < rsi_start:
        return 'bearish'
    return 'none'


def detect_obv_divergence(
    df: pd.DataFrame,
    lookback: int = 14,
) -> str:
    """
    Simple OBV divergence detection.
    
    Args:
        df: DataFrame with 'close' and 'OBV' columns
        lookback: Number of bars to analyze
        
    Returns:
        'bullish', 'bearish', or 'none'
    """
    if len(df) < lookback + 5 or 'OBV' not in df.columns:
        return 'none'

    recent = df.iloc[-lookback:]
    price_start = recent['close'].iloc[0]
    price_end = recent['close'].iloc[-1]
    obv_start = recent['OBV'].iloc[0]
    obv_end = recent['OBV'].iloc[-1]

    # Bullish divergence: price makes lower low, OBV makes higher low (accumulation)
    if price_end < price_start and obv_end > obv_start:
        return 'bullish'
    # Bearish divergence: price makes higher high, OBV makes lower high (distribution)
    elif price_end > price_start and obv_end < obv_start:
        return 'bearish'
    return 'none'

