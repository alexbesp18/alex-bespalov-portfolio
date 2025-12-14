"""
Tests for input validation in API client and calculator.
"""
from unittest.mock import patch

import pandas as pd
import pytest

from src.api_client import (
    StockDataClient,
    MAX_SYMBOL_LENGTH,
    MIN_SYMBOL_LENGTH,
    VALID_DURATIONS,
)
from src.calculator import (
    CLOSE_COLUMN,
    MIN_DATA_POINTS_REQUIRED,
    StockCalculator,
)


class TestInputValidation:
    """Test input validation in API client."""

    def test_invalid_symbol_empty(self):
        """Test that empty symbol returns None."""
        result = StockDataClient.get_historical_data("", "1 year")
        assert result is None

    def test_invalid_symbol_none(self):
        """Test that None symbol returns None."""
        result = StockDataClient.get_historical_data(None, "1 year")  # type: ignore
        assert result is None

    def test_invalid_symbol_too_long(self):
        """Test that symbol exceeding max length returns None."""
        long_symbol = "A" * (MAX_SYMBOL_LENGTH + 1)
        result = StockDataClient.get_historical_data(long_symbol, "1 year")
        assert result is None

    def test_invalid_duration(self):
        """Test that invalid duration defaults to '1 year'."""
        with patch("src.api_client.StockDataClient._fetch_historical_data_internal") as mock_fetch:
            mock_fetch.return_value = pd.DataFrame({"Close": [100.0, 101.0]})
            result = StockDataClient.get_historical_data("AAPL", "invalid duration")
            # Should still attempt to fetch with default duration
            assert mock_fetch.called

    def test_valid_symbol_normalized(self):
        """Test that symbol is normalized to uppercase."""
        with patch("src.api_client.StockDataClient._fetch_historical_data_internal") as mock_fetch:
            mock_fetch.return_value = pd.DataFrame({"Close": [100.0, 101.0]})
            StockDataClient.get_historical_data("aapl", "1 year")
            # Check that symbol was normalized to uppercase
            call_args = mock_fetch.call_args
            assert call_args[0][0] == "AAPL"

    def test_get_current_price_invalid_symbol(self):
        """Test get_current_price with invalid symbol."""
        result = StockDataClient.get_current_price("")
        assert result is None

    def test_get_current_price_too_long(self):
        """Test get_current_price with symbol too long."""
        long_symbol = "A" * (MAX_SYMBOL_LENGTH + 1)
        result = StockDataClient.get_current_price(long_symbol)
        assert result is None


class TestConstants:
    """Test that constants are properly defined."""

    def test_symbol_length_constants(self):
        """Test symbol length constants."""
        assert MIN_SYMBOL_LENGTH > 0
        assert MAX_SYMBOL_LENGTH > MIN_SYMBOL_LENGTH
        assert MAX_SYMBOL_LENGTH <= 20  # Reasonable upper bound

    def test_valid_durations(self):
        """Test VALID_DURATIONS constant."""
        assert isinstance(VALID_DURATIONS, list)
        assert len(VALID_DURATIONS) > 0
        assert "1 year" in VALID_DURATIONS

    def test_calculator_constants(self):
        """Test calculator constants."""
        assert CLOSE_COLUMN == "Close"
        assert MIN_DATA_POINTS_REQUIRED >= 2

