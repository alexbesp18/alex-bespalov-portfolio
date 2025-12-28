"""
Tests for the backtest module.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta

from shared_core.backtest.models import (
    SignalEvent, SignalType, ConvictionLevel,
    BacktestResult, HorizonMetrics, HORIZON_DAYS
)
from shared_core.backtest.engine import BacktestEngine, ScoringConfig
from shared_core.backtest.report import generate_backtest_report


def create_mock_dataframe(days: int = 500) -> pd.DataFrame:
    """Create mock OHLCV data with indicators for testing."""
    dates = pd.date_range(end=date.today(), periods=days, freq='D')

    # Generate somewhat realistic price data
    np.random.seed(42)
    returns = np.random.normal(0.0005, 0.02, days)
    prices = 100 * np.exp(np.cumsum(returns))

    df = pd.DataFrame({
        'datetime': dates,
        'open': prices * (1 + np.random.uniform(-0.01, 0.01, days)),
        'high': prices * (1 + np.random.uniform(0, 0.02, days)),
        'low': prices * (1 - np.random.uniform(0, 0.02, days)),
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, days),
    })

    # Calculate mock indicators
    df['RSI'] = 50 + np.random.uniform(-30, 30, days)  # Random RSI
    df['MACD'] = np.random.uniform(-2, 2, days)
    df['MACD_SIGNAL'] = df['MACD'].rolling(9).mean()
    df['MACD_HIST'] = df['MACD'] - df['MACD_SIGNAL']
    df['SMA_50'] = df['close'].rolling(50).mean()
    df['SMA_200'] = df['close'].rolling(200).mean()
    df['ADX'] = 25 + np.random.uniform(-10, 15, days)

    return df


class TestSignalEvent:
    """Tests for SignalEvent model."""

    def test_signal_event_creation(self):
        """Test basic signal event creation."""
        signal = SignalEvent(
            ticker="AAPL",
            signal_date=date(2024, 1, 15),
            signal_type=SignalType.UPSIDE_REVERSAL,
            conviction=ConvictionLevel.HIGH,
            score=8.5,
            volume_ratio=1.5,
            adx_value=22.0,
            price_at_signal=150.0,
            return_2w=5.0,
            return_2m=12.0,
            return_6m=25.0,
        )

        assert signal.ticker == "AAPL"
        assert signal.score == 8.5
        assert signal.conviction == ConvictionLevel.HIGH
        assert signal.is_winner_2w is True
        assert signal.is_winner_2m is True
        assert signal.is_winner_6m is True

    def test_signal_event_loser(self):
        """Test signal event with negative returns."""
        signal = SignalEvent(
            ticker="MSFT",
            signal_date=date(2024, 1, 15),
            signal_type=SignalType.UPSIDE_REVERSAL,
            conviction=ConvictionLevel.MEDIUM,
            score=7.2,
            volume_ratio=1.1,
            adx_value=28.0,
            price_at_signal=400.0,
            return_2w=-3.0,
            return_2m=-8.0,
            return_6m=-15.0,
        )

        assert signal.is_winner_2w is False
        assert signal.is_winner_2m is False
        assert signal.is_winner_6m is False


class TestHorizonDays:
    """Tests for horizon day constants."""

    def test_horizon_days(self):
        """Verify trading day counts."""
        assert HORIZON_DAYS['2w'] == 10
        assert HORIZON_DAYS['2m'] == 42
        assert HORIZON_DAYS['6m'] == 126


class TestBacktestEngine:
    """Tests for BacktestEngine."""

    def test_engine_initialization(self):
        """Test engine initialization with default config."""
        engine = BacktestEngine()
        assert engine.config.high_score_min == 8.0
        assert engine.config.medium_score_min == 7.0
        assert engine.config.high_volume_min == 1.2

    def test_engine_with_custom_config(self):
        """Test engine with custom config."""
        config = ScoringConfig(
            high_score_min=8.5,
            medium_score_min=7.5,
            high_volume_min=1.5,
        )
        engine = BacktestEngine(scoring_config=config)

        assert engine.config.high_score_min == 8.5
        assert engine.config.medium_score_min == 7.5

    def test_volume_multiplier(self):
        """Test volume multiplier calculation."""
        engine = BacktestEngine()

        assert engine._get_volume_multiplier(2.5) == 1.2
        assert engine._get_volume_multiplier(1.5) == 1.1
        assert engine._get_volume_multiplier(1.0) == 1.0
        assert engine._get_volume_multiplier(0.8) == 0.7
        assert engine._get_volume_multiplier(0.5) == 0.5

    def test_adx_multiplier(self):
        """Test ADX multiplier calculation."""
        engine = BacktestEngine()

        assert engine._get_adx_multiplier(15) == 1.15
        assert engine._get_adx_multiplier(25) == 1.0
        assert engine._get_adx_multiplier(35) == 0.7
        assert engine._get_adx_multiplier(45) == 0.5

    def test_conviction_classification(self):
        """Test conviction level classification."""
        engine = BacktestEngine()

        # HIGH: score >= 8, volume >= 1.2, ADX < 35
        assert engine._classify_conviction(8.5, 1.5, 25) == ConvictionLevel.HIGH

        # Not HIGH if volume too low
        assert engine._classify_conviction(8.5, 1.0, 25) == ConvictionLevel.MEDIUM

        # Not HIGH if ADX too high
        assert engine._classify_conviction(8.5, 1.5, 40) == ConvictionLevel.MEDIUM

        # MEDIUM: score >= 7, volume >= 1.0
        assert engine._classify_conviction(7.5, 1.0, 40) == ConvictionLevel.MEDIUM

        # LOW: score >= 6
        assert engine._classify_conviction(6.5, 0.8, 45) == ConvictionLevel.LOW

        # NONE: below thresholds
        assert engine._classify_conviction(5.0, 0.5, 50) == ConvictionLevel.NONE

    def test_run_backtest_with_mock_data(self):
        """Test running backtest with mock data."""
        engine = BacktestEngine(verbose=False)

        # Create mock data for a few tickers
        ticker_data = {
            'AAPL': create_mock_dataframe(500),
            'MSFT': create_mock_dataframe(500),
        }

        result = engine.run_backtest(
            ticker_data=ticker_data,
            signal_type=SignalType.UPSIDE_REVERSAL,
        )

        assert isinstance(result, BacktestResult)
        assert result.tickers == ['AAPL', 'MSFT']
        assert result.signal_type == SignalType.UPSIDE_REVERSAL
        # May or may not have signals depending on random data
        assert isinstance(result.signals, list)

    def test_forward_return_calculation(self):
        """Test forward return calculation."""
        engine = BacktestEngine()
        df = create_mock_dataframe(500)
        df = df.set_index('datetime')

        signal_idx = 200
        price_at_signal = float(df.iloc[signal_idx]['close'])

        returns = engine._calculate_forward_returns(df, signal_idx, price_at_signal)

        # Should have all return and max gain/loss keys
        assert 'return_2w' in returns
        assert 'return_2m' in returns
        assert 'return_6m' in returns
        assert 'max_gain_2w' in returns
        assert 'max_loss_2w' in returns


class TestHorizonMetrics:
    """Tests for HorizonMetrics calculation."""

    def test_metrics_with_no_signals(self):
        """Test metrics calculation with empty signal list."""
        engine = BacktestEngine()
        metrics = engine._calculate_horizon_metrics([], '2w')

        assert metrics.total_signals == 0
        assert metrics.signals_with_data == 0
        assert metrics.win_rate == 0.0
        assert metrics.expectancy == 0.0

    def test_metrics_with_signals(self):
        """Test metrics calculation with sample signals."""
        signals = [
            SignalEvent(
                ticker="AAPL",
                signal_date=date(2024, 1, 1),
                signal_type=SignalType.UPSIDE_REVERSAL,
                conviction=ConvictionLevel.HIGH,
                score=8.5,
                volume_ratio=1.5,
                adx_value=22.0,
                price_at_signal=100.0,
                return_2w=10.0,
                max_gain_2w=15.0,
                max_loss_2w=-5.0,
            ),
            SignalEvent(
                ticker="MSFT",
                signal_date=date(2024, 1, 15),
                signal_type=SignalType.UPSIDE_REVERSAL,
                conviction=ConvictionLevel.HIGH,
                score=8.0,
                volume_ratio=1.3,
                adx_value=25.0,
                price_at_signal=400.0,
                return_2w=-5.0,
                max_gain_2w=3.0,
                max_loss_2w=-8.0,
            ),
        ]

        engine = BacktestEngine()
        metrics = engine._calculate_horizon_metrics(signals, '2w')

        assert metrics.total_signals == 2
        assert metrics.signals_with_data == 2
        assert metrics.winners == 1
        assert metrics.losers == 1
        assert metrics.win_rate == 50.0
        assert metrics.avg_return == 2.5  # (10 - 5) / 2
        assert metrics.best_return == 10.0
        assert metrics.worst_return == -5.0


class TestReportGeneration:
    """Tests for report generation."""

    def test_generate_report(self):
        """Test basic report generation."""
        result = BacktestResult(
            tickers=['AAPL', 'MSFT'],
            start_date=date(2023, 1, 1),
            end_date=date(2024, 1, 1),
            signal_type=SignalType.UPSIDE_REVERSAL,
            conviction_filter=None,
            signals=[],
            metrics_2w=HorizonMetrics(
                horizon='2w',
                total_signals=10,
                signals_with_data=10,
                winners=6,
                losers=4,
                win_rate=60.0,
                avg_return=5.0,
                median_return=4.0,
                best_return=20.0,
                worst_return=-10.0,
                avg_max_gain=8.0,
                avg_max_loss=-5.0,
                expectancy=2.0,
            ),
        )

        report = generate_backtest_report(result)

        assert "BACKTEST REPORT" in report
        assert "upside_reversal" in report
        assert "2 symbols" in report
        assert "60.0%" in report  # win rate
