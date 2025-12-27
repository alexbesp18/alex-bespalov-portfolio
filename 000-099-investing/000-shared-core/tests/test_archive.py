"""Tests for the archive module (Supabase archival)."""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch

from shared_core.archive.supabase_client import (
    IndicatorSnapshot,
    SupabaseArchiver,
    archive_daily_indicators,
    get_historical_data,
)
from shared_core.archive.aggregator import (
    MonthlyAggregate,
    MonthlyAggregator,
    run_monthly_aggregation,
)


class TestIndicatorSnapshot:
    """Tests for the IndicatorSnapshot dataclass."""

    def test_basic_creation(self):
        """Test creating a basic snapshot."""
        snapshot = IndicatorSnapshot(
            date="2024-01-15",
            symbol="AAPL",
            close=150.0,
            rsi=45.0,
        )
        assert snapshot.date == "2024-01-15"
        assert snapshot.symbol == "AAPL"
        assert snapshot.close == 150.0
        assert snapshot.rsi == 45.0
        assert snapshot.macd is None

    def test_to_dict(self):
        """Test conversion to dictionary."""
        snapshot = IndicatorSnapshot(
            date="2024-01-15",
            symbol="AAPL",
            close=150.0,
            rsi=45.0,
            stoch_k=30.0,
            bullish_score=7.5,
        )
        result = snapshot.to_dict()
        assert result["date"] == "2024-01-15"
        assert result["symbol"] == "AAPL"
        assert result["close"] == 150.0
        assert result["rsi"] == 45.0
        assert result["stoch_k"] == 30.0
        assert result["bullish_score"] == 7.5
        # None values are excluded from sparse dict to avoid overwriting
        assert "macd" not in result

    def test_all_fields(self):
        """Test snapshot with all fields populated."""
        snapshot = IndicatorSnapshot(
            date="2024-01-15",
            symbol="AAPL",
            close=150.0,
            rsi=45.0,
            stoch_k=30.0,
            stoch_d=35.0,
            williams_r=-60.0,
            roc=2.5,
            macd=1.5,
            macd_signal=1.2,
            macd_hist=0.3,
            adx=25.0,
            sma_20=148.0,
            sma_50=145.0,
            sma_200=140.0,
            bb_upper=155.0,
            bb_lower=145.0,
            bb_position=0.5,
            atr=3.0,
            volume=1000000,
            volume_ratio=1.2,
            obv=5000000,
            bullish_score=7.5,
            reversal_score=6.0,
            oversold_score=5.0,
            action="BUY",
        )
        d = snapshot.to_dict()
        assert d["williams_r"] == -60.0
        assert d["adx"] == 25.0
        assert d["action"] == "BUY"


class TestSupabaseArchiver:
    """Tests for the SupabaseArchiver class."""

    def test_not_configured_without_credentials(self):
        """Test archiver reports not configured without credentials."""
        archiver = SupabaseArchiver(url=None, key=None)
        assert not archiver.is_configured

    def test_configured_with_credentials(self):
        """Test archiver reports configured with credentials."""
        archiver = SupabaseArchiver(url="https://test.supabase.co", key="test-key")
        assert archiver.is_configured

    def test_archive_snapshots_empty_list(self):
        """Test archiving empty list returns 0."""
        archiver = SupabaseArchiver(url="https://test.supabase.co", key="test-key")
        result = archiver.archive_snapshots([])
        assert result == 0

    def test_archive_snapshots_not_configured(self):
        """Test archiving when not configured returns 0."""
        archiver = SupabaseArchiver(url=None, key=None)
        snapshots = [
            IndicatorSnapshot(date="2024-01-15", symbol="AAPL", close=150.0)
        ]
        result = archiver.archive_snapshots(snapshots)
        assert result == 0

    def test_get_history_not_configured(self):
        """Test get_history when not configured returns empty list."""
        archiver = SupabaseArchiver(url=None, key=None)
        result = archiver.get_history("AAPL")
        assert result == []

    def test_get_latest_scores_not_configured(self):
        """Test get_latest_scores when not configured returns empty list."""
        archiver = SupabaseArchiver(url=None, key=None)
        result = archiver.get_latest_scores()
        assert result == []

    @patch.dict('os.environ', {'SUPABASE_URL': '', 'SUPABASE_SERVICE_KEY': ''})
    def test_env_var_fallback_empty(self):
        """Test empty env vars don't configure archiver."""
        archiver = SupabaseArchiver()
        assert not archiver.is_configured


class TestArchiveDailyIndicators:
    """Tests for the archive_daily_indicators convenience function."""

    def test_empty_results(self):
        """Test with empty results returns 0."""
        result = archive_daily_indicators([])
        assert result == 0

    @patch.dict('os.environ', {'SUPABASE_URL': '', 'SUPABASE_SERVICE_KEY': ''})
    def test_not_configured_returns_zero(self):
        """Test returns 0 when Supabase not configured."""
        # Reset singleton
        import shared_core.archive.supabase_client as mod
        mod._archiver = None

        results = [{"symbol": "AAPL", "close": 150.0, "rsi": 45.0}]
        result = archive_daily_indicators(results)
        assert result == 0

    def test_list_format_parsing(self):
        """Test parsing list of dicts format (standard for all scanners)."""
        # This tests the parsing logic without actual Supabase connection
        results = [
            {"symbol": "AAPL", "close": 150.0, "rsi": 45.0, "bullish_score": 7.5},
            {"symbol": "GOOGL", "close": 140.0, "rsi": 35.0, "bullish_score": 8.0},
        ]
        # Should not raise, returns 0 when not configured
        result = archive_daily_indicators(results, score_type="bullish")
        assert result == 0

    def test_list_dict_format_parsing(self):
        """Test parsing list of dicts format (from 009-reversals)."""
        results = [
            {"symbol": "AAPL", "_price": 150.0, "_rsi": 45.0, "score": 7.5},
            {"symbol": "GOOGL", "_price": 140.0, "_rsi": 35.0, "score": 8.0},
        ]
        result = archive_daily_indicators(results, score_type="reversal")
        assert result == 0

    def test_list_dict_with_all_indicators(self):
        """Test parsing list of dicts with full indicator data."""
        results = [
            {
                "symbol": "AAPL",
                "close": 150.0,
                "rsi": 45.0,
                "stoch_k": 30.0,
                "stoch_d": 35.0,
                "williams_r": -60.0,
                "roc": 2.5,
                "macd": 1.5,
                "macd_signal": 1.2,
                "macd_hist": 0.3,
                "adx": 25.0,
                "sma_20": 148.0,
                "sma_50": 145.0,
                "sma_200": 140.0,
                "bb_upper": 155.0,
                "bb_lower": 145.0,
                "bb_position": 0.5,
                "atr": 3.0,
                "volume": 1000000,
                "volume_ratio": 1.2,
                "obv": 5000000,
                "bullish_score": 7.5,
            },
        ]
        # Should not raise, returns 0 when not configured
        result = archive_daily_indicators(results, score_type="bullish")
        assert result == 0


class TestGetHistoricalData:
    """Tests for the get_historical_data convenience function."""

    @patch.dict('os.environ', {'SUPABASE_URL': '', 'SUPABASE_SERVICE_KEY': ''})
    def test_not_configured_returns_empty(self):
        """Test returns empty list when not configured."""
        import shared_core.archive.supabase_client as mod
        mod._archiver = None

        result = get_historical_data("AAPL")
        assert result == []


class TestMonthlyAggregate:
    """Tests for the MonthlyAggregate dataclass."""

    def test_basic_creation(self):
        """Test creating a basic aggregate."""
        agg = MonthlyAggregate(
            month="2024-01-01",
            symbol="AAPL",
            open_price=140.0,
            close_price=150.0,
            high_price=155.0,
            low_price=138.0,
            monthly_return=7.14,
            days_oversold=3,
            days_overbought=5,
        )
        assert agg.month == "2024-01-01"
        assert agg.symbol == "AAPL"
        assert agg.monthly_return == 7.14
        assert agg.days_oversold == 3
        assert agg.days_overbought == 5

    def test_to_dict(self):
        """Test conversion to dictionary."""
        agg = MonthlyAggregate(
            month="2024-01-01",
            symbol="AAPL",
            open_price=140.0,
            close_price=150.0,
            high_price=155.0,
            low_price=138.0,
            monthly_return=7.14,
            avg_rsi=50.0,
            avg_bullish_score=8.5,
            days_oversold=2,
            days_overbought=4,
            buy_signals=3,
            sell_signals=1,
        )
        result = agg.to_dict()
        assert result["month"] == "2024-01-01"
        assert result["symbol"] == "AAPL"
        assert result["avg_rsi"] == 50.0
        assert result["avg_bullish_score"] == 8.5
        assert result["monthly_return"] == 7.14
        assert result["days_oversold"] == 2
        assert result["days_overbought"] == 4
        assert result["buy_signals"] == 3
        assert result["sell_signals"] == 1


class TestMonthlyAggregator:
    """Tests for the MonthlyAggregator class."""

    def test_not_configured_without_credentials(self):
        """Test aggregator reports not configured without credentials."""
        aggregator = MonthlyAggregator(url=None, key=None)
        assert not aggregator.is_configured

    def test_configured_with_credentials(self):
        """Test aggregator reports configured with credentials."""
        aggregator = MonthlyAggregator(
            url="https://test.supabase.co",
            key="test-key"
        )
        assert aggregator.is_configured

    def test_get_months_not_configured(self):
        """Test get_months returns empty when not configured."""
        aggregator = MonthlyAggregator(url=None, key=None)
        result = aggregator.get_months_to_aggregate()
        assert result == []

    def test_aggregate_month_not_configured(self):
        """Test aggregate_month returns 0 when not configured."""
        aggregator = MonthlyAggregator(url=None, key=None)
        result = aggregator.aggregate_month("2024-01")
        assert result == 0

    def test_cleanup_old_daily_not_configured(self):
        """Test cleanup returns 0 when not configured."""
        aggregator = MonthlyAggregator(url=None, key=None)
        result = aggregator.cleanup_old_daily("2024-01")
        assert result == 0

    def test_run_aggregation_not_configured(self):
        """Test run_aggregation returns zeros when not configured."""
        aggregator = MonthlyAggregator(url=None, key=None)
        result = aggregator.run_aggregation()
        assert result == {"months": 0, "aggregates": 0, "deleted": 0}

    def test_retention_days_constant(self):
        """Test retention days constant is set."""
        assert MonthlyAggregator.RETENTION_DAYS == 90


class TestRunMonthlyAggregation:
    """Tests for the run_monthly_aggregation convenience function."""

    @patch.dict('os.environ', {'SUPABASE_URL': '', 'SUPABASE_SERVICE_KEY': ''})
    def test_not_configured_returns_zeros(self):
        """Test returns zeros when not configured."""
        import shared_core.archive.aggregator as mod
        mod._aggregator = None

        result = run_monthly_aggregation()
        assert result == {"months": 0, "aggregates": 0, "deleted": 0}


class TestCreateAggregate:
    """Tests for the _create_aggregate method."""

    def test_create_aggregate_from_rows(self):
        """Test creating aggregate from daily rows."""
        aggregator = MonthlyAggregator(
            url="https://test.supabase.co",
            key="test-key"
        )

        rows = [
            {"date": "2024-01-02", "close": 140.0, "rsi": 25.0, "bullish_score": 7.0, "action": "BUY"},
            {"date": "2024-01-03", "close": 145.0, "rsi": 50.0, "bullish_score": 7.5, "action": "HOLD"},
            {"date": "2024-01-04", "close": 150.0, "rsi": 75.0, "bullish_score": 8.0, "action": "SELL"},
        ]

        agg = aggregator._create_aggregate("2024-01", "AAPL", rows)

        assert agg.month == "2024-01-01"  # YYYY-MM-01 format
        assert agg.symbol == "AAPL"
        assert agg.open_price == 140.0
        assert agg.close_price == 150.0
        assert agg.high_price == 150.0
        assert agg.low_price == 140.0
        assert agg.avg_rsi == 50.0
        assert agg.min_rsi == 25.0
        assert agg.max_rsi == 75.0
        assert agg.avg_bullish_score == 7.5
        assert agg.days_oversold == 1  # RSI 25 < 30
        assert agg.days_overbought == 1  # RSI 75 > 70
        assert agg.buy_signals == 1
        assert agg.sell_signals == 1
        # Monthly return: (150 - 140) / 140 * 100 = 7.1429
        assert agg.monthly_return == 7.1429

    def test_create_aggregate_with_none_values(self):
        """Test creating aggregate handles None values gracefully."""
        aggregator = MonthlyAggregator(
            url="https://test.supabase.co",
            key="test-key"
        )

        rows = [
            {"date": "2024-01-02", "close": 140.0, "rsi": None, "bullish_score": None},
            {"date": "2024-01-03", "close": 145.0, "rsi": 50.0, "bullish_score": None},
        ]

        agg = aggregator._create_aggregate("2024-01", "AAPL", rows)

        assert agg.avg_rsi == 50.0  # Only one non-None value
        assert agg.avg_bullish_score is None  # All None
        assert agg.days_oversold == 0  # None RSI values don't count
        assert agg.days_overbought == 0


class TestModuleExports:
    """Tests for module-level exports."""

    def test_archive_module_exports(self):
        """Test that archive module exports expected items."""
        from shared_core.archive import (
            SupabaseArchiver,
            archive_daily_indicators,
            get_historical_data,
            MonthlyAggregator,
            run_monthly_aggregation,
        )
        assert SupabaseArchiver is not None
        assert archive_daily_indicators is not None
        assert get_historical_data is not None
        assert MonthlyAggregator is not None
        assert run_monthly_aggregation is not None

    def test_main_module_exports(self):
        """Test that main shared_core module exports archive items."""
        from shared_core import (
            SupabaseArchiver,
            archive_daily_indicators,
            get_historical_data,
            MonthlyAggregator,
            run_monthly_aggregation,
        )
        assert SupabaseArchiver is not None
        assert archive_daily_indicators is not None
