"""
Integration tests for Stock Tracker application.

These tests verify that components work together correctly.
Note: These tests use mocking to avoid actual API calls.
"""
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from src.api_client import StockDataClient
from src.calculator import StockCalculator


class TestIntegration:
    """Integration tests for API client and calculator."""

    @patch.object(StockDataClient, '_get_client')
    def test_end_to_end_workflow(self, mock_get_client):
        """Test complete workflow from API fetch to metric calculation."""
        # Mock TwelveDataClient response
        mock_client = MagicMock()
        mock_data = pd.DataFrame(
            {
                "open": [100.0, 102.0, 101.0],
                "high": [102.0, 103.0, 102.5],
                "low": [99.0, 101.0, 100.5],
                "close": [101.0, 102.5, 101.5],
                "volume": [1000000, 1100000, 1050000],
            },
            index=pd.date_range("2023-01-01", periods=3),
        )
        mock_client.get_dataframe.return_value = mock_data
        mock_get_client.return_value = mock_client

        # Fetch data
        hist_data = StockDataClient.get_historical_data("AAPL", "1 year")
        assert hist_data is not None

        # Calculate metrics
        metrics = StockCalculator.calculate_metrics(hist_data)
        assert metrics is not None

        # Verify metrics structure
        assert "start_price" in metrics
        assert "current_price" in metrics
        assert metrics["start_price"] == 101.0
        assert metrics["current_price"] == 101.5

    @patch.object(StockDataClient, '_get_client')
    def test_integration_with_empty_data(self, mock_get_client):
        """Test integration when API returns empty data."""
        mock_client = MagicMock()
        mock_client.get_dataframe.return_value = pd.DataFrame()
        mock_get_client.return_value = mock_client

        hist_data = StockDataClient.get_historical_data("INVALID", "1 year")
        assert hist_data is None

        # Calculator should handle None gracefully
        metrics = StockCalculator.calculate_metrics(hist_data)
        assert metrics is None

    @patch.object(StockDataClient, '_get_client')
    def test_integration_with_single_data_point(self, mock_get_client):
        """Test integration with insufficient data points."""
        # Single row DataFrame
        mock_client = MagicMock()
        mock_data = pd.DataFrame(
            {"close": [100.0]}, index=[pd.Timestamp("2023-01-01")]
        )
        mock_client.get_dataframe.return_value = mock_data
        mock_get_client.return_value = mock_client

        hist_data = StockDataClient.get_historical_data("AAPL", "1 year")
        assert hist_data is not None

        # Calculator should return None for insufficient data
        metrics = StockCalculator.calculate_metrics(hist_data)
        assert metrics is None

    def test_format_display_with_calculated_metrics(self):
        """Test formatting metrics that were calculated from real data."""
        # Create realistic metrics
        metrics = {
            "start_price": 150.0,
            "min_price": 140.0,
            "max_price": 160.0,
            "current_price": 155.0,
            "current_percentile": 96.88,
            "price_range": 20.0,
            "change_percent": 3.33,
        }

        output = StockCalculator.format_metrics_display("MSFT", "Microsoft", metrics)
        assert "MSFT" in output
        assert "Microsoft" in output
        assert "3.33" in output or "+3.33" in output
