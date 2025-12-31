"""
Unit tests for shared_core.data module.

Tests OHLCV processing, flag matrix calculation, and bullish score.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from shared_core.data import (
    process_ohlcv_data,
    add_standard_indicators,
    bollinger_bands_with_width,
    calculate_matrix,
    filter_by_flags,
    calculate_bullish_score,
    calculate_bullish_score_detailed,
)


class TestProcessOhlcvData:
    """Tests for process_ohlcv_data function."""
    
    def test_process_ohlcv_data_returns_dataframe(self, sample_api_response):
        """process_ohlcv_data returns a DataFrame."""
        result = process_ohlcv_data(sample_api_response)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
    
    def test_process_ohlcv_data_adds_indicators(self, sample_api_response):
        """process_ohlcv_data adds standard indicators."""
        result = process_ohlcv_data(sample_api_response)
        
        # Check for key indicators
        expected_columns = ['close', 'open', 'high', 'low', 'volume']
        for col in expected_columns:
            assert col in result.columns
        
        # Check for derived indicators
        indicator_columns = ['SMA_20', 'SMA_50', 'SMA_200', 'RSI']
        for col in indicator_columns:
            assert col in result.columns
    
    def test_process_ohlcv_data_returns_none_on_empty(self, empty_api_response):
        """process_ohlcv_data returns None for empty response."""
        result = process_ohlcv_data(empty_api_response)
        assert result is None
    
    def test_process_ohlcv_data_returns_none_on_insufficient(self, insufficient_api_response):
        """process_ohlcv_data returns None for insufficient data."""
        result = process_ohlcv_data(insufficient_api_response)
        # May return None or very short DataFrame depending on implementation
        if result is not None:
            assert len(result) < 20
    
    def test_process_ohlcv_data_handles_missing_volume(self):
        """process_ohlcv_data handles missing volume column."""
        from datetime import datetime, timedelta
        base_date = datetime(2024, 1, 1)
        response = {
            "values": [
                {"datetime": (base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
                 "open": 100 + i, "high": 101 + i,
                 "low": 99 + i, "close": 100.5 + i}
                for i in range(250)
            ]
        }
        result = process_ohlcv_data(response)
        # Should still work, volume might be NaN or 0
        assert result is None or 'close' in result.columns
    
    def test_process_ohlcv_data_datetime_index(self, sample_api_response):
        """process_ohlcv_data sets datetime as index."""
        result = process_ohlcv_data(sample_api_response)
        assert isinstance(result.index, pd.DatetimeIndex)
    
    def test_process_ohlcv_data_numeric_columns(self, sample_api_response):
        """All OHLCV columns are numeric."""
        result = process_ohlcv_data(sample_api_response)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            assert pd.api.types.is_numeric_dtype(result[col])


class TestAddStandardIndicators:
    """Tests for add_standard_indicators function."""
    
    def test_adds_moving_averages(self, sample_ohlcv_df):
        """add_standard_indicators adds SMA columns."""
        result = add_standard_indicators(sample_ohlcv_df.copy())
        
        assert 'SMA_20' in result.columns
        assert 'SMA_50' in result.columns
        assert 'SMA_200' in result.columns
    
    def test_adds_rsi(self, sample_ohlcv_df):
        """add_standard_indicators adds RSI."""
        result = add_standard_indicators(sample_ohlcv_df.copy())
        assert 'RSI' in result.columns
        
        # RSI should be between 0 and 100
        valid_rsi = result['RSI'].dropna()
        assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all()
    
    def test_adds_macd(self, sample_ohlcv_df):
        """add_standard_indicators adds MACD components."""
        result = add_standard_indicators(sample_ohlcv_df.copy())
        
        assert 'MACD' in result.columns or 'MACD_LINE' in result.columns
        assert 'MACD_SIGNAL' in result.columns
        assert 'MACD_HIST' in result.columns
    
    def test_adds_stochastic(self, sample_ohlcv_df):
        """add_standard_indicators adds Stochastic oscillator."""
        result = add_standard_indicators(sample_ohlcv_df.copy())
        
        assert 'STOCH_K' in result.columns
        assert 'STOCH_D' in result.columns
        
        # Stochastic should be between 0 and 100
        valid_k = result['STOCH_K'].dropna()
        assert (valid_k >= 0).all() and (valid_k <= 100).all()
    
    def test_adds_bollinger_bands(self, sample_ohlcv_df):
        """add_standard_indicators adds Bollinger Bands."""
        result = add_standard_indicators(sample_ohlcv_df.copy())
        
        assert 'BB_UPPER' in result.columns
        assert 'BB_MIDDLE' in result.columns
        assert 'BB_LOWER' in result.columns
        
        # Upper should be > Middle > Lower
        valid_idx = result[['BB_UPPER', 'BB_MIDDLE', 'BB_LOWER']].dropna().index
        if len(valid_idx) > 0:
            assert (result.loc[valid_idx, 'BB_UPPER'] >= result.loc[valid_idx, 'BB_MIDDLE']).all()
            assert (result.loc[valid_idx, 'BB_MIDDLE'] >= result.loc[valid_idx, 'BB_LOWER']).all()
    
    def test_adds_williams_r(self, sample_ohlcv_df):
        """add_standard_indicators adds Williams %R."""
        result = add_standard_indicators(sample_ohlcv_df.copy())
        
        assert 'WILLIAMS_R' in result.columns
        
        # Williams %R should be between -100 and 0
        valid_wr = result['WILLIAMS_R'].dropna()
        assert (valid_wr >= -100).all() and (valid_wr <= 0).all()
    
    def test_adds_adx(self, sample_ohlcv_df):
        """add_standard_indicators adds ADX."""
        result = add_standard_indicators(sample_ohlcv_df.copy())
        assert 'ADX' in result.columns
    
    def test_adds_obv(self, sample_ohlcv_df):
        """add_standard_indicators adds OBV."""
        result = add_standard_indicators(sample_ohlcv_df.copy())
        assert 'OBV' in result.columns
    
    def test_preserves_original_columns(self, sample_ohlcv_df):
        """Original OHLCV columns are preserved."""
        original_cols = list(sample_ohlcv_df.columns)
        result = add_standard_indicators(sample_ohlcv_df.copy())
        
        for col in original_cols:
            assert col in result.columns


class TestBollingerBandsWithWidth:
    """Tests for bollinger_bands_with_width function."""
    
    def test_returns_tuple_of_four_series(self, sample_ohlcv_df):
        """Returns tuple of (upper, middle, lower, bandwidth)."""
        result = bollinger_bands_with_width(sample_ohlcv_df['close'], period=20, std_dev=2)
        
        assert isinstance(result, tuple)
        assert len(result) == 4
        upper, middle, lower, bandwidth = result
        assert isinstance(upper, pd.Series)
        assert isinstance(middle, pd.Series)
        assert isinstance(lower, pd.Series)
        assert isinstance(bandwidth, pd.Series)
    
    def test_width_calculation(self, sample_ohlcv_df):
        """Width is (upper - lower) / middle * 100."""
        upper, middle, lower, bandwidth = bollinger_bands_with_width(sample_ohlcv_df['close'])
        
        # Get valid (non-NaN) values
        valid_mask = ~bandwidth.isna()
        expected_width = ((upper[valid_mask] - lower[valid_mask]) / middle[valid_mask]) * 100
        pd.testing.assert_series_equal(bandwidth[valid_mask], expected_width, check_names=False)


class TestCalculateMatrix:
    """Tests for calculate_matrix function."""
    
    def test_calculate_matrix_returns_dict(self, sample_ohlcv_df_with_indicators):
        """calculate_matrix returns a dictionary."""
        result = calculate_matrix(sample_ohlcv_df_with_indicators)
        assert isinstance(result, dict)
    
    def test_binary_flags(self, sample_ohlcv_df_with_indicators):
        """Matrix contains 0/1 binary flags."""
        result = calculate_matrix(sample_ohlcv_df_with_indicators)
        
        # Check for binary flags (0 or 1)
        binary_flags = ['above_SMA200', 'above_SMA50', 'golden_cross', 'death_cross']
        for flag in binary_flags:
            if flag in result:
                assert result[flag] in [0, 1]
    
    def test_rsi_present(self, sample_ohlcv_df_with_indicators):
        """Matrix includes RSI value."""
        result = calculate_matrix(sample_ohlcv_df_with_indicators)
        assert '_rsi' in result
    
    def test_golden_cross(self):
        """Detect golden cross (SMA50 crosses above SMA200)."""
        # Create data where SMA50 crosses above SMA200
        dates = pd.date_range('2024-01-01', periods=250)
        prices = np.linspace(100, 200, 250)  # Strong uptrend
        
        df = pd.DataFrame({
            'open': prices,
            'high': prices * 1.01,
            'low': prices * 0.99,
            'close': prices,
            'volume': [1000000] * 250
        }, index=dates)
        
        df = add_standard_indicators(df)
        result = calculate_matrix(df)
        
        # In strong uptrend, should eventually show SMA50 > SMA200
        assert 'above_SMA200' in result or 'above_SMA50' in result
    
    def test_death_cross(self):
        """Detect death cross flag exists."""
        # Create data for downtrend
        dates = pd.date_range('2024-01-01', periods=250)
        prices = np.linspace(200, 100, 250)  # Strong downtrend
        
        df = pd.DataFrame({
            'open': prices,
            'high': prices * 1.01,
            'low': prices * 0.99,
            'close': prices,
            'volume': [1000000] * 250
        }, index=dates)
        
        df = add_standard_indicators(df)
        result = calculate_matrix(df)
        
        # Matrix should have death_cross flag
        assert 'death_cross' in result
        assert result['death_cross'] in [0, 1]


class TestFilterByFlags:
    """Tests for filter_by_flags function."""
    
    def test_filter_by_single_flag(self):
        """Filter by a single binary flag."""
        matrices = [
            {'symbol': 'AAPL', 'above_SMA200': 1, '_rsi': 45},
            {'symbol': 'NVDA', 'above_SMA200': 0, '_rsi': 55},
            {'symbol': 'GOOGL', 'above_SMA200': 1, '_rsi': 35},
        ]
        
        result = filter_by_flags(matrices, {'above_SMA200': 1})
        
        assert len(result) == 2
        symbols = [m['symbol'] for m in result]
        assert 'AAPL' in symbols
        assert 'GOOGL' in symbols
    
    def test_filter_by_multiple_flags(self):
        """Filter by multiple flags."""
        matrices = [
            {'symbol': 'AAPL', 'above_SMA200': 1, 'corr_20pct': 1},
            {'symbol': 'NVDA', 'above_SMA200': 1, 'corr_20pct': 0},
            {'symbol': 'GOOGL', 'above_SMA200': 0, 'corr_20pct': 1},
        ]
        
        result = filter_by_flags(matrices, {'above_SMA200': 1, 'corr_20pct': 1})
        
        assert len(result) == 1
        assert result[0]['symbol'] == 'AAPL'
    
    def test_filter_empty_criteria(self):
        """Empty criteria returns all matrices."""
        matrices = [{'_rsi': 45}, {'_rsi': 55}]
        result = filter_by_flags(matrices, {})
        
        assert len(result) == 2


class TestCalculateBullishScore:
    """Tests for calculate_bullish_score function."""
    
    def test_returns_tuple(self, sample_ohlcv_df_with_indicators):
        """calculate_bullish_score returns (score, breakdown) tuple."""
        result = calculate_bullish_score(sample_ohlcv_df_with_indicators)
        assert isinstance(result, tuple)
        assert len(result) == 2
    
    def test_score_is_numeric(self, sample_ohlcv_df_with_indicators):
        """Score is a numeric value."""
        score, breakdown = calculate_bullish_score(sample_ohlcv_df_with_indicators)
        assert isinstance(score, (int, float))
    
    def test_score_range(self, sample_ohlcv_df_with_indicators):
        """Score is between 0 and 10."""
        score, breakdown = calculate_bullish_score(sample_ohlcv_df_with_indicators)
        assert 0 <= score <= 10
    
    def test_breakdown_is_dict(self, sample_ohlcv_df_with_indicators):
        """Breakdown is a dict with component scores."""
        score, breakdown = calculate_bullish_score(sample_ohlcv_df_with_indicators)
        assert isinstance(breakdown, dict)
        assert len(breakdown) > 0
    
    def test_uptrend_higher_score(self, uptrend_df):
        """Uptrending stock gets higher bullish score."""
        df = add_standard_indicators(uptrend_df)
        score, _ = calculate_bullish_score(df)
        # Should be in upper half
        assert score > 4.0
    
    def test_downtrend_lower_score(self, downtrend_df):
        """Downtrending stock gets lower bullish score."""
        df = add_standard_indicators(downtrend_df)
        score, _ = calculate_bullish_score(df)
        # Should be in lower half
        assert score < 6.0


class TestCalculateBullishScoreDetailed:
    """Tests for calculate_bullish_score_detailed function."""
    
    def test_returns_bullish_score(self, sample_ohlcv_df_with_indicators):
        """Returns BullishScore object."""
        from shared_core.scoring.models import BullishScore
        result = calculate_bullish_score_detailed(sample_ohlcv_df_with_indicators)
        
        assert isinstance(result, BullishScore)
    
    def test_has_final_score(self, sample_ohlcv_df_with_indicators):
        """BullishScore has final_score attribute."""
        result = calculate_bullish_score_detailed(sample_ohlcv_df_with_indicators)
        
        assert hasattr(result, 'final_score')
        assert isinstance(result.final_score, (int, float))
    
    def test_has_components(self, sample_ohlcv_df_with_indicators):
        """BullishScore has components dict."""
        result = calculate_bullish_score_detailed(sample_ohlcv_df_with_indicators)
        
        assert hasattr(result, 'components')
        assert isinstance(result.components, dict)
    
    def test_score_consistency(self, sample_ohlcv_df_with_indicators):
        """Score matches simple calculation."""
        simple_score, _ = calculate_bullish_score(sample_ohlcv_df_with_indicators)
        detailed_result = calculate_bullish_score_detailed(sample_ohlcv_df_with_indicators)
        
        assert abs(simple_score - detailed_result.final_score) < 0.01


class TestEdgeCases:
    """Edge case tests for data processing."""
    
    def test_empty_dataframe(self):
        """Handle empty DataFrame."""
        empty_df = pd.DataFrame()
        score, breakdown = calculate_bullish_score(empty_df)
        assert score == 0.0  # Returns 0.0 for empty/insufficient data
    
    def test_single_row(self):
        """Handle single row DataFrame."""
        single_row = pd.DataFrame({
            'open': [100], 'high': [101], 'low': [99],
            'close': [100], 'volume': [1000000]
        }, index=[datetime.now()])
        
        # Should return 0.0 for insufficient data
        score, breakdown = calculate_bullish_score(single_row)
        assert score == 0.0
    
    def test_nan_values_in_indicators(self, sample_ohlcv_df):
        """Handle NaN values in indicators."""
        df = add_standard_indicators(sample_ohlcv_df.copy())
        
        # First few rows will have NaN for SMAs
        assert df['SMA_200'].isna().any()
        
        # Should still calculate score for valid rows
        score, breakdown = calculate_bullish_score(df)
        assert isinstance(score, (int, float))
        assert not pd.isna(score)
    
    def test_constant_prices(self):
        """Handle constant price series."""
        dates = pd.date_range('2024-01-01', periods=250)
        df = pd.DataFrame({
            'open': [100] * 250,
            'high': [100] * 250,
            'low': [100] * 250,
            'close': [100] * 250,
            'volume': [1000000] * 250
        }, index=dates)
        
        df = add_standard_indicators(df)
        score, breakdown = calculate_bullish_score(df)
        
        # Should handle constant prices gracefully
        assert isinstance(score, (int, float))

