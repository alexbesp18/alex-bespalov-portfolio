"""
Unit tests for TwelveDataClient.
Uses mocking to avoid actual API calls.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shared_core.market_data.twelve_data import TwelveDataClient
from shared_core.cache.data_cache import DataCache


@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for cache files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def cache(temp_cache_dir):
    """Create a DataCache instance with a temporary directory."""
    return DataCache(temp_cache_dir, verbose=False)


@pytest.fixture
def client(cache):
    """Create a TwelveDataClient instance with cache."""
    return TwelveDataClient(api_key="test_api_key", cache=cache, verbose=False)


@pytest.fixture
def mock_api_response():
    """Create a mock API response with realistic data."""
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    np.random.seed(42)
    base_price = 150.0
    returns = np.random.normal(0.001, 0.02, 100)
    prices = base_price * np.cumprod(1 + returns)
    
    values = []
    for i, date in enumerate(dates):
        values.append({
            'datetime': date.strftime('%Y-%m-%d'),
            'open': str(round(prices[i] * 0.99, 2)),
            'high': str(round(prices[i] * 1.01, 2)),
            'low': str(round(prices[i] * 0.98, 2)),
            'close': str(round(prices[i], 2)),
            'volume': str(np.random.randint(1000000, 10000000))
        })
    
    return {'values': list(reversed(values)), 'status': 'ok'}


@pytest.fixture
def sample_df():
    """Create a sample OHLCV DataFrame."""
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
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


class TestClientInitialization:
    """Tests for client initialization."""
    
    def test_client_creates_with_defaults(self):
        client = TwelveDataClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert client.output_size == 365
        assert client.cache is None
    
    def test_client_creates_with_cache(self, cache):
        client = TwelveDataClient(api_key="test_key", cache=cache)
        assert client.cache is cache


class TestTickersNeedingRefresh:
    """Tests for get_tickers_needing_refresh."""
    
    def test_all_need_refresh_with_empty_cache(self, client):
        tickers = ['AAPL', 'NVDA', 'TSLA']
        result = client.get_tickers_needing_refresh(tickers)
        assert result == tickers
    
    def test_cached_ticker_not_in_refresh_list(self, client, cache, sample_df):
        cache.save_twelve_data("AAPL", sample_df)
        
        tickers = ['AAPL', 'NVDA', 'TSLA']
        result = client.get_tickers_needing_refresh(tickers)
        
        assert 'AAPL' not in result
        assert 'NVDA' in result
        assert 'TSLA' in result
    
    def test_no_cache_returns_all_tickers(self):
        client = TwelveDataClient(api_key="test_key", cache=None)
        tickers = ['AAPL', 'NVDA']
        result = client.get_tickers_needing_refresh(tickers)
        assert result == tickers


class TestFetchRaw:
    """Tests for fetch_raw method."""
    
    @patch('shared_core.market_data.twelve_data.requests.get')
    def test_fetch_raw_success(self, mock_get, client, mock_api_response):
        mock_get.return_value.json.return_value = mock_api_response
        
        result = client.fetch_raw("AAPL")
        
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert 'close' in result.columns
        assert len(result) >= 50
    
    @patch('shared_core.market_data.twelve_data.requests.get')
    def test_fetch_raw_handles_api_error(self, mock_get, client):
        mock_get.return_value.json.return_value = {
            'code': 401,
            'message': 'Invalid API key'
        }
        
        result = client.fetch_raw("AAPL")
        assert result is None
    
    @patch('shared_core.market_data.twelve_data.requests.get')
    def test_fetch_raw_handles_empty_response(self, mock_get, client):
        mock_get.return_value.json.return_value = {'values': []}
        
        result = client.fetch_raw("AAPL")
        assert result is None
    
    @patch('shared_core.market_data.twelve_data.requests.get')
    def test_fetch_raw_handles_timeout(self, mock_get, client):
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()
        
        result = client.fetch_raw("AAPL")
        assert result is None


class TestFetchAndCalculate:
    """Tests for fetch_and_calculate method."""
    
    @patch('shared_core.market_data.twelve_data.requests.get')
    def test_fetch_and_calculate_returns_indicators(self, mock_get, client, mock_api_response):
        mock_get.return_value.json.return_value = mock_api_response
        
        result = client.fetch_and_calculate("AAPL")
        
        assert result is not None
        assert result['Ticker'] == 'AAPL'
        assert 'Price' in result
        assert 'RSI' in result
        assert 'MACD' in result
        assert 'MACD_Hist' in result
        assert 'Trend' in result
        assert 'SMA_20' in result
        assert 'SMA_50' in result
        assert 'SMA_200' in result
        assert 'Status' in result
    
    def test_fetch_and_calculate_uses_cache(self, client, cache, sample_df):
        cache.save_twelve_data("AAPL", sample_df)
        
        # This should NOT make an API call
        with patch('shared_core.market_data.twelve_data.requests.get') as mock_get:
            result = client.fetch_and_calculate("AAPL")
            mock_get.assert_not_called()
        
        assert result is not None
        assert result['Ticker'] == 'AAPL'
    
    @patch('shared_core.market_data.twelve_data.requests.get')
    def test_fetch_and_calculate_force_refresh_bypasses_cache(self, mock_get, client, cache, sample_df, mock_api_response):
        cache.save_twelve_data("AAPL", sample_df)
        mock_get.return_value.json.return_value = mock_api_response
        
        result = client.fetch_and_calculate("AAPL", force_refresh=True)
        
        mock_get.assert_called_once()
        assert result is not None
    
    @patch('shared_core.market_data.twelve_data.requests.get')
    def test_fetch_and_calculate_saves_to_cache(self, mock_get, client, cache, mock_api_response):
        mock_get.return_value.json.return_value = mock_api_response
        
        client.fetch_and_calculate("NVDA")
        
        # Should now be in cache
        cached = cache.get_twelve_data("NVDA")
        assert cached is not None
    
    @patch('shared_core.market_data.twelve_data.requests.get')
    def test_fetch_and_calculate_returns_error_on_failure(self, mock_get, client):
        mock_get.return_value.json.return_value = {'code': 500, 'message': 'Server error'}
        
        result = client.fetch_and_calculate("AAPL")
        
        assert result['Ticker'] == 'AAPL'
        assert 'ERROR' in result['Status']


class TestGetDataframe:
    """Tests for get_dataframe method."""
    
    @patch('shared_core.market_data.twelve_data.requests.get')
    def test_get_dataframe_returns_df(self, mock_get, client, mock_api_response):
        mock_get.return_value.json.return_value = mock_api_response
        
        result = client.get_dataframe("AAPL")
        
        assert isinstance(result, pd.DataFrame)
        assert 'close' in result.columns
        assert 'volume' in result.columns
    
    def test_get_dataframe_uses_cache(self, client, cache, sample_df):
        cache.save_twelve_data("AAPL", sample_df)
        
        with patch('shared_core.market_data.twelve_data.requests.get') as mock_get:
            result = client.get_dataframe("AAPL")
            mock_get.assert_not_called()
        
        assert result is not None


class TestIndicatorCalculation:
    """Tests for indicator calculation accuracy."""
    
    @patch('shared_core.market_data.twelve_data.requests.get')
    def test_rsi_in_valid_range(self, mock_get, client, mock_api_response):
        mock_get.return_value.json.return_value = mock_api_response
        
        result = client.fetch_and_calculate("AAPL")
        
        assert 0 <= result['RSI'] <= 100
    
    @patch('shared_core.market_data.twelve_data.requests.get')
    def test_trend_is_valid_value(self, mock_get, client, mock_api_response):
        mock_get.return_value.json.return_value = mock_api_response
        
        result = client.fetch_and_calculate("AAPL")
        
        valid_trends = ['STRONG_UPTREND', 'UPTREND', 'SIDEWAYS', 'DOWNTREND', 'STRONG_DOWNTREND']
        assert result['Trend'] in valid_trends
    
    @patch('shared_core.market_data.twelve_data.requests.get')
    def test_obv_trend_is_valid(self, mock_get, client, mock_api_response):
        mock_get.return_value.json.return_value = mock_api_response
        
        result = client.fetch_and_calculate("AAPL")
        
        assert result['OBV_Trend'] in ['UP', 'DOWN', 'SIDEWAYS']

