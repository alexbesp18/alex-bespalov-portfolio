"""
OHLCV data processing utilities.

Converts raw API responses to DataFrames with calculated indicators.
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, Optional

# Import TechnicalCalculator for indicator calculations
from ..market_data.technical import TechnicalCalculator


def process_ohlcv_data(
    time_series_data: Dict[str, Any],
    include_indicators: bool = True,
) -> Optional[pd.DataFrame]:
    """
    Convert raw Twelve Data API response to DataFrame with indicators.
    
    Args:
        time_series_data: API response with 'values' key containing OHLCV data
        include_indicators: If True, calculate standard technical indicators
        
    Returns:
        DataFrame with datetime index and OHLCV + indicators, or None if invalid
        
    Example:
        >>> data = fetch_from_twelve_data("NVDA")
        >>> df = process_ohlcv_data(data)
        >>> print(df.columns)
        Index(['open', 'high', 'low', 'close', 'volume', 'SMA_20', 'RSI', ...])
    """
    if "values" not in time_series_data or not time_series_data["values"]:
        return None
    
    df = pd.DataFrame(time_series_data["values"])
    
    # Parse datetime and set as index
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.set_index('datetime').sort_index()
    
    # Convert numeric columns
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows with missing close prices
    df = df.dropna(subset=['close'])
    
    if len(df) < 20:
        return None
    
    if include_indicators:
        df = add_standard_indicators(df)
    
    return df


def add_standard_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add standard technical indicators to a DataFrame.
    
    Adds:
    - SMAs: SMA_5, SMA_14, SMA_20, SMA_50, SMA_200
    - Momentum: RSI, MACD, MACD_SIGNAL, MACD_HIST
    - Volatility: BB_UPPER, BB_MIDDLE, BB_LOWER, BB_WIDTH, ATR
    - Volume: OBV
    - Oscillators: STOCH_K, STOCH_D, ADX, WILLIAMS_R, ROC
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with added indicator columns
    """
    calc = TechnicalCalculator()
    
    # SMAs
    df['SMA_5'] = calc.sma(df['close'], 5)
    df['SMA_14'] = calc.sma(df['close'], 14)
    df['SMA_20'] = calc.sma(df['close'], 20)
    df['SMA_50'] = calc.sma(df['close'], 50)
    df['SMA_200'] = calc.sma(df['close'], 200)
    
    # RSI
    df['RSI'] = calc.rsi(df['close'], 14)
    
    # MACD
    macd_line, signal_line, hist = calc.macd(df['close'])
    df['MACD'] = macd_line
    df['MACD_SIGNAL'] = signal_line
    df['MACD_HIST'] = hist
    
    # Bollinger Bands with width
    bb_upper, bb_middle, bb_lower = calc.bollinger_bands(df['close'])
    df['BB_UPPER'] = bb_upper
    df['BB_MIDDLE'] = bb_middle
    df['BB_LOWER'] = bb_lower
    df['BB_WIDTH'] = ((bb_upper - bb_lower) / bb_middle) * 100
    
    # ATR
    df['ATR'] = calc.atr(df)
    
    # OBV (requires volume)
    if 'volume' in df.columns:
        df['OBV'] = calc.obv(df)
    
    # Stochastics
    stoch_k, stoch_d = calc.stochastic(df)
    df['STOCH_K'] = stoch_k
    df['STOCH_D'] = stoch_d
    
    # ADX
    df['ADX'] = calc.adx_series(df)
    
    # Williams %R
    df['WILLIAMS_R'] = calc.williams_r(df)
    
    # Rate of Change
    df['ROC'] = calc.roc(df['close'])
    
    return df


def bollinger_bands_with_width(
    close: pd.Series,
    period: int = 20,
    std_dev: int = 2,
) -> tuple:
    """
    Calculate Bollinger Bands with bandwidth.
    
    Args:
        close: Series of closing prices
        period: Lookback period (default 20)
        std_dev: Number of standard deviations (default 2)
        
    Returns:
        Tuple of (upper_band, middle_band, lower_band, bandwidth)
    """
    middle = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    bandwidth = ((upper - lower) / middle) * 100
    return upper, middle, lower, bandwidth

