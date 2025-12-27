"""
Technical indicator calculations.
Pure math functions operating on pandas DataFrames/Series.

Unified calculator for all investing projects in 000-099-investing.
"""

import pandas as pd
import numpy as np
from typing import Tuple

from shared_core.config.constants import (
    TREND_THRESHOLDS,
    RSI_THRESHOLDS,
    VOLATILITY_THRESHOLDS,
    DEFAULT_PERIODS,
)


class TechnicalCalculator:
    """
    Calculate all technical indicators from raw OHLCV data.
    All methods are static - no state needed.
    """

    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average."""
        return data.rolling(window=period).mean()

    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average."""
        return data.ewm(span=period, adjust=False).mean()

    @staticmethod
    def rsi(close_prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Relative Strength Index.

        Args:
            close_prices: Series of closing prices
            period: RSI period (default 14)

        Returns:
            Series of RSI values (0-100)
        """
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def macd(close_prices: pd.Series, fast: int = 12, slow: int = 26,
             signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Moving Average Convergence Divergence.

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
    def bollinger_bands(close_prices: pd.Series, period: int = 20,
                        num_std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands.

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
        Average True Range.

        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            period: ATR period (default 14)
        """
        high, low, close = df['high'], df['low'], df['close']
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

    @staticmethod
    def stochastic(df: pd.DataFrame, k_period: int = 14,
                   d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic Oscillator.

        Returns:
            Tuple of (%K, %D)
        """
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        k = 100 * ((df['close'] - low_min) / (high_max - low_min))
        d = k.rolling(window=d_period).mean()
        return k, d

    @staticmethod
    def adx(df: pd.DataFrame, period: int = 14) -> float:
        """
        Average Directional Index.

        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            period: ADX period (default 14)

        Returns:
            Current ADX value (float)
        """
        high, low, close = df['high'], df['low'], df['close']
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        return float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else 20.0

    @staticmethod
    def adx_series(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Average Directional Index as a full Series.

        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            period: ADX period (default 14)

        Returns:
            Series of ADX values
        """
        high, low, close = df['high'], df['low'], df['close']
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        return dx.rolling(window=period).mean()

    @staticmethod
    def obv(df: pd.DataFrame) -> pd.Series:
        """
        On-Balance Volume.

        Args:
            df: DataFrame with 'close' and 'volume' columns
        """
        return (df['volume'] * np.where(df['close'].diff() > 0, 1, -1)).cumsum()

    @staticmethod
    def vwap(df: pd.DataFrame, period: int = 20) -> float:
        """
        Volume Weighted Average Price (over recent period).

        Args:
            df: DataFrame with 'close' and 'volume' columns
            period: Number of bars to include

        Returns:
            VWAP value (float)
        """
        recent_df = df.tail(period)
        total_volume = recent_df['volume'].sum()
        if total_volume > 0:
            return float((recent_df['close'] * recent_df['volume']).sum() / total_volume)
        return float(df['close'].iloc[-1])

    @staticmethod
    def williams_r(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Williams %R: -100 to 0, below -80 = oversold, above -20 = overbought.
        """
        high_max = df['high'].rolling(window=period).max()
        low_min = df['low'].rolling(window=period).min()
        wr = -100 * ((high_max - df['close']) / (high_max - low_min))
        return wr

    @staticmethod
    def roc(close: pd.Series, period: int = 14) -> pd.Series:
        """Rate of Change: percentage change over N periods."""
        return ((close - close.shift(period)) / close.shift(period)) * 100

    @staticmethod
    def classify_trend(current_price: float, sma_20: float, sma_50: float,
                       sma_200: float, macd_hist: float) -> str:
        """
        Classify the current trend based on price and moving averages.

        Returns:
            One of: 'STRONG_UPTREND', 'UPTREND', 'SIDEWAYS', 'DOWNTREND', 'STRONG_DOWNTREND'
        """
        strong_up = TREND_THRESHOLDS.STRONG_UPTREND_MULTIPLIER
        strong_down = TREND_THRESHOLDS.STRONG_DOWNTREND_MULTIPLIER

        if current_price > sma_200 * strong_up and macd_hist > 0 and sma_20 > sma_50 > sma_200:
            return 'STRONG_UPTREND'
        elif current_price > sma_200 and sma_20 > sma_50:
            return 'UPTREND'
        elif current_price < sma_200 * strong_down and macd_hist < 0 and sma_20 < sma_50 < sma_200:
            return 'STRONG_DOWNTREND'
        elif current_price < sma_200 and sma_20 < sma_50:
            return 'DOWNTREND'
        else:
            return 'SIDEWAYS'

    @staticmethod
    def classify_obv_trend(obv_series: pd.Series) -> str:
        """
        Classify OBV trend.

        Returns:
            One of: 'UP', 'DOWN', 'SIDEWAYS'
        """
        obv_sma = obv_series.rolling(DEFAULT_PERIODS.OBV_SMA).mean()
        if obv_series.iloc[-1] > obv_sma.iloc[-1] * TREND_THRESHOLDS.OBV_UP_MULTIPLIER:
            return 'UP'
        elif obv_series.iloc[-1] < obv_sma.iloc[-1] * TREND_THRESHOLDS.OBV_DOWN_MULTIPLIER:
            return 'DOWN'
        else:
            return 'SIDEWAYS'

    @staticmethod
    def detect_divergence(df: pd.DataFrame, rsi_series: pd.Series) -> str:
        """
        Detect RSI divergence.

        Returns:
            One of: 'BULLISH', 'BEARISH', 'NONE'
        """
        price_trend = df['close'].tail(DEFAULT_PERIODS.SMA_SHORT).diff().sum()
        rsi_trend = rsi_series.tail(DEFAULT_PERIODS.SMA_SHORT).diff().sum()
        rsi_current = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50.0

        if price_trend < 0 and rsi_trend > 0 and rsi_current < RSI_THRESHOLDS.BULLISH_DIVERGENCE_MAX:
            return 'BULLISH'
        elif price_trend > 0 and rsi_trend < 0 and rsi_current > RSI_THRESHOLDS.BEARISH_DIVERGENCE_MIN:
            return 'BEARISH'
        else:
            return 'NONE'

    @staticmethod
    def detect_rsi_divergence(df: pd.DataFrame, lookback: int = 14) -> str:
        """
        Detects RSI divergence over the lookback period.

        Returns: 'bullish', 'bearish', or 'none'
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

    @staticmethod
    def detect_obv_divergence(df: pd.DataFrame, lookback: int = 14) -> str:
        """
        Detects OBV divergence over the lookback period.

        Returns: 'bullish', 'bearish', or 'none'
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

    @staticmethod
    def count_consecutive_direction(df: pd.DataFrame, lookback: int = 10) -> dict:
        """
        Counts consecutive up/down days.

        Returns: {'consecutive_down': int, 'consecutive_up': int}
        """
        if len(df) < 2:
            return {'consecutive_down': 0, 'consecutive_up': 0}

        recent = df.iloc[-lookback:]
        changes = recent['close'].diff().dropna()

        # Count consecutive from end
        consecutive_down = 0
        consecutive_up = 0

        for change in reversed(changes.values):
            if change < 0:
                if consecutive_up == 0:
                    consecutive_down += 1
                else:
                    break
            elif change > 0:
                if consecutive_down == 0:
                    consecutive_up += 1
                else:
                    break
            else:
                break

        return {'consecutive_down': consecutive_down, 'consecutive_up': consecutive_up}

    @staticmethod
    def classify_volatility(atr_series: pd.Series, lookback: int = 90) -> str:
        """
        Classify current volatility regime.

        Returns:
            One of: 'LOW', 'NORMAL', 'HIGH', 'EXTREME'
        """
        atr_recent = atr_series.tail(min(lookback, len(atr_series)))
        atr_current = float(atr_series.iloc[-1])
        atr_min, atr_max = atr_recent.min(), atr_recent.max()

        if atr_max > atr_min:
            atr_pct = (atr_current - atr_min) / (atr_max - atr_min)
        else:
            atr_pct = 0.5

        if atr_pct < VOLATILITY_THRESHOLDS.LOW_PERCENTILE:
            return 'LOW'
        elif atr_pct < VOLATILITY_THRESHOLDS.NORMAL_PERCENTILE:
            return 'NORMAL'
        elif atr_pct < VOLATILITY_THRESHOLDS.HIGH_PERCENTILE:
            return 'HIGH'
        else:
            return 'EXTREME'

    @staticmethod
    def calculate_support_resistance(df: pd.DataFrame, short_window: int = 20,
                                     long_window: int = 90) -> dict:
        """
        Calculate support and resistance levels.

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

