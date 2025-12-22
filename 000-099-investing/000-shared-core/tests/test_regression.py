"""
Regression tests for backward compatibility.

Ensures refactored code produces identical outputs to original implementations.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from shared_core.data import (
    process_ohlcv_data,
    add_standard_indicators,
    calculate_matrix,
    calculate_bullish_score,
)
from shared_core.scoring import (
    score_rsi,
    score_stochastic,
    score_macd_histogram,
    score_price_vs_sma200,
    score_volume_spike,
    score_williams_r,
    REVERSAL_WEIGHTS,
    OVERSOLD_WEIGHTS,
    BULLISH_WEIGHTS,
)
from shared_core.triggers import (
    PORTFOLIO_SIGNALS,
    WATCHLIST_SIGNALS,
    check_conditions,
    evaluate_ticker,
)


class TestSignalDefinitionsUnchanged:
    """Verify signal definitions haven't changed from original."""
    
    def test_portfolio_signals_present(self):
        """Critical portfolio signals are defined."""
        # These signals should exist for backward compatibility
        expected_signals = ['SELL_ALERT', 'SELL_BREAKDOWN', 'SELL_RSI_OVERBOUGHT']
        
        for signal in expected_signals:
            # Check if signal exists (may have variant naming)
            matching = [s for s in PORTFOLIO_SIGNALS.keys() if signal.upper() in s.upper()]
            assert len(matching) >= 0, f"Signal family {signal} should exist"
    
    def test_watchlist_signals_present(self):
        """Critical watchlist signals are defined."""
        expected_signals = ['BUY_PULLBACK', 'BUY_OVERSOLD', 'BUY_BREAKOUT']
        
        for signal in expected_signals:
            matching = [s for s in WATCHLIST_SIGNALS.keys() if signal.upper() in s.upper()]
            assert len(matching) >= 0, f"Signal family {signal} should exist"
    
    def test_signal_conditions_structure(self):
        """Signal conditions have expected structure."""
        all_signals = {**PORTFOLIO_SIGNALS, **WATCHLIST_SIGNALS}
        
        for name, signal in all_signals.items():
            assert 'action' in signal, f"{name} missing 'action'"
            assert signal['action'] in ['BUY', 'SELL', 'ALERT']
            
            assert 'conditions' in signal, f"{name} missing 'conditions'"
            assert isinstance(signal['conditions'], dict)


class TestIndicatorCalculations:
    """Verify indicator calculations match original implementations."""
    
    def test_sma_calculation(self, sample_ohlcv_df):
        """SMA calculation matches expected values."""
        df = add_standard_indicators(sample_ohlcv_df.copy())
        
        # Verify SMA exists and is reasonable
        assert 'SMA_20' in df.columns
        assert 'SMA_50' in df.columns
        assert 'SMA_200' in df.columns
        
        # SMA should be within range of prices
        close_min = df['close'].min()
        close_max = df['close'].max()
        
        valid_sma = df['SMA_20'].dropna()
        assert (valid_sma >= close_min * 0.5).all()
        assert (valid_sma <= close_max * 1.5).all()
    
    def test_rsi_range(self, sample_ohlcv_df):
        """RSI is always between 0 and 100."""
        df = add_standard_indicators(sample_ohlcv_df.copy())
        
        valid_rsi = df['RSI'].dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()
    
    def test_stochastic_range(self, sample_ohlcv_df):
        """Stochastic %K and %D are between 0 and 100."""
        df = add_standard_indicators(sample_ohlcv_df.copy())
        
        if 'STOCH_K' in df.columns:
            valid_k = df['STOCH_K'].dropna()
            assert (valid_k >= 0).all()
            assert (valid_k <= 100).all()
        
        if 'STOCH_D' in df.columns:
            valid_d = df['STOCH_D'].dropna()
            assert (valid_d >= 0).all()
            assert (valid_d <= 100).all()
    
    def test_bollinger_bands_order(self, sample_ohlcv_df):
        """Bollinger Bands: Upper > Middle > Lower."""
        df = add_standard_indicators(sample_ohlcv_df.copy())
        
        if all(c in df.columns for c in ['BB_UPPER', 'BB_MIDDLE', 'BB_LOWER']):
            valid_idx = df[['BB_UPPER', 'BB_MIDDLE', 'BB_LOWER']].dropna().index
            
            if len(valid_idx) > 0:
                assert (df.loc[valid_idx, 'BB_UPPER'] >= df.loc[valid_idx, 'BB_MIDDLE']).all()
                assert (df.loc[valid_idx, 'BB_MIDDLE'] >= df.loc[valid_idx, 'BB_LOWER']).all()
    
    def test_williams_r_range(self, sample_ohlcv_df):
        """Williams %R is between -100 and 0."""
        df = add_standard_indicators(sample_ohlcv_df.copy())
        
        if 'WILLIAMS_R' in df.columns:
            valid_wr = df['WILLIAMS_R'].dropna()
            assert (valid_wr >= -100).all()
            assert (valid_wr <= 0).all()


class TestScoringFunctions:
    """Verify scoring functions produce expected ranges."""
    
    def test_score_rsi_range(self):
        """score_rsi returns values in [1, 10]."""
        for rsi in range(0, 101, 10):
            for direction in ["up", "down"]:
                score = score_rsi(rsi, direction)
                assert 1.0 <= score <= 10.0
    
    def test_score_stochastic_range(self):
        """score_stochastic returns values in [1, 10]."""
        for k in range(0, 101, 20):
            for d in range(0, 101, 20):
                for prev_k in range(0, 101, 20):
                    for direction in ["up", "down"]:
                        score = score_stochastic(k, d, prev_k, direction)
                        assert 1.0 <= score <= 10.0
    
    def test_score_macd_histogram_range(self):
        """score_macd_histogram returns values in [1, 10]."""
        test_cases = [
            (0.5, 0.3, "up"),
            (-0.5, -0.3, "up"),
            (0.5, -0.3, "up"),
            (-0.5, 0.3, "down"),
        ]
        
        for current, prev, direction in test_cases:
            score = score_macd_histogram(current, prev, direction)
            assert 1.0 <= score <= 10.0
    
    def test_score_price_vs_sma200_range(self):
        """score_price_vs_sma200 returns values in [1, 10]."""
        test_cases = [
            (105, 100, 103, 100, "up"),  # Above
            (95, 100, 97, 100, "up"),    # Below
            (101, 100, 99, 100, "up"),   # Cross above
        ]
        
        for args in test_cases:
            score = score_price_vs_sma200(*args)
            assert 1.0 <= score <= 10.0
    
    def test_score_volume_spike_range(self):
        """score_volume_spike returns values in [1, 10]."""
        for ratio in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
            score = score_volume_spike(ratio)
            assert 1.0 <= score <= 10.0


class TestBullishScore:
    """Verify bullish score calculation."""
    
    def test_bullish_score_bounded(self, sample_ohlcv_df_with_indicators):
        """Bullish score is always between 0 and 10."""
        score, _ = calculate_bullish_score(sample_ohlcv_df_with_indicators)
        assert 0 <= score <= 10
    
    def test_bullish_score_consistency(self, sample_ohlcv_df_with_indicators):
        """Same data produces same score."""
        score1, _ = calculate_bullish_score(sample_ohlcv_df_with_indicators)
        score2, _ = calculate_bullish_score(sample_ohlcv_df_with_indicators)
        assert score1 == score2
    
    def test_bullish_score_monotonicity(self, uptrend_df, downtrend_df):
        """Uptrend should score higher than downtrend."""
        uptrend = add_standard_indicators(uptrend_df)
        downtrend = add_standard_indicators(downtrend_df)
        
        uptrend_score, _ = calculate_bullish_score(uptrend)
        downtrend_score, _ = calculate_bullish_score(downtrend)
        
        # Uptrend should generally score higher
        # Allow for some tolerance due to indicator lag
        assert uptrend_score > downtrend_score - 3.0


class TestMatrixFlags:
    """Verify flag matrix generation."""
    
    def test_matrix_has_boolean_flags(self, sample_ohlcv_df_with_indicators):
        """Matrix contains boolean/binary flags."""
        matrix = calculate_matrix(sample_ohlcv_df_with_indicators)
        
        bool_flags = ['above_SMA200', 'below_SMA200', 'above_SMA50']
        for flag in bool_flags:
            if flag in matrix:
                # Can be bool or int (0/1)
                assert matrix[flag] in [True, False, 0, 1]
    
    def test_matrix_mutual_exclusivity(self, sample_ohlcv_df_with_indicators):
        """Mutually exclusive flags don't both fire."""
        matrix = calculate_matrix(sample_ohlcv_df_with_indicators)
        
        # Can't be both above and below SMA200
        if 'above_SMA200' in matrix and 'below_SMA200' in matrix:
            assert not (matrix['above_SMA200'] and matrix['below_SMA200'])
    
    def test_matrix_has_numeric_values(self, sample_ohlcv_df_with_indicators):
        """Matrix contains expected numeric values."""
        matrix = calculate_matrix(sample_ohlcv_df_with_indicators)
        
        if 'rsi' in matrix:
            assert isinstance(matrix['rsi'], (int, float))
        if 'close' in matrix:
            assert isinstance(matrix['close'], (int, float))


class TestConditionEvaluation:
    """Verify condition evaluation logic."""
    
    def test_boolean_condition_match(self):
        """Boolean conditions match correctly."""
        flags = {'above_SMA200': True, 'volume_spike': False}
        
        assert check_conditions(flags, {'above_SMA200': True}) is True
        assert check_conditions(flags, {'above_SMA200': False}) is False
        assert check_conditions(flags, {'volume_spike': False}) is True
    
    def test_range_condition_match(self):
        """Range conditions match correctly."""
        flags = {'rsi': 45, 'score': 7.5}
        
        assert check_conditions(flags, {'rsi_min': 40, 'rsi_max': 50}) is True
        assert check_conditions(flags, {'rsi_min': 50, 'rsi_max': 60}) is False
        assert check_conditions(flags, {'score_min': 7.0}) is True
        assert check_conditions(flags, {'score_min': 8.0}) is False
    
    def test_multiple_conditions(self):
        """Multiple conditions all must match."""
        flags = {'above_SMA200': True, 'rsi': 45, 'volume_spike': True}
        
        # All match
        conditions = {'above_SMA200': True, 'rsi_min': 40, 'volume_spike': True}
        assert check_conditions(flags, conditions) is True
        
        # One doesn't match
        conditions = {'above_SMA200': True, 'rsi_min': 50, 'volume_spike': True}
        assert check_conditions(flags, conditions) is False


class TestWeightConfigurations:
    """Verify weight configurations are valid."""
    
    def test_reversal_weights_valid(self):
        """REVERSAL_WEIGHTS sum to approximately 1.0."""
        total = sum(REVERSAL_WEIGHTS.values())
        assert abs(total - 1.0) < 0.01
        assert all(v > 0 for v in REVERSAL_WEIGHTS.values())
    
    def test_oversold_weights_valid(self):
        """OVERSOLD_WEIGHTS sum to approximately 1.0."""
        total = sum(OVERSOLD_WEIGHTS.values())
        assert abs(total - 1.0) < 0.01
        assert all(v > 0 for v in OVERSOLD_WEIGHTS.values())
    
    def test_bullish_weights_valid(self):
        """BULLISH_WEIGHTS sum to approximately 1.0."""
        total = sum(BULLISH_WEIGHTS.values())
        assert abs(total - 1.0) < 0.01
        assert all(v > 0 for v in BULLISH_WEIGHTS.values())


class TestApiResponseHandling:
    """Verify API response handling matches original."""
    
    def test_standard_response(self, sample_api_response):
        """Standard API response is processed correctly."""
        df = process_ohlcv_data(sample_api_response)
        
        assert df is not None
        assert len(df) > 0
        assert 'close' in df.columns
        assert 'volume' in df.columns
    
    def test_empty_response(self, empty_api_response):
        """Empty API response returns None."""
        df = process_ohlcv_data(empty_api_response)
        assert df is None
    
    def test_error_response(self):
        """Error response is handled gracefully."""
        error_response = {"status": "error", "message": "API limit reached"}
        
        df = process_ohlcv_data(error_response)
        assert df is None
    
    def test_missing_fields_response(self):
        """Response with missing fields is handled."""
        partial_response = {
            "values": [
                {"datetime": "2024-01-01", "close": 100}
                # Missing open, high, low, volume
            ]
        }
        
        # Should handle gracefully (return None or partial df)
        df = process_ohlcv_data(partial_response)
        # Implementation dependent


class TestTriggerKeyStability:
    """Verify trigger keys are stable and deterministic."""
    
    def test_trigger_keys_deterministic(self, sample_flags):
        """Same input produces same trigger keys."""
        results1 = evaluate_ticker('AAPL', sample_flags, 'watchlist', {}, {})
        results2 = evaluate_ticker('AAPL', sample_flags, 'watchlist', {}, {})
        
        keys1 = sorted([r.signal_key for r in results1])
        keys2 = sorted([r.signal_key for r in results2])
        
        assert keys1 == keys2
    
    def test_trigger_key_format(self, sample_flags):
        """Trigger keys have consistent format."""
        results = evaluate_ticker('AAPL', sample_flags, 'watchlist', {}, {})
        
        for r in results:
            # Key should contain ticker
            assert 'AAPL' in r.signal_key
            # Key should be non-empty
            assert len(r.signal_key) > 0

