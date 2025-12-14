"""
Unit tests for StockCalculator class.
"""
import pandas as pd
import pytest

from src.calculator import StockCalculator


class TestStockCalculator:
    """Test suite for StockCalculator."""

    def test_calculate_metrics_basic(self, sample_historical_data):
        """Test basic metric calculation with valid data."""
        metrics = StockCalculator.calculate_metrics(sample_historical_data)

        assert metrics is not None
        assert "start_price" in metrics
        assert "current_price" in metrics
        assert "min_price" in metrics
        assert "max_price" in metrics
        assert "change_percent" in metrics
        assert "current_percentile" in metrics
        assert "price_range" in metrics

        # Verify start price is first close price
        assert metrics["start_price"] == 101.0
        # Verify current price is last close price
        assert metrics["current_price"] == 110.5

    def test_calculate_metrics_empty_dataframe(self, empty_dataframe):
        """Test that empty DataFrame returns None."""
        metrics = StockCalculator.calculate_metrics(empty_dataframe)
        assert metrics is None

    def test_calculate_metrics_none_input(self):
        """Test that None input returns None."""
        metrics = StockCalculator.calculate_metrics(None)
        assert metrics is None

    def test_calculate_metrics_single_row(self, single_row_dataframe):
        """Test calculation with single row (edge case)."""
        metrics = StockCalculator.calculate_metrics(single_row_dataframe)
        # Should return None because we need at least 2 data points
        assert metrics is None

    def test_calculate_metrics_missing_close_column(self):
        """Test that missing 'Close' column returns None."""
        df = pd.DataFrame({"Open": [100.0, 101.0]})
        metrics = StockCalculator.calculate_metrics(df)
        assert metrics is None

    def test_calculate_metrics_percentile_calculation(self):
        """Test percentile calculation correctness."""
        # Create data where current = max (should be 100%)
        data = pd.DataFrame(
            {"Close": [100.0, 90.0, 110.0]}, index=pd.date_range("2023-01-01", periods=3)
        )
        metrics = StockCalculator.calculate_metrics(data)
        assert metrics is not None
        assert metrics["current_percentile"] == 100.0

    def test_calculate_metrics_change_percent(self):
        """Test percentage change calculation."""
        # Start: 100, Current: 110, Change: +10%
        data = pd.DataFrame(
            {"Close": [100.0, 110.0]}, index=pd.date_range("2023-01-01", periods=2)
        )
        metrics = StockCalculator.calculate_metrics(data)
        assert metrics is not None
        assert metrics["change_percent"] == 10.0

    def test_calculate_metrics_negative_change(self):
        """Test negative percentage change."""
        # Start: 100, Current: 90, Change: -10%
        data = pd.DataFrame(
            {"Close": [100.0, 90.0]}, index=pd.date_range("2023-01-01", periods=2)
        )
        metrics = StockCalculator.calculate_metrics(data)
        assert metrics is not None
        assert metrics["change_percent"] == -10.0

    def test_format_metrics_display_valid(self, sample_metrics):
        """Test formatting with valid metrics."""
        output = StockCalculator.format_metrics_display(
            "AAPL", "Apple Inc.", sample_metrics
        )
        assert "AAPL" in output
        assert "Apple Inc." in output
        assert "$100.00" in output or "100.00" in output

    def test_format_metrics_display_none(self):
        """Test formatting with None metrics."""
        output = StockCalculator.format_metrics_display("AAPL", "Apple Inc.", None)
        assert "Data unavailable" in output

    def test_format_metrics_display_empty_dict(self):
        """Test formatting with empty metrics dict."""
        output = StockCalculator.format_metrics_display("AAPL", "Apple Inc.", {})
        assert "Data unavailable" in output

    def test_metrics_rounding(self):
        """Test that metrics are properly rounded to 2 decimal places."""
        # Use data that will produce non-round numbers
        data = pd.DataFrame(
            {"Close": [100.123456, 110.789012]},
            index=pd.date_range("2023-01-01", periods=2),
        )
        metrics = StockCalculator.calculate_metrics(data)
        assert metrics is not None
        # All values should be rounded to 2 decimal places
        assert metrics["start_price"] == 100.12
        assert metrics["current_price"] == 110.79

