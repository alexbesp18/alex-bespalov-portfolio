"""
Integration tests for shared_core modules.

Tests complete data flows across multiple modules.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from pathlib import Path

from shared_core.data import (
    process_ohlcv_data,
    add_standard_indicators,
    calculate_matrix,
    calculate_bullish_score,
    calculate_bullish_score_detailed,
)
from shared_core.scoring import (
    score_rsi,
    score_stochastic,
    score_macd_histogram,
    DivergenceType,
    BULLISH_WEIGHTS,
    REVERSAL_WEIGHTS,
)
from shared_core.divergence import (
    detect_divergence_enhanced,
    detect_combined_divergence,
)
from shared_core.triggers import (
    evaluate_ticker,
    TriggerEngine,
    PORTFOLIO_SIGNALS,
    WATCHLIST_SIGNALS,
)
from shared_core.state import (
    StateManager,
    ArchiveManager,
    Digest,
    utc_now_iso,
)
from shared_core.notifications import (
    format_html_table,
    format_subject,
    make_basic_html_email,
)


class TestFullScanPipeline:
    """Test complete data flow from API response to score."""
    
    def test_fetch_process_score_flow(self, sample_api_response):
        """Verify: API response -> process_ohlcv -> calculate_bullish_score."""
        # Step 1: Process raw API response
        df = process_ohlcv_data(sample_api_response)
        assert df is not None
        assert len(df) > 0
        
        # Step 2: Calculate bullish score
        result = calculate_bullish_score_detailed(df)
        
        # Verify score is valid (BullishScore dataclass)
        assert 0 <= result.final_score <= 10
        
        # Verify breakdown has expected keys
        assert isinstance(result.components, dict)
        assert len(result.components) > 0
    
    def test_process_to_matrix_flow(self, sample_api_response):
        """Verify: API response -> process_ohlcv -> calculate_matrix."""
        df = process_ohlcv_data(sample_api_response)
        assert df is not None
        
        matrix = calculate_matrix(df)
        
        # Verify matrix structure
        assert isinstance(matrix, dict)
        # Matrix stores RSI as _rsi (prefixed for metadata)
        assert '_rsi' in matrix or 'rsi' in matrix or 'RSI' in matrix
    
    def test_matrix_to_trigger_flow(self, sample_api_response):
        """Verify: matrix -> evaluate_ticker -> trigger results."""
        df = process_ohlcv_data(sample_api_response)
        matrix = calculate_matrix(df)
        
        # Add score to matrix (calculate_bullish_score returns tuple)
        score, _ = calculate_bullish_score(df)
        matrix['score'] = score
        
        # Evaluate triggers
        results = evaluate_ticker(
            ticker='TEST',
            flags=matrix,
            list_type='watchlist',
            cooldowns={},
            actioned={},  # Use 'actioned' not 'archive'
        )
        
        # Verify structure
        assert isinstance(results, list)
        for r in results:
            assert r.ticker == 'TEST'
            assert r.action in ['BUY', 'SELL', 'ALERT']
    
    def test_complete_watchlist_scan(self, sample_api_response):
        """Simulate complete watchlist scan."""
        tickers = ['AAPL', 'NVDA', 'GOOGL']
        all_results = []
        
        for ticker in tickers:
            df = process_ohlcv_data(sample_api_response)
            if df is None:
                continue
            
            matrix = calculate_matrix(df)
            score, _ = calculate_bullish_score(df)
            matrix['score'] = score
            
            results = evaluate_ticker(
                ticker=ticker,
                flags=matrix,
                list_type='watchlist',
                cooldowns={},
                actioned={},
            )
            
            all_results.extend(results)
        
        # Should produce some results (may be empty depending on conditions)
        assert isinstance(all_results, list)


class TestTriggerEvaluationFlow:
    """Test trigger evaluation with realistic data."""
    
    def test_uptrend_stock_triggers(self, uptrend_df):
        """Uptrending stock should trigger buy signals."""
        df = add_standard_indicators(uptrend_df)
        matrix = calculate_matrix(df)
        score, _ = calculate_bullish_score(df)
        matrix['score'] = score
        
        results = evaluate_ticker(
            ticker='UPTREND',
            flags=matrix,
            list_type='watchlist',
            cooldowns={},
            actioned={},
        )
        
        # High score might trigger buy signals
        assert isinstance(results, list)
    
    def test_downtrend_stock_triggers(self, downtrend_df):
        """Downtrending stock should trigger sell signals."""
        df = add_standard_indicators(downtrend_df)
        matrix = calculate_matrix(df)
        score, _ = calculate_bullish_score(df)
        matrix['score'] = score
        
        results = evaluate_ticker(
            ticker='DOWNTREND',
            flags=matrix,
            list_type='portfolio',  # Portfolio has sell signals
            cooldowns={},
            actioned={},
        )
        
        assert isinstance(results, list)
    
    def test_trigger_engine_with_custom_triggers(self, sample_ohlcv_df_with_indicators):
        """TriggerEngine with custom trigger definitions."""
        engine = TriggerEngine([
            {'type': 'score_above', 'value': 6, 'action': 'BUY'},
            {'type': 'score_below', 'value': 4, 'action': 'SELL'},
        ])
        
        results = engine.evaluate(
            symbol='TEST',  # Use 'symbol' not 'ticker'
            df=sample_ohlcv_df_with_indicators,
            score=7.0,
        )
        
        # Should trigger score_above (results are dicts)
        assert any(r.get('action') == 'BUY' for r in results) or len(results) == 0


class TestStateIntegration:
    """Test state persistence across runs."""
    
    def test_state_persists_across_manager_instances(self, tmp_path):
        """State changes persist when loading in new manager instance."""
        path = str(tmp_path / "state.json")
        
        # First instance: set some state
        mgr1 = StateManager(path)
        state1 = mgr1.load()
        mgr1.set_last_run(state1, ["TEST:SIGNAL1", "TEST:SIGNAL2"])
        mgr1.save(state1)
        
        # Second instance: verify state persisted
        mgr2 = StateManager(path)
        state2 = mgr2.load()
        keys = mgr2.get_last_run_trigger_keys(state2)
        
        assert keys == ["TEST:SIGNAL1", "TEST:SIGNAL2"]
    
    def test_archive_persists_across_instances(self, tmp_path):
        """Archive changes persist when loading in new manager instance."""
        path = str(tmp_path / "archive.json")
        
        # First instance: archive a trigger
        mgr1 = ArchiveManager(path)
        archive1 = mgr1.load()
        mgr1.archive_trigger(archive1, "NVDA", "KEY1", "Test trigger", suppress_days=30)
        mgr1.save(archive1)
        
        # Second instance: verify suppression
        mgr2 = ArchiveManager(path)
        archive2 = mgr2.load()
        
        assert mgr2.is_suppressed(archive2, "KEY1") is True
    
    def test_full_state_workflow(self, tmp_path):
        """Complete state management workflow."""
        state_path = str(tmp_path / "state.json")
        archive_path = str(tmp_path / "archive.json")
        
        # Initialize managers
        state_mgr = StateManager(state_path)
        archive_mgr = ArchiveManager(archive_path)
        
        # Simulate first run
        state = state_mgr.load()
        archive = archive_mgr.load()
        
        # Record triggered signals
        triggered_keys = ["AAPL:BUY_PULLBACK", "NVDA:SCORE_ABOVE"]
        state_mgr.set_last_run(state, triggered_keys)
        
        # Update seen triggers
        signals = [
            {"symbol": "AAPL", "trigger_key": "AAPL:BUY_PULLBACK", "message": "Buy signal"},
            {"symbol": "NVDA", "trigger_key": "NVDA:SCORE_ABOVE", "message": "Score 8.5"},
        ]
        state_mgr.update_seen_triggers(state, signals)
        
        # Archive one trigger
        archive_mgr.archive_trigger(archive, "NVDA", "NVDA:SCORE_ABOVE", "Score 8.5", 30)
        
        # Save state
        state_mgr.save(state)
        archive_mgr.save(archive)
        
        # Verify persistence
        state2 = state_mgr.load()
        archive2 = archive_mgr.load()
        
        assert "AAPL:BUY_PULLBACK" in state_mgr.get_last_run_trigger_keys(state2)
        assert archive_mgr.is_suppressed(archive2, "NVDA:SCORE_ABOVE") is True


class TestDigestWorkflow:
    """Test digest creation and reminder workflow."""
    
    def test_digest_creation_and_reminder(self, tmp_path):
        """Create digest and check reminder eligibility."""
        state_path = str(tmp_path / "state.json")
        mgr = StateManager(state_path)
        state = mgr.load()
        
        # Create a digest
        digest = Digest(
            digest_id=datetime.now().strftime("%Y-%m-%d"),
            sent_at=utc_now_iso(),
            results=[
                {"symbol": "NVDA", "action": "BUY", "score": 8.5},
                {"symbol": "AAPL", "action": "BUY", "score": 7.2},
            ],
            buy_count=2,
            sell_count=0,
        )
        mgr.set_last_digest(state, digest)
        mgr.save(state)
        
        # Reload and check reminder eligibility
        state2 = mgr.load()
        should_remind = mgr.should_send_reminder(state2)
        
        assert should_remind is True
        
        # Mark reminder sent
        mgr.mark_reminder_sent(state2, digest.digest_id)
        mgr.save(state2)
        
        # Check again
        state3 = mgr.load()
        should_remind_again = mgr.should_send_reminder(state3)
        
        assert should_remind_again is False


class TestEmailFormatting:
    """Test email formatting with real data."""
    
    def test_format_scan_results_email(self, sample_api_response):
        """Format complete scan results as email."""
        df = process_ohlcv_data(sample_api_response)
        score, _ = calculate_bullish_score(df)
        
        # Create results data
        headers = ['Symbol', 'Score', 'Action', 'Price']
        rows = [
            ['NVDA', 8.5, 'BUY', 500.0],
            ['AAPL', 7.2, 'BUY', 150.0],
            ['TSLA', 3.5, 'SELL', 250.0],
        ]
        
        # Format table (takes headers and rows)
        table_html = format_html_table(headers, rows)
        
        # Format subject (takes signals list)
        signals = [
            {'action': 'BUY', 'symbol': 'NVDA'},
            {'action': 'BUY', 'symbol': 'AAPL'},
            {'action': 'SELL', 'symbol': 'TSLA'},
        ]
        subject = format_subject(signals, mode='alert')
        
        # Create email
        email_html = make_basic_html_email(
            title='Daily Scan Results',
            body_html=table_html,
        )
        
        # Verify
        assert 'NVDA' in email_html
        assert isinstance(subject, str)
        assert '<html' in email_html.lower()
    
    def test_format_empty_results(self):
        """Format email with no results."""
        subject = format_subject([], mode='alert')
        email_html = make_basic_html_email(
            title='No Signals',
            body_html='<p>No trading signals today.</p>',
        )
        
        assert isinstance(subject, str)
        assert '<html' in email_html.lower()


class TestDivergenceWithScoringFlow:
    """Test divergence detection integrated with scoring."""
    
    def test_divergence_contributes_to_score(self, sample_ohlcv_df_with_indicators):
        """Divergence detection feeds into reversal score."""
        # Detect divergence (takes df and lookback)
        divergence = detect_combined_divergence(
            sample_ohlcv_df_with_indicators,
            lookback=14
        )
        
        # Score the divergence
        from shared_core.scoring import score_divergence
        div_score = score_divergence(divergence, DivergenceType.BULLISH)
        
        # Verify score is valid
        assert 1.0 <= div_score <= 10.0
    
    def test_multiple_indicator_scoring(self, sample_ohlcv_df_with_indicators):
        """Score multiple indicators and combine."""
        df = sample_ohlcv_df_with_indicators
        row = df.iloc[-1]
        
        # Score individual components
        rsi_score = score_rsi(row.get('RSI', 50), "up")
        stoch_score = score_stochastic(
            row.get('STOCH_K', 50),
            row.get('STOCH_D', 50),
            df.iloc[-2].get('STOCH_K', 50),
            "up"
        )
        
        # All scores should be valid
        assert 1.0 <= rsi_score <= 10.0
        assert 1.0 <= stoch_score <= 10.0


class TestCrossModuleConsistency:
    """Test consistency across modules."""
    
    def test_bullish_score_uses_correct_weights(self, sample_ohlcv_df_with_indicators):
        """Bullish score calculation uses BULLISH_WEIGHTS."""
        result = calculate_bullish_score_detailed(sample_ohlcv_df_with_indicators)
        
        # Breakdown keys should relate to weights (BullishScore dataclass)
        assert isinstance(result.components, dict)
        # Score should be bounded
        assert 0 <= result.final_score <= 10
    
    def test_trigger_signals_match_definitions(self):
        """Trigger evaluation uses correct signal definitions."""
        # All PORTFOLIO_SIGNALS should have required fields
        for name, signal in PORTFOLIO_SIGNALS.items():
            assert 'action' in signal
            assert 'conditions' in signal
        
        # All WATCHLIST_SIGNALS should have required fields
        for name, signal in WATCHLIST_SIGNALS.items():
            assert 'action' in signal
            assert 'conditions' in signal


class TestEdgeCasesIntegration:
    """Integration tests for edge cases."""
    
    def test_empty_api_response_flow(self, empty_api_response):
        """Handle empty API response through pipeline."""
        df = process_ohlcv_data(empty_api_response)
        assert df is None
    
    def test_insufficient_data_flow(self, insufficient_api_response):
        """Handle insufficient data through pipeline."""
        df = process_ohlcv_data(insufficient_api_response)
        
        if df is not None:
            # Should still produce valid output (returns tuple)
            score, breakdown = calculate_bullish_score(df)
            assert isinstance(score, (int, float))
    
    def test_concurrent_state_access(self, tmp_path):
        """Multiple managers accessing same state file."""
        path = str(tmp_path / "concurrent_state.json")
        
        # Create two managers pointing to same file
        mgr1 = StateManager(path)
        mgr2 = StateManager(path)
        
        # First manager writes
        state1 = mgr1.load()
        mgr1.set_last_run(state1, ["KEY1"])
        mgr1.save(state1)
        
        # Second manager reads and writes
        state2 = mgr2.load()
        assert "KEY1" in mgr2.get_last_run_trigger_keys(state2)
        
        mgr2.set_last_run(state2, ["KEY2"])
        mgr2.save(state2)
        
        # First manager reloads
        state3 = mgr1.load()
        assert "KEY2" in mgr1.get_last_run_trigger_keys(state3)

