"""
Unit tests for shared_core.divergence module.

Tests swing point detection and divergence detection.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from shared_core.divergence import (
    find_swing_lows,
    find_swing_highs,
    find_swing_points,
    get_recent_swing_lows,
    get_recent_swing_highs,
    detect_divergence_enhanced,
    detect_combined_divergence,
    detect_rsi_divergence,
    detect_obv_divergence,
    DivergenceType,
    DivergenceResult,
)
from shared_core.data import add_standard_indicators


class TestFindSwingLows:
    """Tests for find_swing_lows function."""
    
    def test_detects_local_minima(self):
        """Find swing lows identifies local minima."""
        prices = pd.Series([100, 98, 96, 94, 92, 90, 92, 94, 96, 98, 100])
        
        result = find_swing_lows(prices)
        
        assert isinstance(result, pd.Series)
        assert not result.dropna().empty
    
    def test_multiple_lows(self):
        """Detect multiple swing lows."""
        prices = pd.Series([100, 95, 90, 95, 100, 95, 85, 90, 95, 100])
        
        result = find_swing_lows(prices)
        
        assert isinstance(result, pd.Series)
    
    def test_empty_series(self):
        """Handle empty series."""
        result = find_swing_lows(pd.Series(dtype=float))
        assert isinstance(result, pd.Series)


class TestFindSwingHighs:
    """Tests for find_swing_highs function."""
    
    def test_detects_local_maxima(self):
        """Find swing highs identifies local maxima."""
        prices = pd.Series([90, 92, 94, 96, 98, 100, 98, 96, 94, 92, 90])
        
        result = find_swing_highs(prices)
        
        assert isinstance(result, pd.Series)
        assert not result.dropna().empty
    
    def test_empty_series(self):
        """Handle empty series."""
        result = find_swing_highs(pd.Series(dtype=float))
        assert isinstance(result, pd.Series)


class TestFindSwingPoints:
    """Tests for find_swing_points function."""
    
    def test_returns_dict(self):
        """Returns dict with highs and lows."""
        prices = pd.Series([90, 95, 100, 95, 90, 95, 100, 95, 90])
        
        result = find_swing_points(prices)
        
        assert isinstance(result, dict)
        assert 'highs' in result
        assert 'lows' in result


class TestGetRecentSwingPoints:
    """Tests for get_recent_swing_lows and get_recent_swing_highs."""
    
    def test_get_recent_swing_lows(self, sample_ohlcv_df):
        """get_recent_swing_lows returns Series."""
        result = get_recent_swing_lows(sample_ohlcv_df['close'], n=3, lookback=50)
        
        assert isinstance(result, pd.Series)
    
    def test_get_recent_swing_highs(self, sample_ohlcv_df):
        """get_recent_swing_highs returns Series."""
        result = get_recent_swing_highs(sample_ohlcv_df['close'], n=3, lookback=50)
        
        assert isinstance(result, pd.Series)
    
    def test_respects_n_limit(self, sample_ohlcv_df):
        """Returns at most n swing points."""
        result = get_recent_swing_lows(sample_ohlcv_df['close'], n=2, lookback=100)
        assert len(result.dropna()) <= 2


class TestDetectDivergenceEnhanced:
    """Tests for detect_divergence_enhanced function."""
    
    def test_returns_divergence_result(self, sample_ohlcv_df_with_indicators):
        """Returns a DivergenceResult object."""
        result = detect_divergence_enhanced(
            sample_ohlcv_df_with_indicators,
            lookback=14,
            indicator='RSI'
        )
        
        assert isinstance(result, DivergenceResult)
    
    def test_handles_short_data(self):
        """Handle short DataFrame."""
        df = pd.DataFrame({
            'close': [100, 101, 102],
            'RSI': [50, 51, 52]
        })
        result = detect_divergence_enhanced(df, lookback=14)
        assert result.type == DivergenceType.NONE
    
    def test_handles_missing_indicator(self, sample_ohlcv_df):
        """Handle missing indicator column."""
        result = detect_divergence_enhanced(sample_ohlcv_df, indicator='RSI')
        assert result.type == DivergenceType.NONE


class TestDetectCombinedDivergence:
    """Tests for detect_combined_divergence function."""
    
    def test_returns_divergence_result(self, sample_ohlcv_df_with_indicators):
        """Returns DivergenceResult."""
        result = detect_combined_divergence(sample_ohlcv_df_with_indicators)
        
        assert isinstance(result, DivergenceResult)
    
    def test_handles_missing_indicators(self, sample_ohlcv_df):
        """Handle DataFrame without indicators."""
        result = detect_combined_divergence(sample_ohlcv_df)
        assert isinstance(result, DivergenceResult)


class TestDetectRsiDivergence:
    """Tests for detect_rsi_divergence function."""
    
    def test_returns_string(self, sample_ohlcv_df_with_indicators):
        """Returns string description."""
        result = detect_rsi_divergence(sample_ohlcv_df_with_indicators)
        assert isinstance(result, str)
    
    def test_handles_missing_rsi(self, sample_ohlcv_df):
        """Handle DataFrame without RSI column."""
        result = detect_rsi_divergence(sample_ohlcv_df)
        assert isinstance(result, str)


class TestDetectObvDivergence:
    """Tests for detect_obv_divergence function."""
    
    def test_returns_string(self, sample_ohlcv_df_with_indicators):
        """Returns string description."""
        result = detect_obv_divergence(sample_ohlcv_df_with_indicators)
        assert isinstance(result, str)
    
    def test_handles_missing_obv(self, sample_ohlcv_df):
        """Handle DataFrame without OBV column."""
        result = detect_obv_divergence(sample_ohlcv_df)
        assert isinstance(result, str)


class TestDivergenceEdgeCases:
    """Edge case tests for divergence detection."""
    
    def test_empty_dataframe(self):
        """Handle empty DataFrame."""
        df = pd.DataFrame()
        result = detect_divergence_enhanced(df)
        assert result.type == DivergenceType.NONE
    
    def test_divergence_result_factories(self):
        """Test DivergenceResult factory methods."""
        bullish = DivergenceResult.bullish(5.0, "Test bullish")
        bearish = DivergenceResult.bearish(5.0, "Test bearish")
        none = DivergenceResult.none("Test none")
        
        assert bullish.type == DivergenceType.BULLISH
        assert bearish.type == DivergenceType.BEARISH
        assert none.type == DivergenceType.NONE
    
    def test_divergence_result_strength(self):
        """Divergence strength is preserved."""
        result = DivergenceResult.bullish(7.5, "Test")
        assert result.strength == 7.5
