"""
Binary flags matrix for dashboard output.

Generates a dictionary of binary (0/1) flags for easy filtering
and dashboard display.
"""

import pandas as pd
from typing import Dict, Any

from ..market_data.technical import TechnicalCalculator


def calculate_matrix(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate binary flags matrix for dashboard/matrix output.
    
    Categories:
    - Price Correction from 52W High: corr_5pct, corr_10pct, etc.
    - Price vs MAs: above_SMA5, above_SMA14, above_SMA50, above_SMA200
    - MA Crosses Today: golden_cross, death_cross
    - RSI Levels: rsi_above_85, rsi_above_70, rsi_below_30, rsi_below_15
    
    Also includes non-binary metadata:
    - _price, _high_52w, _pct_from_high, _rsi
    
    Args:
        df: DataFrame with OHLCV and indicator data
        
    Returns:
        Dict with binary (0/1) values for each flag plus metadata
        
    Example:
        >>> matrix = calculate_matrix(df)
        >>> if matrix['corr_20pct'] == 1:
        ...     print("Stock is 20%+ off highs")
    """
    if df is None or len(df) < 2:
        return {}
    
    calc = TechnicalCalculator()
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    price = curr['close']
    
    # Calculate 52-week high (use available data)
    high_52w = df['high'].max()
    
    # Ensure short-term SMAs exist
    if 'SMA_5' not in df.columns:
        df = df.copy()
        df['SMA_5'] = calc.sma(df['close'], 5)
    if 'SMA_14' not in df.columns:
        df = df.copy()
        df['SMA_14'] = calc.sma(df['close'], 14)
    
    curr = df.iloc[-1]  # Refresh after adding columns
    prev = df.iloc[-2]
    
    matrix: Dict[str, Any] = {}
    
    # === Price Correction from 52W High ===
    pct_from_high = (high_52w - price) / high_52w * 100 if high_52w > 0 else 0
    matrix['corr_5pct'] = 1 if pct_from_high >= 5 else 0
    matrix['corr_10pct'] = 1 if pct_from_high >= 10 else 0
    matrix['corr_15pct'] = 1 if pct_from_high >= 15 else 0
    matrix['corr_20pct'] = 1 if pct_from_high >= 20 else 0
    matrix['corr_30pct'] = 1 if pct_from_high >= 30 else 0
    matrix['corr_40pct'] = 1 if pct_from_high >= 40 else 0
    matrix['corr_50pct'] = 1 if pct_from_high >= 50 else 0
    
    # === Price vs MAs ===
    matrix['above_SMA5'] = 1 if price > (curr.get('SMA_5') or 0) else 0
    matrix['above_SMA14'] = 1 if price > (curr.get('SMA_14') or 0) else 0
    matrix['above_SMA50'] = 1 if price > (curr.get('SMA_50') or 0) else 0
    matrix['above_SMA200'] = 1 if price > (curr.get('SMA_200') or 0) else 0
    
    # === MA Crosses Today ===
    sma50_curr = curr.get('SMA_50') or 0
    sma50_prev = prev.get('SMA_50') or 0
    sma200_curr = curr.get('SMA_200') or 0
    sma200_prev = prev.get('SMA_200') or 0
    
    # Golden Cross: SMA50 crosses above SMA200
    matrix['golden_cross'] = 1 if (sma50_prev <= sma200_prev and sma50_curr > sma200_curr) else 0
    # Death Cross: SMA50 crosses below SMA200
    matrix['death_cross'] = 1 if (sma50_prev >= sma200_prev and sma50_curr < sma200_curr) else 0
    
    # === RSI Levels ===
    rsi = curr.get('RSI') or 50
    matrix['rsi_above_85'] = 1 if rsi > 85 else 0
    matrix['rsi_above_70'] = 1 if rsi > 70 else 0
    matrix['rsi_below_30'] = 1 if rsi < 30 else 0
    matrix['rsi_below_15'] = 1 if rsi < 15 else 0
    
    # === Non-binary metadata (prefixed with _) ===
    matrix['_price'] = round(price, 2)
    matrix['_high_52w'] = round(high_52w, 2)
    matrix['_pct_from_high'] = round(pct_from_high, 1)
    matrix['_rsi'] = round(rsi, 1)
    
    return matrix


def filter_by_flags(
    matrices: list,
    required_flags: Dict[str, int],
) -> list:
    """
    Filter a list of matrix dicts by required flag values.
    
    Args:
        matrices: List of matrix dicts from calculate_matrix()
        required_flags: Dict of flag -> expected value
        
    Returns:
        Filtered list of matrices matching all required flags
        
    Example:
        >>> # Find stocks 20%+ off highs and above SMA200
        >>> filtered = filter_by_flags(matrices, {'corr_20pct': 1, 'above_SMA200': 1})
    """
    return [
        m for m in matrices
        if all(m.get(flag) == value for flag, value in required_flags.items())
    ]

