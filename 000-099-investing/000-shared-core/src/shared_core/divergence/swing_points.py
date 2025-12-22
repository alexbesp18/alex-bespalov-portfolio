"""
Swing point detection utilities.

Identifies local minima (swing lows) and maxima (swing highs)
in price and indicator series.
"""

import pandas as pd
from typing import Dict


def find_swing_lows(series: pd.Series) -> pd.Series:
    """
    Find local minima (swing lows) in a series.
    
    A swing low is a point where the previous value is higher
    AND the next value is higher.
    
    Args:
        series: Price or indicator series
        
    Returns:
        Series containing only swing low values (others are NaN)
        
    Example:
        >>> lows = find_swing_lows(df['close'])
        >>> print(f"Found {lows.dropna().count()} swing lows")
    """
    swing_lows = series[(series.shift(1) > series) & (series.shift(-1) > series)]
    return swing_lows


def find_swing_highs(series: pd.Series) -> pd.Series:
    """
    Find local maxima (swing highs) in a series.
    
    A swing high is a point where the previous value is lower
    AND the next value is lower.
    
    Args:
        series: Price or indicator series
        
    Returns:
        Series containing only swing high values (others are NaN)
        
    Example:
        >>> highs = find_swing_highs(df['close'])
        >>> print(f"Found {highs.dropna().count()} swing highs")
    """
    swing_highs = series[(series.shift(1) < series) & (series.shift(-1) < series)]
    return swing_highs


def find_swing_points(series: pd.Series) -> Dict[str, pd.Series]:
    """
    Find both swing highs and lows in a series.
    
    Args:
        series: Price or indicator series
        
    Returns:
        Dict with 'highs' and 'lows' Series
        
    Example:
        >>> swings = find_swing_points(df['close'])
        >>> recent_low = swings['lows'].dropna().iloc[-1]
    """
    return {
        'highs': find_swing_highs(series),
        'lows': find_swing_lows(series),
    }


def get_recent_swing_lows(
    series: pd.Series,
    n: int = 2,
    lookback: int = 20,
) -> pd.Series:
    """
    Get the N most recent swing lows within a lookback window.
    
    Args:
        series: Price or indicator series
        n: Number of swing lows to return
        lookback: Maximum lookback period
        
    Returns:
        Series with the N most recent swing lows
    """
    window = series.iloc[-lookback:]
    lows = find_swing_lows(window).dropna()
    return lows.iloc[-n:] if len(lows) >= n else lows


def get_recent_swing_highs(
    series: pd.Series,
    n: int = 2,
    lookback: int = 20,
) -> pd.Series:
    """
    Get the N most recent swing highs within a lookback window.
    
    Args:
        series: Price or indicator series
        n: Number of swing highs to return
        lookback: Maximum lookback period
        
    Returns:
        Series with the N most recent swing highs
    """
    window = series.iloc[-lookback:]
    highs = find_swing_highs(window).dropna()
    return highs.iloc[-n:] if len(highs) >= n else highs

