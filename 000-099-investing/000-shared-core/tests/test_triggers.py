"""
Unit tests for shared_core.triggers module.

Tests trigger engine, conditions, definitions, and evaluation.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

from shared_core.triggers import (
    # Definitions
    PORTFOLIO_SIGNALS,
    WATCHLIST_SIGNALS,
    # Conditions
    check_conditions,
    is_in_cooldown,
    is_suppressed,
    update_cooldowns,
    # Evaluation
    TriggerResult,
    evaluate_ticker,
    # Engine
    TriggerEngine,
)


class TestTriggerDefinitions:
    """Tests for signal definitions."""
    
    def test_portfolio_signals_exists(self):
        """PORTFOLIO_SIGNALS is defined."""
        assert isinstance(PORTFOLIO_SIGNALS, dict)
    
    def test_watchlist_signals_exists(self):
        """WATCHLIST_SIGNALS is defined."""
        assert isinstance(WATCHLIST_SIGNALS, dict)
    
    def test_signal_structure(self):
        """Signals have required fields."""
        all_signals = {**PORTFOLIO_SIGNALS, **WATCHLIST_SIGNALS}
        
        for name, signal in all_signals.items():
            assert 'action' in signal, f"{name} missing action"
            assert 'conditions' in signal, f"{name} missing conditions"
            assert signal['action'] in ['BUY', 'SELL', 'ALERT', 'WATCH']


class TestCheckConditions:
    """Tests for check_conditions function."""
    
    def test_all_match(self, sample_flags):
        """All conditions matching returns True."""
        conditions = {
            'above_SMA200': True,
            'below_SMA200': False,
        }
        
        result = check_conditions(sample_flags, conditions)
        assert result is True
    
    def test_partial_match(self, sample_flags):
        """Partial match returns False."""
        conditions = {
            'above_SMA200': True,
            'below_SMA200': True,  # This doesn't match
        }
        
        result = check_conditions(sample_flags, conditions)
        assert result is False
    
    def test_empty_conditions(self, sample_flags):
        """Empty conditions always match."""
        result = check_conditions(sample_flags, {})
        assert result is True
    
    def test_missing_flag(self, sample_flags):
        """Missing flag in data returns False for that condition."""
        conditions = {'nonexistent_flag': True}
        result = check_conditions(sample_flags, conditions)
        assert result is False


class TestCooldowns:
    """Tests for cooldown functions."""
    
    def test_update_cooldowns(self):
        """update_cooldowns adds cooldown entries."""
        cooldowns = {}
        triggered = [
            {'signal_key': 'TEST:SIGNAL', 'cooldown_days': 7}
        ]
        
        update_cooldowns(cooldowns, triggered)
        
        assert 'TEST:SIGNAL' in cooldowns
    
    def test_is_in_cooldown_active(self):
        """is_in_cooldown returns True for active cooldown."""
        future = (datetime.now() + timedelta(days=1)).isoformat()
        
        cooldowns = {'TEST:SIGNAL': future}
        
        result = is_in_cooldown('TEST:SIGNAL', cooldowns, cooldown_days=7)
        assert result is True
    
    def test_is_in_cooldown_expired(self):
        """is_in_cooldown returns False for expired cooldown."""
        past = (datetime.now() - timedelta(days=10)).isoformat()
        
        cooldowns = {'TEST:SIGNAL': past}
        
        result = is_in_cooldown('TEST:SIGNAL', cooldowns, cooldown_days=7)
        assert result is False
    
    def test_is_in_cooldown_unknown(self):
        """is_in_cooldown returns False for unknown key."""
        result = is_in_cooldown('UNKNOWN:KEY', {}, cooldown_days=7)
        assert result is False
    
    def test_is_in_cooldown_zero_days(self):
        """is_in_cooldown returns False when cooldown_days is 0."""
        future = (datetime.now() + timedelta(days=1)).isoformat()
        cooldowns = {'TEST:SIGNAL': future}
        
        result = is_in_cooldown('TEST:SIGNAL', cooldowns, cooldown_days=0)
        assert result is False


class TestSuppression:
    """Tests for is_suppressed function."""
    
    def test_is_suppressed_unknown(self):
        """is_suppressed returns False for unknown ticker/signal."""
        result = is_suppressed('UNKNOWN', 'SIGNAL', {})
        assert result is False


class TestTriggerResult:
    """Tests for TriggerResult dataclass."""
    
    def test_create_trigger_result(self):
        """Create TriggerResult with all fields."""
        result = TriggerResult(
            ticker='AAPL',
            signal='BUY_PULLBACK',
            action='BUY',
            description='Buy signal triggered',
            cooldown_days=7,
            signal_key='AAPL:BUY_PULLBACK',
        )
        
        assert result.ticker == 'AAPL'
        assert result.action == 'BUY'
        assert result.signal_key == 'AAPL:BUY_PULLBACK'
    
    def test_to_dict(self):
        """TriggerResult.to_dict includes all fields."""
        result = TriggerResult(
            ticker='AAPL',
            signal='BUY_PULLBACK',
            action='BUY',
            description='Test',
            cooldown_days=7,
            signal_key='AAPL:BUY_PULLBACK',
        )
        
        d = result.to_dict()
        assert 'ticker' in d
        assert 'signal' in d
        assert 'action' in d


class TestEvaluateTicker:
    """Tests for evaluate_ticker function."""
    
    def test_returns_list(self, sample_flags):
        """evaluate_ticker returns list of TriggerResults."""
        result = evaluate_ticker(
            ticker='AAPL',
            flags=sample_flags,
            list_type='watchlist',
            cooldowns={},
            actioned={},
        )
        
        assert isinstance(result, list)
    
    def test_portfolio_vs_watchlist(self, sample_flags):
        """Different list_type uses different signals."""
        portfolio_result = evaluate_ticker(
            ticker='AAPL',
            flags=sample_flags,
            list_type='portfolio',
            cooldowns={},
            actioned={},
        )
        
        watchlist_result = evaluate_ticker(
            ticker='AAPL',
            flags=sample_flags,
            list_type='watchlist',
            cooldowns={},
            actioned={},
        )
        
        assert isinstance(portfolio_result, list)
        assert isinstance(watchlist_result, list)


class TestTriggerEngine:
    """Tests for TriggerEngine class."""
    
    @pytest.fixture
    def engine(self):
        """Create a basic trigger engine."""
        triggers = [
            {
                'type': 'score_above',
                'value': 7,
                'action': 'BUY',
            },
            {
                'type': 'score_below',
                'value': 4,
                'action': 'SELL',
            },
        ]
        return TriggerEngine(triggers)
    
    def test_evaluate_returns_list(self, engine, sample_ohlcv_df_with_indicators):
        """TriggerEngine.evaluate returns a list."""
        results = engine.evaluate(
            symbol='AAPL',
            df=sample_ohlcv_df_with_indicators,
            score=8.0,
        )
        
        assert isinstance(results, list)
    
    def test_evaluate_score_above(self, engine, sample_ohlcv_df_with_indicators):
        """TriggerEngine triggers on score_above."""
        results = engine.evaluate(
            symbol='AAPL',
            df=sample_ohlcv_df_with_indicators,
            score=8.0,
        )
        
        # Should have at least one BUY trigger
        buy_results = [r for r in results if r.get('action') == 'BUY']
        assert len(buy_results) >= 1
    
    def test_evaluate_score_below(self, engine, sample_ohlcv_df_with_indicators):
        """TriggerEngine triggers on score_below."""
        results = engine.evaluate(
            symbol='AAPL',
            df=sample_ohlcv_df_with_indicators,
            score=3.0,
        )
        
        sell_results = [r for r in results if r.get('action') == 'SELL']
        assert len(sell_results) >= 1
    
    def test_empty_triggers(self, sample_ohlcv_df_with_indicators):
        """Engine with no triggers returns empty results."""
        engine = TriggerEngine([])
        results = engine.evaluate(
            symbol='AAPL',
            df=sample_ohlcv_df_with_indicators,
            score=8.0,
        )
        assert results == []
    
    def test_price_above_ma(self, sample_ohlcv_df_with_indicators):
        """TriggerEngine evaluates price_above_ma."""
        engine = TriggerEngine([
            {'type': 'price_above_ma', 'ma': 'SMA_20', 'action': 'BUY'}
        ])
        
        results = engine.evaluate(
            symbol='AAPL',
            df=sample_ohlcv_df_with_indicators,
            score=5.0,
        )
        
        assert isinstance(results, list)
    
    def test_trigger_key_deterministic(self, sample_ohlcv_df_with_indicators):
        """Trigger keys are deterministic."""
        engine = TriggerEngine([
            {'type': 'score_above', 'value': 7, 'action': 'BUY'}
        ])
        
        results1 = engine.evaluate(
            symbol='AAPL',
            df=sample_ohlcv_df_with_indicators,
            score=8.0,
        )
        results2 = engine.evaluate(
            symbol='AAPL',
            df=sample_ohlcv_df_with_indicators,
            score=8.0,
        )
        
        if results1 and results2:
            keys1 = [r.get('trigger_key') for r in results1]
            keys2 = [r.get('trigger_key') for r in results2]
            assert keys1 == keys2


class TestTriggerEdgeCases:
    """Edge case tests for triggers."""
    
    def test_empty_flags(self):
        """Handle empty flags dict."""
        result = check_conditions({}, {'above_SMA200': True})
        assert result is False
    
    def test_none_values_in_flags(self):
        """Handle None values in flags."""
        flags = {'above_SMA200': None, 'rsi': None}
        conditions = {'above_SMA200': True}
        result = check_conditions(flags, conditions)
        assert result is False
    
    def test_empty_df(self):
        """Handle empty DataFrame in TriggerEngine."""
        engine = TriggerEngine([{'type': 'score_above', 'value': 7, 'action': 'BUY'}])
        
        empty_df = pd.DataFrame()
        results = engine.evaluate(symbol='AAPL', df=empty_df, score=8.0)
        
        assert results == []
    
    def test_short_df(self):
        """Handle short DataFrame in TriggerEngine."""
        engine = TriggerEngine([{'type': 'score_above', 'value': 7, 'action': 'BUY'}])
        
        short_df = pd.DataFrame({'close': [100.0]})
        results = engine.evaluate(symbol='AAPL', df=short_df, score=8.0)
        
        assert results == []
