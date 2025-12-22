"""
Property-based tests using Hypothesis.

Tests invariants and edge cases that would be difficult to enumerate manually.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from hypothesis import given, strategies as st, assume, settings, HealthCheck

from shared_core.scoring import (
    score_rsi,
    score_rsi_oversold,
    score_stochastic,
    score_stochastic_oversold,
    score_macd_histogram,
    score_williams_r,
    score_williams_r_oversold,
    score_volume_spike,
    score_bollinger_position,
    score_sma200_distance,
    get_volume_multiplier,
    get_adx_multiplier,
)
from shared_core.state import (
    StateManager,
    ArchiveManager,
    safe_read_json,
    safe_write_json,
    utc_now_iso,
    parse_iso_datetime,
)
from shared_core.triggers import (
    check_conditions,
    is_in_cooldown,
    update_cooldowns,
)


class TestScoringProperties:
    """Property-based tests for scoring functions."""
    
    @given(rsi=st.floats(0, 100))
    @settings(max_examples=50)
    def test_score_rsi_always_in_range(self, rsi):
        """score_rsi always returns value in [1, 10] or handles NaN."""
        assume(not pd.isna(rsi))
        
        result_up = score_rsi(rsi, "up")
        result_down = score_rsi(rsi, "down")
        
        assert 1.0 <= result_up <= 10.0
        assert 1.0 <= result_down <= 10.0
    
    @given(rsi=st.floats(0, 100))
    @settings(max_examples=50)
    def test_score_rsi_oversold_in_range(self, rsi):
        """score_rsi_oversold always returns value in [0, 10]."""
        assume(not pd.isna(rsi))
        
        result = score_rsi_oversold(rsi)
        assert 0.0 <= result <= 10.0
    
    @given(
        stoch_k=st.floats(0, 100),
        stoch_d=st.floats(0, 100),
        prev_k=st.floats(0, 100),
    )
    @settings(max_examples=50)
    def test_score_stochastic_in_range(self, stoch_k, stoch_d, prev_k):
        """score_stochastic always returns value in [1, 10]."""
        assume(all(not pd.isna(x) for x in [stoch_k, stoch_d, prev_k]))
        
        result_up = score_stochastic(stoch_k, stoch_d, prev_k, "up")
        result_down = score_stochastic(stoch_k, stoch_d, prev_k, "down")
        
        assert 1.0 <= result_up <= 10.0
        assert 1.0 <= result_down <= 10.0
    
    @given(stoch_k=st.floats(0, 100))
    @settings(max_examples=50)
    def test_score_stochastic_oversold_in_range(self, stoch_k):
        """score_stochastic_oversold always returns value in [0, 10]."""
        assume(not pd.isna(stoch_k))
        
        result = score_stochastic_oversold(stoch_k)
        assert 0.0 <= result <= 10.0
    
    @given(
        current=st.floats(-10, 10),
        prev=st.floats(-10, 10),
    )
    @settings(max_examples=50)
    def test_score_macd_histogram_in_range(self, current, prev):
        """score_macd_histogram always returns value in [1, 10]."""
        assume(all(not pd.isna(x) for x in [current, prev]))
        
        result_up = score_macd_histogram(current, prev, "up")
        result_down = score_macd_histogram(current, prev, "down")
        
        assert 1.0 <= result_up <= 10.0
        assert 1.0 <= result_down <= 10.0
    
    @given(williams_r=st.floats(-100, 0))
    @settings(max_examples=50)
    def test_score_williams_r_in_range(self, williams_r):
        """score_williams_r always returns value in [1, 10]."""
        assume(not pd.isna(williams_r))
        
        result_up = score_williams_r(williams_r, "up")
        result_down = score_williams_r(williams_r, "down")
        
        assert 1.0 <= result_up <= 10.0
        assert 1.0 <= result_down <= 10.0
    
    @given(williams_r=st.floats(-100, 0))
    @settings(max_examples=50)
    def test_score_williams_r_oversold_in_range(self, williams_r):
        """score_williams_r_oversold always returns value in [0, 10]."""
        assume(not pd.isna(williams_r))
        
        result = score_williams_r_oversold(williams_r)
        assert 0.0 <= result <= 10.0
    
    @given(volume_ratio=st.floats(0.1, 10.0))
    @settings(max_examples=50)
    def test_score_volume_spike_in_range(self, volume_ratio):
        """score_volume_spike always returns value in [1, 10]."""
        assume(not pd.isna(volume_ratio))
        
        result = score_volume_spike(volume_ratio)
        assert 1.0 <= result <= 10.0
    
    @given(
        close=st.floats(50, 200),
        bb_lower=st.floats(50, 150),
        bb_middle=st.floats(100, 200),
    )
    @settings(max_examples=50)
    def test_score_bollinger_position_in_range(self, close, bb_lower, bb_middle):
        """score_bollinger_position always returns value in [0, 10]."""
        assume(all(not pd.isna(x) for x in [close, bb_lower, bb_middle]))
        assume(bb_middle > bb_lower)  # Valid band configuration
        
        result = score_bollinger_position(close, bb_lower, bb_middle)
        assert 0.0 <= result <= 10.0
    
    @given(
        close=st.floats(50, 200),
        sma200=st.floats(80, 150),
    )
    @settings(max_examples=50)
    def test_score_sma200_distance_in_range(self, close, sma200):
        """score_sma200_distance always returns value in [0, 10]."""
        assume(all(not pd.isna(x) for x in [close, sma200]))
        assume(sma200 > 0)
        
        result = score_sma200_distance(close, sma200)
        assert 0.0 <= result <= 10.0


class TestMultiplierProperties:
    """Property-based tests for multiplier functions."""
    
    @given(adx=st.floats(0, 100))
    @settings(max_examples=50)
    def test_adx_multiplier_bounded(self, adx):
        """ADX multiplier is bounded between 0.75 and 1.1."""
        assume(not pd.isna(adx))
        
        result = get_adx_multiplier(adx, "reversal")
        assert 0.75 <= result <= 1.1


class TestStateProperties:
    """Property-based tests for state management."""
    
    @given(trigger_keys=st.lists(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'))), max_size=10))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_set_get_trigger_keys_roundtrip(self, trigger_keys, tmp_path):
        """Setting and getting trigger keys preserves data."""
        import uuid
        path = str(tmp_path / f"state_{uuid.uuid4()}.json")
        mgr = StateManager(path)
        state = mgr.load()
        
        mgr.set_last_run(state, trigger_keys)
        result = mgr.get_last_run_trigger_keys(state)
        
        assert result == trigger_keys
    
    @given(data=st.dictionaries(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))), st.integers(min_value=-1000000, max_value=1000000), max_size=10))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_json_roundtrip(self, data, tmp_path):
        """JSON write/read preserves data."""
        import os
        import uuid
        path = str(tmp_path / f"test_{uuid.uuid4()}.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        safe_write_json(path, data)
        result = safe_read_json(path)
        
        assert result == data


class TestDatetimeProperties:
    """Property-based tests for datetime handling."""
    
    @given(
        year=st.integers(2020, 2030),
        month=st.integers(1, 12),
        day=st.integers(1, 28),
        hour=st.integers(0, 23),
        minute=st.integers(0, 59),
    )
    @settings(max_examples=50)
    def test_iso_datetime_roundtrip(self, year, month, day, hour, minute):
        """ISO datetime parsing preserves date components."""
        dt = datetime(year, month, day, hour, minute, 0, tzinfo=timezone.utc)
        iso_str = dt.isoformat()
        
        parsed = parse_iso_datetime(iso_str)
        
        assert parsed is not None
        assert parsed.year == year
        assert parsed.month == month
        assert parsed.day == day
        assert parsed.hour == hour
        assert parsed.minute == minute


class TestConditionProperties:
    """Property-based tests for condition checking."""
    
    @given(
        flag_value=st.booleans(),
        condition_value=st.booleans(),
    )
    @settings(max_examples=20)
    def test_boolean_condition_match(self, flag_value, condition_value):
        """Boolean conditions match iff values are equal."""
        flags = {'test_flag': flag_value}
        conditions = {'test_flag': condition_value}
        
        result = check_conditions(flags, conditions)
        assert result == (flag_value == condition_value)
    
    @given(
        rsi=st.floats(0, 100),
        rsi_min=st.floats(0, 100),
        rsi_max=st.floats(0, 100),
    )
    @settings(max_examples=50)
    def test_range_condition_logic(self, rsi, rsi_min, rsi_max):
        """Range conditions work correctly."""
        assume(all(not pd.isna(x) for x in [rsi, rsi_min, rsi_max]))
        assume(rsi_min <= rsi_max)
        
        flags = {'rsi': rsi}
        conditions = {'rsi_min': rsi_min, 'rsi_max': rsi_max}
        
        result = check_conditions(flags, conditions)
        expected = rsi_min <= rsi <= rsi_max
        
        assert result == expected


class TestCooldownProperties:
    """Property-based tests for cooldown logic."""
    
    @given(cooldown_days=st.integers(1, 30))
    @settings(max_examples=20)
    def test_cooldown_expiry_future(self, cooldown_days):
        """Cooldown expiry is always in the future after update."""
        cooldowns = {}
        
        # Simulate a triggered signal
        triggered_signals = [
            {'signal_key': 'AAPL:KEY1', 'cooldown_days': cooldown_days}
        ]
        
        update_cooldowns(cooldowns, triggered_signals)
        
        # Verify cooldown was set
        if 'AAPL:KEY1' in cooldowns:
            expiry_str = cooldowns['AAPL:KEY1']
            # Parse timezone-aware or naive datetime
            try:
                expiry = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
            except ValueError:
                expiry = datetime.fromisoformat(expiry_str)
            
            # Make both timezone aware for comparison
            now = datetime.now(timezone.utc)
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            assert expiry > now
    
    @given(cooldown_days=st.integers(1, 30))
    @settings(max_examples=20)
    def test_active_cooldown_is_in_cooldown(self, cooldown_days):
        """Newly set cooldown is always active."""
        cooldowns = {}
        
        # Simulate a triggered signal
        triggered_signals = [
            {'signal_key': 'AAPL:KEY1', 'cooldown_days': cooldown_days}
        ]
        
        update_cooldowns(cooldowns, triggered_signals)
        
        # Check cooldown status
        result = is_in_cooldown('AAPL:KEY1', cooldowns, cooldown_days)
        assert result is True


class TestDataFrameProperties:
    """Property-based tests for DataFrame operations."""
    
    @given(
        prices=st.lists(
            st.floats(1, 1000, allow_nan=False, allow_infinity=False),
            min_size=50,
            max_size=300
        )
    )
    @settings(max_examples=20)
    def test_sma_never_exceeds_max(self, prices):
        """SMA never exceeds max price in window."""
        series = pd.Series(prices)
        
        # Calculate SMA-20
        sma = series.rolling(window=20).mean()
        valid = sma.dropna()
        
        if len(valid) > 0:
            assert all(valid <= max(prices))
            assert all(valid >= min(prices))
    
    @given(
        prices=st.lists(
            st.floats(1, 1000, allow_nan=False, allow_infinity=False),
            min_size=50,
            max_size=300
        )
    )
    @settings(max_examples=20)
    def test_ema_converges_to_price(self, prices):
        """EMA converges toward price over time."""
        series = pd.Series(prices)
        
        # Calculate EMA-20
        ema = series.ewm(span=20, adjust=False).mean()
        
        # EMA should be bounded by price range (approximately)
        assert all(ema >= min(prices) * 0.9)
        assert all(ema <= max(prices) * 1.1)


class TestEdgeCaseProperties:
    """Property-based tests for edge cases."""
    
    @given(value=st.one_of(st.none(), st.text()))
    @settings(max_examples=20)
    def test_parse_iso_datetime_handles_invalid(self, value):
        """parse_iso_datetime handles invalid input gracefully."""
        result = parse_iso_datetime(value)
        
        # Should return None or a datetime, never crash
        assert result is None or isinstance(result, datetime)
    
    @given(flags=st.dictionaries(st.text(min_size=1), st.booleans()))
    @settings(max_examples=20)
    def test_empty_conditions_always_match(self, flags):
        """Empty conditions always match any flags."""
        result = check_conditions(flags, {})
        assert result is True
    
    @given(
        rsi=st.one_of(
            st.floats(allow_nan=True, allow_infinity=True),
            st.just(float('nan')),
        )
    )
    @settings(max_examples=20)
    def test_score_handles_nan(self, rsi):
        """Scoring functions handle NaN gracefully."""
        # Should not crash
        result = score_rsi(rsi, "up")
        assert isinstance(result, (int, float))
    
    @given(
        ticker=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        key=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
    )
    @settings(max_examples=20)
    def test_cooldown_key_isolation(self, ticker, key):
        """Different signal keys have isolated cooldowns."""
        cooldowns = {}
        
        signal_key = f"{ticker}:{key}"
        triggered_signals = [{'signal_key': signal_key, 'cooldown_days': 1}]
        update_cooldowns(cooldowns, triggered_signals)
        
        # Different key should not be in cooldown
        other_key = f"{ticker}:{key}_other"
        result = is_in_cooldown(other_key, cooldowns, 1)
        assert result is False
        
        # Different ticker, same key should not be in cooldown  
        other_ticker_key = f"{ticker}_other:{key}"
        result = is_in_cooldown(other_ticker_key, cooldowns, 1)
        assert result is False


class TestInvariantProperties:
    """Property-based tests for invariants."""
    
    @given(rsi=st.floats(0, 100))
    @settings(max_examples=50)
    def test_rsi_score_monotonicity_for_up(self, rsi):
        """Lower RSI should score higher for 'up' direction."""
        assume(not pd.isna(rsi) and rsi >= 1 and rsi <= 99)
        
        # Compare with nearby values
        higher_rsi = min(100, rsi + 10)
        
        score_low = score_rsi(rsi, "up")
        score_high = score_rsi(higher_rsi, "up")
        
        # Lower RSI (more oversold) should score >= higher RSI for upside
        assert score_low >= score_high
    
    @given(williams_r=st.floats(-100, 0))
    @settings(max_examples=50)
    def test_williams_r_score_monotonicity_for_up(self, williams_r):
        """Lower Williams %R should score higher for 'up' direction."""
        assume(not pd.isna(williams_r) and williams_r >= -99 and williams_r <= -1)
        
        higher_wr = min(0, williams_r + 10)
        
        score_low = score_williams_r(williams_r, "up")
        score_high = score_williams_r(higher_wr, "up")
        
        # Lower Williams %R (more oversold) should score >= higher for upside
        assert score_low >= score_high

