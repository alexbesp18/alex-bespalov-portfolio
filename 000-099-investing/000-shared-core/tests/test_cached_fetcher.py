"""
Integration tests for CacheAwareFetcher.

Tests:
1. Cache hit - returns cached data when file exists for today
2. Cache miss - calls API when no cache file
3. Cache format conversion - column-oriented JSON to API format
4. Cache date filtering - only uses today's cache
5. API fallback on cache error
"""
import pytest
import json
import datetime
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shared_core.market_data.cached_fetcher import CacheAwareFetcher


@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for cache files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_cache_data():
    """
    Sample cache data in column-oriented format (pandas DataFrame JSON).
    
    This is the format created by:
        df.to_json("file.json")  # default orient='columns'
    """
    return {
        "datetime": {
            "0": "2025-12-01T00:00:00.000",
            "1": "2025-12-02T00:00:00.000",
            "2": "2025-12-03T00:00:00.000",
            "3": "2025-12-04T00:00:00.000",
            "4": "2025-12-05T00:00:00.000",
        },
        "open": {
            "0": 100.0,
            "1": 101.5,
            "2": 102.0,
            "3": 101.0,
            "4": 103.0,
        },
        "high": {
            "0": 101.5,
            "1": 103.0,
            "2": 104.0,
            "3": 102.5,
            "4": 105.0,
        },
        "low": {
            "0": 99.5,
            "1": 100.5,
            "2": 101.0,
            "3": 100.0,
            "4": 102.0,
        },
        "close": {
            "0": 101.0,
            "1": 102.5,
            "2": 103.5,
            "3": 101.5,
            "4": 104.5,
        },
        "volume": {
            "0": 1000000,
            "1": 1100000,
            "2": 1200000,
            "3": 900000,
            "4": 1300000,
        },
    }


@pytest.fixture
def fetcher(temp_cache_dir):
    """Create a CacheAwareFetcher with temporary cache directory."""
    return CacheAwareFetcher(
        api_key="test_api_key",
        cache_dir=temp_cache_dir,
        rate_limit_delay=0.1,
        output_size=100,
    )


class TestCacheHit:
    """Tests for cache hit scenarios."""
    
    def test_returns_cached_data_when_file_exists(self, fetcher, temp_cache_dir, sample_cache_data):
        """Should return cached data when today's cache file exists."""
        today = datetime.date.today().isoformat()
        cache_file = temp_cache_dir / f"AAPL_{today}.json"
        
        with open(cache_file, 'w') as f:
            json.dump(sample_cache_data, f)
        
        result = fetcher.fetch("AAPL")
        
        assert result is not None
        assert "values" in result
        assert len(result["values"]) == 5
        assert result["meta"]["source"] == "cache"
    
    def test_cache_data_has_correct_format(self, fetcher, temp_cache_dir, sample_cache_data):
        """Cached data should be converted to API-like format."""
        today = datetime.date.today().isoformat()
        cache_file = temp_cache_dir / f"TSLA_{today}.json"
        
        with open(cache_file, 'w') as f:
            json.dump(sample_cache_data, f)
        
        result = fetcher.fetch("TSLA")
        
        # Check structure matches API format
        assert "values" in result
        first_row = result["values"][0]
        assert "datetime" in first_row
        assert "open" in first_row
        assert "high" in first_row
        assert "low" in first_row
        assert "close" in first_row
        assert "volume" in first_row
        
        # Values should be strings (API format)
        assert first_row["open"] == "100.0"
        assert first_row["close"] == "101.0"
        assert first_row["volume"] == "1000000"
    
    def test_datetime_truncated_to_date(self, fetcher, temp_cache_dir, sample_cache_data):
        """Datetime should be truncated to date only (YYYY-MM-DD)."""
        today = datetime.date.today().isoformat()
        cache_file = temp_cache_dir / f"NVDA_{today}.json"
        
        with open(cache_file, 'w') as f:
            json.dump(sample_cache_data, f)
        
        result = fetcher.fetch("NVDA")
        
        # Check datetime is truncated
        first_row = result["values"][0]
        assert first_row["datetime"] == "2025-12-01"
        assert "T" not in first_row["datetime"]


class TestCacheMiss:
    """Tests for cache miss and API fallback."""
    
    def test_calls_api_when_no_cache_file(self, fetcher):
        """Should call API when cache file doesn't exist."""
        with patch('shared_core.market_data.cached_fetcher.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "values": [{"datetime": "2025-12-01", "close": "100.0"}],
                "status": "ok"
            }
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            result = fetcher.fetch("UNKNOWN_TICKER")
            
            mock_get.assert_called_once()
            assert result is not None
            assert result["meta"]["source"] == "api"
    
    def test_returns_none_on_api_error(self, fetcher):
        """Should return None when API returns error."""
        with patch('shared_core.market_data.cached_fetcher.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "status": "error",
                "message": "Invalid symbol"
            }
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            result = fetcher.fetch("INVALID")
            
            assert result is None


class TestCacheDateFiltering:
    """Tests for date-based cache filtering."""
    
    def test_ignores_old_cache_files(self, fetcher, temp_cache_dir, sample_cache_data):
        """Should not use cache files from previous days."""
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        old_cache = temp_cache_dir / f"AAPL_{yesterday}.json"
        
        with open(old_cache, 'w') as f:
            json.dump(sample_cache_data, f)
        
        with patch('shared_core.market_data.cached_fetcher.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "values": [{"datetime": "2025-12-01", "close": "100.0"}],
                "status": "ok"
            }
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            result = fetcher.fetch("AAPL")
            
            # Should call API because today's cache doesn't exist
            mock_get.assert_called_once()
    
    def test_is_cached_returns_true_for_today(self, fetcher, temp_cache_dir, sample_cache_data):
        """is_cached() should return True for today's cache."""
        today = datetime.date.today().isoformat()
        cache_file = temp_cache_dir / f"MSFT_{today}.json"
        
        with open(cache_file, 'w') as f:
            json.dump(sample_cache_data, f)
        
        assert fetcher.is_cached("MSFT") is True
        assert fetcher.is_cached("UNKNOWN") is False


class TestCacheFormatConversion:
    """Tests for column-oriented JSON to API format conversion."""
    
    def test_handles_missing_columns_gracefully(self, fetcher, temp_cache_dir):
        """Should handle cache files missing optional columns."""
        today = datetime.date.today().isoformat()
        cache_file = temp_cache_dir / f"PARTIAL_{today}.json"
        
        # Only datetime and close (minimal required columns)
        minimal_data = {
            "datetime": {"0": "2025-12-01T00:00:00.000"},
            "close": {"0": 100.0},
        }
        
        with open(cache_file, 'w') as f:
            json.dump(minimal_data, f)
        
        result = fetcher.fetch("PARTIAL")
        
        assert result is not None
        assert len(result["values"]) == 1
        # Missing columns should have empty strings
        assert result["values"][0]["open"] == ""
        assert result["values"][0]["close"] == "100.0"
    
    def test_handles_corrupted_cache_gracefully(self, fetcher, temp_cache_dir):
        """Should fall back to API on corrupted cache files."""
        today = datetime.date.today().isoformat()
        cache_file = temp_cache_dir / f"CORRUPT_{today}.json"
        
        with open(cache_file, 'w') as f:
            f.write("not valid json{{{")
        
        with patch('shared_core.market_data.cached_fetcher.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "values": [{"datetime": "2025-12-01", "close": "100.0"}],
                "status": "ok"
            }
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            result = fetcher.fetch("CORRUPT")
            
            # Should fall back to API
            mock_get.assert_called_once()
    
    def test_handles_wrong_format_gracefully(self, fetcher, temp_cache_dir):
        """Should fall back to API when cache has unexpected format."""
        today = datetime.date.today().isoformat()
        cache_file = temp_cache_dir / f"WRONG_{today}.json"
        
        # Array format instead of column-oriented dict
        wrong_format = [{"datetime": "2025-12-01", "close": 100.0}]
        
        with open(cache_file, 'w') as f:
            json.dump(wrong_format, f)
        
        with patch('shared_core.market_data.cached_fetcher.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "values": [{"datetime": "2025-12-01", "close": "100.0"}],
                "status": "ok"
            }
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            result = fetcher.fetch("WRONG")
            
            # Should fall back to API
            mock_get.assert_called_once()


class TestBatchFetching:
    """Tests for batch fetching with cache support."""
    
    def test_batch_uses_cache_for_available_tickers(self, fetcher, temp_cache_dir, sample_cache_data):
        """Batch fetch should use cache for available tickers and API for others."""
        today = datetime.date.today().isoformat()
        
        # Cache AAPL and MSFT
        for symbol in ["AAPL", "MSFT"]:
            cache_file = temp_cache_dir / f"{symbol}_{today}.json"
            with open(cache_file, 'w') as f:
                json.dump(sample_cache_data, f)
        
        with patch('shared_core.market_data.cached_fetcher.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "values": [{"datetime": "2025-12-01", "close": "100.0"}],
                "status": "ok"
            }
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            results = fetcher.fetch_batch(["AAPL", "MSFT", "GOOG"])
            
            # AAPL and MSFT from cache, GOOG from API
            assert len(results) == 3
            assert results["AAPL"]["meta"]["source"] == "cache"
            assert results["MSFT"]["meta"]["source"] == "cache"
            assert results["GOOG"]["meta"]["source"] == "api"
            
            # Only one API call (for GOOG)
            assert mock_get.call_count == 1
    
    def test_batch_handles_mixed_failures(self, fetcher, temp_cache_dir, sample_cache_data):
        """Batch fetch should handle mix of successes and failures."""
        today = datetime.date.today().isoformat()
        
        # Cache AAPL
        cache_file = temp_cache_dir / f"AAPL_{today}.json"
        with open(cache_file, 'w') as f:
            json.dump(sample_cache_data, f)
        
        with patch('shared_core.market_data.cached_fetcher.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "status": "error",
                "message": "Invalid symbol"
            }
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            results = fetcher.fetch_batch(["AAPL", "INVALID"])
            
            assert results["AAPL"] is not None  # From cache
            assert results["INVALID"] is None  # API error

