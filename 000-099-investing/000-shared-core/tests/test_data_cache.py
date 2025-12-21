"""
Unit tests for DataCache.
"""
import pytest
import pandas as pd
import json
import datetime
from pathlib import Path
import tempfile
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

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
def sample_df():
    """Create a sample OHLCV DataFrame."""
    dates = pd.date_range(end=datetime.datetime.now(), periods=100, freq='D')
    return pd.DataFrame({
        'datetime': dates,
        'open': [100 + i * 0.1 for i in range(100)],
        'high': [101 + i * 0.1 for i in range(100)],
        'low': [99 + i * 0.1 for i in range(100)],
        'close': [100 + i * 0.1 for i in range(100)],
        'volume': [1000000 + i * 1000 for i in range(100)]
    })


class TestCacheInitialization:
    """Tests for cache initialization."""
    
    def test_cache_creates_directories(self, temp_cache_dir):
        cache = DataCache(temp_cache_dir)
        assert (temp_cache_dir / "twelve_data").exists()
        assert (temp_cache_dir / "transcripts").exists()
    
    def test_cache_sets_today_date(self, cache):
        assert cache.today == datetime.date.today().isoformat()


class TestTwelveDataCache:
    """Tests for Twelve Data caching."""
    
    def test_save_and_get_twelve_data(self, cache, sample_df):
        cache.save_twelve_data("AAPL", sample_df)
        result = cache.get_twelve_data("AAPL")
        
        assert result is not None
        assert len(result) == len(sample_df)
    
    def test_get_nonexistent_returns_none(self, cache):
        result = cache.get_twelve_data("NONEXISTENT")
        assert result is None
    
    def test_case_insensitive_tickers(self, cache, sample_df):
        cache.save_twelve_data("aapl", sample_df)
        result = cache.get_twelve_data("AAPL")
        assert result is not None
    
    def test_file_path_format(self, cache, temp_cache_dir):
        path = cache._get_twelve_data_path("AAPL")
        expected = temp_cache_dir / "twelve_data" / f"AAPL_{cache.today}.json"
        assert path == expected


class TestTranscriptCache:
    """Tests for transcript caching."""
    
    def test_save_and_get_transcript(self, cache):
        transcript_data = {
            'Ticker': 'NVDA',
            'Period': 'Q3 2024',
            'text': 'This is a test transcript...',
            'date': '2024-11-20'
        }
        cache.save_transcript("NVDA", transcript_data)
        result = cache.get_transcript("NVDA")
        
        assert result is not None
        assert result['Period'] == 'Q3 2024'
        assert result['text'] == 'This is a test transcript...'
    
    def test_get_nonexistent_transcript_returns_none(self, cache):
        result = cache.get_transcript("NONEXISTENT")
        assert result is None


class TestCacheManagement:
    """Tests for cache management operations."""
    
    def test_list_cached_tickers(self, cache, sample_df):
        cache.save_twelve_data("AAPL", sample_df)
        cache.save_twelve_data("NVDA", sample_df)
        cache.save_twelve_data("TSLA", sample_df)
        
        tickers = cache.list_cached_tickers('twelve_data')
        assert set(tickers) == {'AAPL', 'NVDA', 'TSLA'}
    
    def test_list_cached_tickers_sorted(self, cache, sample_df):
        cache.save_twelve_data("TSLA", sample_df)
        cache.save_twelve_data("AAPL", sample_df)
        cache.save_twelve_data("NVDA", sample_df)
        
        tickers = cache.list_cached_tickers('twelve_data')
        assert tickers == sorted(tickers)
    
    def test_get_cache_stats(self, cache, sample_df):
        cache.save_twelve_data("AAPL", sample_df)
        cache.save_transcript("AAPL", {'text': 'test'})
        
        stats = cache.get_cache_stats()
        
        assert stats['twelve_data_today'] == 1
        assert stats['transcripts_today'] == 1
        assert stats['cache_date'] == cache.today
        assert 'total_size_mb' in stats
    
    def test_clear_all_cache(self, cache, sample_df):
        cache.save_twelve_data("AAPL", sample_df)
        cache.save_twelve_data("NVDA", sample_df)
        cache.save_transcript("AAPL", {'text': 'test'})
        
        deleted = cache.clear_all_cache()
        
        assert deleted == 3
        assert cache.get_twelve_data("AAPL") is None
        assert cache.get_twelve_data("NVDA") is None
        assert cache.get_transcript("AAPL") is None
    
    def test_clear_old_cache(self, cache, temp_cache_dir, sample_df):
        # Save current data
        cache.save_twelve_data("CURRENT", sample_df)
        
        # Manually create an "old" cache file
        old_date = (datetime.date.today() - datetime.timedelta(days=10)).isoformat()
        old_path = temp_cache_dir / "twelve_data" / f"OLD_{old_date}.json"
        sample_df.to_json(old_path)
        
        # Clear files older than 7 days
        deleted = cache.clear_old_cache(days=7)
        
        assert deleted == 1
        assert not old_path.exists()
        assert cache.get_twelve_data("CURRENT") is not None


class TestCacheVerbose:
    """Tests for verbose mode."""
    
    def test_verbose_mode_prints(self, temp_cache_dir, sample_df, capsys):
        cache = DataCache(temp_cache_dir, verbose=True)
        cache.save_twelve_data("AAPL", sample_df)
        cache.get_twelve_data("AAPL")
        
        captured = capsys.readouterr()
        assert "Cached" in captured.out or "hit" in captured.out

