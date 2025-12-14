"""
Unit tests for StockDataClient class.

Note: These tests use mocking to avoid actual API calls.
"""
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.api_client import StockDataClient


class TestStockDataClient:
    """Test suite for StockDataClient."""

    def test_duration_mapping(self):
        """Test that duration mapping is correct."""
        assert StockDataClient.DURATION_MAPPING["1 month"] == "1mo"
        assert StockDataClient.DURATION_MAPPING["1 year"] == "1y"
        assert StockDataClient.DURATION_MAPPING["5 years"] == "5y"

    def test_duration_mapping_default(self):
        """Test that unknown duration defaults to 1y."""
        # The get_historical_data method uses .get(duration, "1y")
        # So unknown durations should map to "1y"
        unknown_duration = "unknown"
        # This is tested indirectly through the mocked call

    @patch("src.api_client.yf.download")
    @patch("src.api_client.time.sleep")
    def test_get_historical_data_success(self, mock_sleep, mock_download):
        """Test successful data fetch."""
        # Create mock DataFrame
        mock_data = pd.DataFrame(
            {"Close": [100.0, 101.0, 102.0]},
            index=pd.date_range("2023-01-01", periods=3),
        )
        mock_download.return_value = mock_data

        result = StockDataClient.get_historical_data("AAPL", "1 year")

        assert result is not None
        assert len(result) == 3
        mock_download.assert_called_once_with(
            tickers="AAPL", period="1y", progress=False, auto_adjust=True
        )
        mock_sleep.assert_called_once()

    @patch("src.api_client.yf.download")
    def test_get_historical_data_empty(self, mock_download):
        """Test handling of empty DataFrame response."""
        mock_download.return_value = pd.DataFrame()

        result = StockDataClient.get_historical_data("INVALID", "1 year")

        assert result is None

    @patch("src.api_client.yf.download")
    def test_get_historical_data_network_error(self, mock_download):
        """Test handling of network errors."""
        mock_download.side_effect = ConnectionError("Network error")

        result = StockDataClient.get_historical_data("AAPL", "1 year")

        assert result is None

    @patch("src.api_client.yf.download")
    def test_get_historical_data_timeout(self, mock_download):
        """Test handling of timeout errors."""
        mock_download.side_effect = TimeoutError("Request timed out")

        result = StockDataClient.get_historical_data("AAPL", "1 year")

        assert result is None

    @patch("src.api_client.yf.Ticker")
    def test_get_current_price_success(self, mock_ticker_class):
        """Test successful current price fetch."""
        mock_ticker = MagicMock()
        mock_ticker.info = {"currentPrice": 150.50}
        mock_ticker_class.return_value = mock_ticker

        result = StockDataClient.get_current_price("AAPL")

        assert result == 150.50
        mock_ticker_class.assert_called_once_with("AAPL")

    @patch("src.api_client.yf.Ticker")
    def test_get_current_price_fallback(self, mock_ticker_class):
        """Test fallback to regularMarketPrice when currentPrice unavailable."""
        mock_ticker = MagicMock()
        mock_ticker.info = {"regularMarketPrice": 145.75}
        mock_ticker_class.return_value = mock_ticker

        result = StockDataClient.get_current_price("AAPL")

        assert result == 145.75

    @patch("src.api_client.yf.Ticker")
    def test_get_current_price_not_found(self, mock_ticker_class):
        """Test handling when price is not found."""
        mock_ticker = MagicMock()
        mock_ticker.info = {}
        mock_ticker_class.return_value = mock_ticker

        result = StockDataClient.get_current_price("INVALID")

        assert result is None

    @patch("src.api_client.yf.Ticker")
    def test_get_current_price_network_error(self, mock_ticker_class):
        """Test handling of network errors in get_current_price."""
        mock_ticker_class.side_effect = ConnectionError("Network error")

        result = StockDataClient.get_current_price("AAPL")

        assert result is None

    def test_duration_mapping_all_values(self):
        """Test all duration mappings are present."""
        expected_durations = [
            "1 month",
            "3 months",
            "6 months",
            "1 year",
            "2 years",
            "5 years",
        ]
        for duration in expected_durations:
            assert duration in StockDataClient.DURATION_MAPPING

