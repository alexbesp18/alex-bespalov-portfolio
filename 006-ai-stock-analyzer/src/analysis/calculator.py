"""
Technical indicator calculations.

All calculations are performed client-side from raw OHLCV data,
reducing API costs to a single data fetch per stock.
"""

import logging
from typing import Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class TechnicalCalculator:
    """
    Calculate technical indicators from raw OHLCV data.
    
    Implements standard technical analysis indicators including:
    - Moving averages (SMA, EMA)
    - Momentum indicators (RSI, MACD, Stochastic)
    - Volatility measures (ATR, Bollinger Bands)
    - Support/Resistance levels
    """
    
    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """
        Calculate Simple Moving Average.
        
        Args:
            data: Price series (typically close prices)
            period: Number of periods for the average
            
        Returns:
            Series with SMA values
        """
        return data.rolling(window=period).mean()
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """
        Calculate Exponential Moving Average.
        
        Args:
            data: Price series
            period: EMA period (span)
            
        Returns:
            Series with EMA values
        """
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def rsi(close_prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index.
        
        RSI measures momentum by comparing recent gains vs losses.
        Values above 70 indicate overbought, below 30 is oversold.
        
        Args:
            close_prices: Close price series
            period: RSI period (default 14)
            
        Returns:
            Series with RSI values (0-100 range)
        """
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        # Avoid division by zero
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def macd(
        close_prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            close_prices: Close price series
            fast: Fast EMA period (default 12)
            slow: Slow EMA period (default 26)
            signal: Signal line period (default 9)
            
        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        ema_fast = close_prices.ewm(span=fast, adjust=False).mean()
        ema_slow = close_prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def bollinger_bands(
        close_prices: pd.Series,
        period: int = 20,
        num_std: float = 2.0
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands.
        
        Args:
            close_prices: Close price series
            period: Moving average period (default 20)
            num_std: Number of standard deviations (default 2.0)
            
        Returns:
            Tuple of (upper_band, middle_band, lower_band)
        """
        sma = close_prices.rolling(window=period).mean()
        std = close_prices.rolling(window=period).std()
        upper = sma + (std * num_std)
        lower = sma - (std * num_std)
        return upper, sma, lower
    
    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range (volatility indicator).
        
        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            period: ATR period (default 14)
            
        Returns:
            Series with ATR values
        """
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr
    
    @staticmethod
    def stochastic(
        df: pd.DataFrame,
        k_period: int = 14,
        d_period: int = 3
    ) -> tuple[pd.Series, pd.Series]:
        """
        Calculate Stochastic Oscillator.
        
        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            k_period: %K period (default 14)
            d_period: %D smoothing period (default 3)
            
        Returns:
            Tuple of (%K, %D) series
        """
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        
        k = 100 * ((df['close'] - low_min) / (high_max - low_min))
        d = k.rolling(window=d_period).mean()
        
        return k, d
    
    @staticmethod
    def calculate_support_resistance(
        df: pd.DataFrame,
        short_window: int = 20,
        long_window: int = 90
    ) -> Dict[str, float]:
        """
        Calculate support and resistance levels.
        
        Uses recent price action to identify key levels where
        price is likely to find support or resistance.
        
        Args:
            df: DataFrame with OHLC data
            short_window: Window for recent levels (default 20)
            long_window: Window for major levels (default 90)
            
        Returns:
            Dict with support and resistance levels
        """
        # Recent levels (last 20 days)
        recent_high = df['high'].tail(short_window).max()
        recent_low = df['low'].tail(short_window).min()
        
        # Longer-term levels (last 90 days)
        strong_resistance = df['high'].tail(long_window).max()
        strong_support = df['low'].tail(long_window).min()
        
        # Find pivot points
        current_price = df['close'].iloc[-1]
        
        # Closest support: highest low below current price
        support_levels = df[df['low'] < current_price]['low'].tail(short_window)
        closest_support = support_levels.max() if not support_levels.empty else recent_low
        
        # Closest resistance: lowest high above current price
        resistance_levels = df[df['high'] > current_price]['high'].tail(short_window)
        closest_resistance = resistance_levels.min() if not resistance_levels.empty else recent_high
        
        return {
            'closest_support': float(closest_support),
            'key_support': float(strong_support),
            'closest_resistance': float(closest_resistance),
            'strongest_resistance': float(strong_resistance)
        }
