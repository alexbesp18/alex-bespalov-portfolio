"""
Unit tests for StockDataClient class.

Note: These tests use mocking to avoid actual API calls to Twelve Data.
"""
from unittest.mock import MagicMock, patch, PropertyMock
import tempfile
from pathlib import Path

import pandas as pd
import numpy as np
import pytest

from src.api_client import StockDataClient


@pytest.fixture(autouse=True)
def reset_client_singleton():
    """Reset the singleton client before each test."""
    StockDataClient._client = None
    StockDataClient._cache = None
    yield
    StockDataClient._client = None
    StockDataClient._cache = None


@pytest.fixture
def mock_twelve_data_client():
    """Create a mock TwelveDataClient."""
    with patch('src.api_client.TwelveDataClient') as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_df():
    """Create a sample OHLCV DataFrame."""
    dates = pd.date_range("2023-01-01", periods=100, freq='D')
    np.random.seed(42)
    base_price = 150.0
    returns = np.random.normal(0.001, 0.02, 100)
    prices = base_price * np.cumprod(1 + returns)
    
    return pd.DataFrame({
        'datetime': dates,
        'open': prices * 0.99,
        'high': prices * 1.01,
        'low': prices * 0.98,
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 100)
    })


class TestStockDataClient:
    """Test suite for StockDataClient."""

    def test_duration_mapping(self):
        """Test that duration mapping is correct."""
        assert StockDataClient.DURATION_MAPPING["1 month"] == 30
        assert StockDataClient.DURATION_MAPPING["1 year"] == 365
        assert StockDataClient.DURATION_MAPPING["5 years"] == 1825

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


class TestGetHistoricalData:
    """Tests for get_historical_data method."""
    
    @patch('src.api_client.DataCache')
    @patch('src.api_client.TwelveDataClient')
    @patch.dict('os.environ', {'TWELVE_DATA_API_KEY': 'test_key'})
    def test_get_historical_data_success(self, mock_client_class, mock_cache_class, sample_df):
        """Test successful data fetch."""
        mock_client = MagicMock()
        mock_client.get_dataframe.return_value = sample_df
        mock_client_class.return_value = mock_client

        result = StockDataClient.get_historical_data("AAPL", "1 year")

        assert result is not None
        assert len(result) == 100  # sample_df has 100 rows
        assert 'Close' in result.columns
        mock_client.get_dataframe.assert_called_once_with("AAPL")

    @patch('src.api_client.DataCache')
    @patch('src.api_client.TwelveDataClient')
    @patch.dict('os.environ', {'TWELVE_DATA_API_KEY': 'test_key'})
    def test_get_historical_data_empty(self, mock_client_class, mock_cache_class):
        """Test handling of empty DataFrame response."""
        mock_client = MagicMock()
        mock_client.get_dataframe.return_value = pd.DataFrame()
        mock_client_class.return_value = mock_client

        result = StockDataClient.get_historical_data("INVALID", "1 year")

        assert result is None

    @patch('src.api_client.DataCache')
    @patch('src.api_client.TwelveDataClient')
    @patch.dict('os.environ', {'TWELVE_DATA_API_KEY': 'test_key'})
    def test_get_historical_data_none(self, mock_client_class, mock_cache_class):
        """Test handling of None response."""
        mock_client = MagicMock()
        mock_client.get_dataframe.return_value = None
        mock_client_class.return_value = mock_client

        result = StockDataClient.get_historical_data("INVALID", "1 year")

        assert result is None

    @patch('src.api_client.DataCache')
    @patch('src.api_client.TwelveDataClient')
    @patch.dict('os.environ', {'TWELVE_DATA_API_KEY': 'test_key'})
    def test_get_historical_data_network_error(self, mock_client_class, mock_cache_class):
        """Test handling of network errors."""
        mock_client = MagicMock()
        mock_client.get_dataframe.side_effect = ConnectionError("Network error")
        mock_client_class.return_value = mock_client

        result = StockDataClient.get_historical_data("AAPL", "1 year")

        assert result is None

    def test_get_historical_data_invalid_symbol_none(self):
        """Test handling of None symbol."""
        result = StockDataClient.get_historical_data(None, "1 year")
        assert result is None

    def test_get_historical_data_invalid_symbol_empty(self):
        """Test handling of empty symbol."""
        result = StockDataClient.get_historical_data("", "1 year")
        assert result is None

    def test_get_historical_data_invalid_symbol_too_long(self):
        """Test handling of symbol that's too long."""
        result = StockDataClient.get_historical_data("A" * 15, "1 year")
        assert result is None

    @patch('src.api_client.DataCache')
    @patch('src.api_client.TwelveDataClient')
    @patch.dict('os.environ', {'TWELVE_DATA_API_KEY': 'test_key'})
    def test_get_historical_data_filters_by_duration(self, mock_client_class, mock_cache_class, sample_df):
        """Test that data is filtered to requested duration."""
        mock_client = MagicMock()
        mock_client.get_dataframe.return_value = sample_df
        mock_client_class.return_value = mock_client

        result = StockDataClient.get_historical_data("AAPL", "1 month")

        # 1 month = 30 days, so should be truncated
        assert result is not None
        assert len(result) == 30


class TestGetCurrentPrice:
    """Tests for get_current_price method."""
    
    @patch('src.api_client.DataCache')
    @patch('src.api_client.TwelveDataClient')
    @patch.dict('os.environ', {'TWELVE_DATA_API_KEY': 'test_key'})
    def test_get_current_price_success(self, mock_client_class, mock_cache_class, sample_df):
        """Test successful current price fetch."""
        mock_client = MagicMock()
        mock_client.get_dataframe.return_value = sample_df
        mock_client_class.return_value = mock_client

        result = StockDataClient.get_current_price("AAPL")

        assert result is not None
        assert isinstance(result, float)
        assert result == float(sample_df['close'].iloc[-1])

    @patch('src.api_client.DataCache')
    @patch('src.api_client.TwelveDataClient')
    @patch.dict('os.environ', {'TWELVE_DATA_API_KEY': 'test_key'})
    def test_get_current_price_not_found(self, mock_client_class, mock_cache_class):
        """Test handling when price is not found."""
        mock_client = MagicMock()
        mock_client.get_dataframe.return_value = None
        mock_client_class.return_value = mock_client

        result = StockDataClient.get_current_price("INVALID")

        assert result is None

    @patch('src.api_client.DataCache')
    @patch('src.api_client.TwelveDataClient')
    @patch.dict('os.environ', {'TWELVE_DATA_API_KEY': 'test_key'})
    def test_get_current_price_network_error(self, mock_client_class, mock_cache_class):
        """Test handling of network errors in get_current_price."""
        mock_client = MagicMock()
        mock_client.get_dataframe.side_effect = ConnectionError("Network error")
        mock_client_class.return_value = mock_client

        result = StockDataClient.get_current_price("AAPL")

        assert result is None

    def test_get_current_price_invalid_symbol(self):
        """Test handling of invalid symbol."""
        result = StockDataClient.get_current_price(None)
        assert result is None


class TestClientSingleton:
    """Tests for client singleton behavior."""
    
    @patch('src.api_client.DataCache')
    @patch('src.api_client.TwelveDataClient')
    @patch.dict('os.environ', {'TWELVE_DATA_API_KEY': 'test_key'})
    def test_client_singleton_reused(self, mock_client_class, mock_cache_class, sample_df):
        """Test that the same client instance is reused."""
        mock_client = MagicMock()
        mock_client.get_dataframe.return_value = sample_df
        mock_client_class.return_value = mock_client
        
        # First call
        StockDataClient.get_historical_data("AAPL", "1 year")
        # Second call
        StockDataClient.get_historical_data("NVDA", "1 year")
        
        # TwelveDataClient should only be instantiated once
        assert mock_client_class.call_count == 1
    
    @patch.dict('os.environ', {'TWELVE_DATA_API_KEY': ''})
    def test_client_requires_api_key(self):
        """Test that client raises error without API key."""
        StockDataClient._client = None
        StockDataClient._cache = None
        
        with pytest.raises(ValueError, match="TWELVE_DATA_API_KEY"):
            StockDataClient._get_client()
