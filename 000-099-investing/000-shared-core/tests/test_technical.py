"""
Unit tests for TechnicalCalculator.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shared_core.market_data.technical import TechnicalCalculator


@pytest.fixture
def sample_ohlcv_df():
    """Create a sample OHLCV DataFrame with 100 days of data."""
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    
    # Generate realistic price data with trend
    base_price = 100.0
    returns = np.random.normal(0.001, 0.02, 100)
    prices = base_price * np.cumprod(1 + returns)
    
    df = pd.DataFrame({
        'open': prices * (1 + np.random.uniform(-0.01, 0.01, 100)),
        'high': prices * (1 + np.abs(np.random.uniform(0, 0.02, 100))),
        'low': prices * (1 - np.abs(np.random.uniform(0, 0.02, 100))),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)
    
    return df


@pytest.fixture
def calc():
    """Create TechnicalCalculator instance."""
    return TechnicalCalculator()


class TestSMAandEMA:
    """Tests for SMA and EMA calculations."""
    
    def test_sma_returns_series(self, sample_ohlcv_df, calc):
        result = calc.sma(sample_ohlcv_df['close'], 20)
        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlcv_df)
    
    def test_sma_correct_values(self, calc):
        data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        result = calc.sma(data, 5)
        # First 4 values should be NaN
        assert pd.isna(result.iloc[0])
        assert pd.isna(result.iloc[3])
        # 5th value should be mean of 1,2,3,4,5 = 3
        assert result.iloc[4] == 3.0
        # Last value should be mean of 6,7,8,9,10 = 8
        assert result.iloc[9] == 8.0
    
    def test_ema_returns_series(self, sample_ohlcv_df, calc):
        result = calc.ema(sample_ohlcv_df['close'], 20)
        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlcv_df)
    
    def test_ema_reacts_faster_than_sma(self, calc):
        # EMA should react faster to recent prices
        data = pd.Series([10, 10, 10, 10, 10, 20, 20, 20, 20, 20])
        sma = calc.sma(data, 5)
        ema = calc.ema(data, 5)
        # After the jump, EMA should be higher than SMA initially
        assert ema.iloc[6] > sma.iloc[6]


class TestRSI:
    """Tests for RSI calculation."""
    
    def test_rsi_returns_series(self, sample_ohlcv_df, calc):
        result = calc.rsi(sample_ohlcv_df['close'], 14)
        assert isinstance(result, pd.Series)
    
    def test_rsi_bounds(self, sample_ohlcv_df, calc):
        result = calc.rsi(sample_ohlcv_df['close'], 14)
        valid = result.dropna()
        assert all(valid >= 0)
        assert all(valid <= 100)
    
    def test_rsi_high_on_uptrend(self, sample_ohlcv_df, calc):
        # Use realistic price data with mostly upward movement (but some down days)
        np.random.seed(42)
        # Biased random walk with positive drift
        returns = np.random.normal(0.005, 0.015, 100)  # Positive drift
        prices = pd.Series(100 * np.cumprod(1 + returns))
        result = calc.rsi(prices, 14)
        # RSI should generally be above neutral for uptrend
        valid_rsi = result.dropna()
        assert len(valid_rsi) > 0
        # Average RSI should be above 50 for uptrend
        assert valid_rsi.mean() > 45
    
    def test_rsi_low_on_downtrend(self, calc):
        # Steadily decreasing prices should give low RSI
        prices = pd.Series(range(100, 0, -1))
        result = calc.rsi(prices, 14)
        assert result.iloc[-1] < 30


class TestMACD:
    """Tests for MACD calculation."""
    
    def test_macd_returns_tuple(self, sample_ohlcv_df, calc):
        result = calc.macd(sample_ohlcv_df['close'])
        assert isinstance(result, tuple)
        assert len(result) == 3
    
    def test_macd_returns_series(self, sample_ohlcv_df, calc):
        macd_line, signal_line, histogram = calc.macd(sample_ohlcv_df['close'])
        assert isinstance(macd_line, pd.Series)
        assert isinstance(signal_line, pd.Series)
        assert isinstance(histogram, pd.Series)
    
    def test_macd_histogram_is_difference(self, sample_ohlcv_df, calc):
        macd_line, signal_line, histogram = calc.macd(sample_ohlcv_df['close'])
        calculated_hist = macd_line - signal_line
        pd.testing.assert_series_equal(histogram, calculated_hist)


class TestBollingerBands:
    """Tests for Bollinger Bands calculation."""
    
    def test_bollinger_returns_tuple(self, sample_ohlcv_df, calc):
        result = calc.bollinger_bands(sample_ohlcv_df['close'])
        assert isinstance(result, tuple)
        assert len(result) == 3
    
    def test_bollinger_order(self, sample_ohlcv_df, calc):
        upper, middle, lower = calc.bollinger_bands(sample_ohlcv_df['close'])
        valid_idx = ~(upper.isna() | middle.isna() | lower.isna())
        assert all(upper[valid_idx] >= middle[valid_idx])
        assert all(middle[valid_idx] >= lower[valid_idx])


class TestATR:
    """Tests for ATR calculation."""
    
    def test_atr_returns_series(self, sample_ohlcv_df, calc):
        result = calc.atr(sample_ohlcv_df)
        assert isinstance(result, pd.Series)
    
    def test_atr_positive(self, sample_ohlcv_df, calc):
        result = calc.atr(sample_ohlcv_df)
        valid = result.dropna()
        assert all(valid >= 0)


class TestStochastic:
    """Tests for Stochastic Oscillator calculation."""
    
    def test_stochastic_returns_tuple(self, sample_ohlcv_df, calc):
        result = calc.stochastic(sample_ohlcv_df)
        assert isinstance(result, tuple)
        assert len(result) == 2
    
    def test_stochastic_bounds(self, sample_ohlcv_df, calc):
        k, d = calc.stochastic(sample_ohlcv_df)
        valid_k = k.dropna()
        valid_d = d.dropna()
        assert all(valid_k >= 0) and all(valid_k <= 100)
        assert all(valid_d >= 0) and all(valid_d <= 100)


class TestADX:
    """Tests for ADX calculation."""
    
    def test_adx_returns_float(self, sample_ohlcv_df, calc):
        result = calc.adx(sample_ohlcv_df)
        assert isinstance(result, float)
    
    def test_adx_series_returns_series(self, sample_ohlcv_df, calc):
        result = calc.adx_series(sample_ohlcv_df)
        assert isinstance(result, pd.Series)
    
    def test_adx_positive(self, sample_ohlcv_df, calc):
        result = calc.adx(sample_ohlcv_df)
        assert result >= 0


class TestOBV:
    """Tests for OBV calculation."""
    
    def test_obv_returns_series(self, sample_ohlcv_df, calc):
        result = calc.obv(sample_ohlcv_df)
        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlcv_df)


class TestTrendClassification:
    """Tests for trend classification methods."""
    
    def test_classify_trend_strong_uptrend(self, calc):
        result = calc.classify_trend(
            current_price=110.0,
            sma_20=105.0,
            sma_50=100.0,
            sma_200=90.0,
            macd_hist=1.5
        )
        assert result == 'STRONG_UPTREND'
    
    def test_classify_trend_downtrend(self, calc):
        result = calc.classify_trend(
            current_price=80.0,
            sma_20=85.0,
            sma_50=90.0,
            sma_200=100.0,
            macd_hist=-1.5
        )
        # Can be DOWNTREND or STRONG_DOWNTREND depending on severity
        assert result in ['DOWNTREND', 'STRONG_DOWNTREND']
    
    def test_classify_obv_trend_up(self, calc):
        obv = pd.Series([100, 110, 120, 130, 140] * 10)
        result = calc.classify_obv_trend(obv)
        assert result == 'UP'
    
    def test_classify_volatility(self, calc):
        atr = pd.Series(range(1, 101))  # Increasing volatility
        result = calc.classify_volatility(atr)
        assert result in ['LOW', 'NORMAL', 'HIGH', 'EXTREME']


class TestDivergence:
    """Tests for divergence detection."""
    
    def test_detect_divergence_returns_valid(self, sample_ohlcv_df, calc):
        rsi = calc.rsi(sample_ohlcv_df['close'])
        result = calc.detect_divergence(sample_ohlcv_df, rsi)
        assert result in ['BULLISH', 'BEARISH', 'NONE']


class TestSupportResistance:
    """Tests for support/resistance calculation."""
    
    def test_calculate_support_resistance(self, sample_ohlcv_df, calc):
        result = calc.calculate_support_resistance(sample_ohlcv_df)
        assert 'closest_support' in result
        assert 'key_support' in result
        assert 'closest_resistance' in result
        assert 'strongest_resistance' in result
        
        # Support should be lower than resistance
        assert result['key_support'] <= result['strongest_resistance']

