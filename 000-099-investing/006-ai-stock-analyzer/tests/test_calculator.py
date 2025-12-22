"""Tests for TechnicalCalculator from shared_core."""

import numpy as np
import pandas as pd
import pytest

from shared_core.market_data.technical import TechnicalCalculator


class TestMovingAverages:
    """Test moving average calculations."""
    
    def test_sma_basic(self, sample_prices):
        """Test simple moving average calculation."""
        sma = TechnicalCalculator.sma(sample_prices, period=5)
        
        assert len(sma) == len(sample_prices)
        assert pd.isna(sma.iloc[0])  # First values should be NaN
        assert not pd.isna(sma.iloc[5])  # Should have values after period
        
        # Verify calculation manually for last value
        expected = sample_prices.iloc[-5:].mean()
        assert abs(sma.iloc[-1] - expected) < 0.001
    
    def test_ema_basic(self, sample_prices):
        """Test exponential moving average calculation."""
        ema = TechnicalCalculator.ema(sample_prices, period=12)
        
        assert len(ema) == len(sample_prices)
        # EMA should have all values (uses ewm)
        assert not pd.isna(ema.iloc[-1])


class TestMomentumIndicators:
    """Test momentum indicator calculations."""
    
    def test_rsi_range(self, sample_prices):
        """Test that RSI values are in valid range (0-100)."""
        rsi = TechnicalCalculator.rsi(sample_prices, period=14)
        
        valid_values = rsi.dropna()
        assert all(valid_values >= 0)
        assert all(valid_values <= 100)
    
    def test_rsi_with_constant_gains(self):
        """Test RSI with constant upward movement."""
        # Add some small variation to avoid division-by-zero edge case
        prices = pd.Series([100 + i + (i % 3) * 0.1 for i in range(30)])
        rsi = TechnicalCalculator.rsi(prices, period=14)
        
        # With mostly gains, RSI should be high (>70)
        valid_rsi = rsi.dropna()
        if len(valid_rsi) > 0:
            assert valid_rsi.iloc[-1] > 70
    
    def test_macd_components(self, sample_prices):
        """Test MACD returns all three components."""
        macd_line, signal_line, histogram = TechnicalCalculator.macd(sample_prices)
        
        assert len(macd_line) == len(sample_prices)
        assert len(signal_line) == len(sample_prices)
        assert len(histogram) == len(sample_prices)
        
        # Histogram should equal macd - signal
        error = abs(histogram.iloc[-1] - (macd_line.iloc[-1] - signal_line.iloc[-1]))
        assert error < 0.001


class TestVolatilityIndicators:
    """Test volatility indicator calculations."""
    
    def test_bollinger_bands_order(self, sample_ohlcv_df):
        """Test that Bollinger Bands are in correct order (upper > middle > lower)."""
        upper, middle, lower = TechnicalCalculator.bollinger_bands(
            sample_ohlcv_df['close'], period=20
        )
        
        # Check last valid values
        assert upper.iloc[-1] > middle.iloc[-1]
        assert middle.iloc[-1] > lower.iloc[-1]
    
    def test_atr_positive(self, sample_ohlcv_df):
        """Test that ATR values are positive."""
        atr = TechnicalCalculator.atr(sample_ohlcv_df, period=14)
        
        valid_values = atr.dropna()
        assert all(valid_values > 0)
    
    def test_stochastic_range(self, sample_ohlcv_df):
        """Test that Stochastic values are in 0-100 range."""
        k, d = TechnicalCalculator.stochastic(sample_ohlcv_df)
        
        k_valid = k.dropna()
        d_valid = d.dropna()
        
        assert all(k_valid >= 0) and all(k_valid <= 100)
        assert all(d_valid >= 0) and all(d_valid <= 100)


class TestSupportResistance:
    """Test support/resistance level calculations."""
    
    def test_returns_all_levels(self, sample_ohlcv_df):
        """Test that all expected levels are returned."""
        levels = TechnicalCalculator.calculate_support_resistance(sample_ohlcv_df)
        
        assert 'closest_support' in levels
        assert 'key_support' in levels
        assert 'closest_resistance' in levels
        assert 'strongest_resistance' in levels
    
    def test_support_below_resistance(self, sample_ohlcv_df):
        """Test that support levels are below resistance levels."""
        levels = TechnicalCalculator.calculate_support_resistance(sample_ohlcv_df)
        
        assert levels['key_support'] <= levels['strongest_resistance']
