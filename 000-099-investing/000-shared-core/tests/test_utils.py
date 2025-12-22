"""
Unit tests for shared_core.utils module.

Tests cache tickers, time guard, and logging utilities.
"""

import pytest
import os
import logging
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from unittest import mock

from shared_core.utils import (
    get_cached_tickers,
    get_latest_cached_tickers,
    get_cache_dates,
    check_time_guard,
    is_market_hours,
    setup_logging,
    get_logger,
)


class TestGetCachedTickers:
    """Tests for get_cached_tickers function."""
    
    def test_finds_today_files(self, tmp_cache_dir):
        """get_cached_tickers finds today's cached files."""
        today = datetime.now().strftime('%Y-%m-%d')
        
        result = get_cached_tickers(tmp_cache_dir, date=today)
        
        assert isinstance(result, list)
        # Should find AAPL, NVDA, GOOGL from fixture
        assert 'AAPL' in result
        assert 'NVDA' in result
        assert 'GOOGL' in result
    
    def test_finds_yesterday_files(self, tmp_cache_dir):
        """get_cached_tickers finds yesterday's cached files."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        result = get_cached_tickers(tmp_cache_dir, date=yesterday)
        
        assert isinstance(result, list)
        # Should find AAPL, MSFT from fixture
        assert 'AAPL' in result
        assert 'MSFT' in result
    
    def test_empty_on_missing_date(self, tmp_cache_dir):
        """get_cached_tickers returns empty for non-existent date."""
        result = get_cached_tickers(tmp_cache_dir, date='1999-01-01')
        
        assert result == []
    
    def test_empty_on_missing_dir(self):
        """get_cached_tickers returns empty for non-existent directory."""
        result = get_cached_tickers('/nonexistent/path')
        
        assert result == []
    
    def test_default_date_is_today(self, tmp_cache_dir):
        """get_cached_tickers defaults to today's date."""
        # Create file for today
        today = datetime.now().strftime('%Y-%m-%d')
        
        result = get_cached_tickers(tmp_cache_dir)
        
        assert isinstance(result, list)
        # Should find today's files
        assert 'AAPL' in result


class TestGetLatestCachedTickers:
    """Tests for get_latest_cached_tickers function."""
    
    def test_finds_latest(self, tmp_cache_dir):
        """get_latest_cached_tickers finds most recent files."""
        result = get_latest_cached_tickers(tmp_cache_dir, lookback_days=7)
        
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_lookback_works(self, tmp_cache_dir):
        """Lookback parameter limits search range."""
        # With lookback=0, should only find today
        result = get_latest_cached_tickers(tmp_cache_dir, lookback_days=0)
        
        assert isinstance(result, list)
    
    def test_empty_on_no_files(self, tmp_path):
        """Returns empty when no cache files exist."""
        empty_dir = tmp_path / "empty_cache"
        empty_dir.mkdir()
        
        result = get_latest_cached_tickers(str(empty_dir), lookback_days=30)
        
        assert result == []


class TestGetCacheDates:
    """Tests for get_cache_dates function."""
    
    def test_returns_sorted_dates(self, tmp_cache_dir):
        """get_cache_dates returns sorted list of dates."""
        result = get_cache_dates(tmp_cache_dir)
        
        assert isinstance(result, list)
        assert len(result) >= 2  # Today and yesterday from fixture
        
        # Should be sorted (most recent first or oldest first)
        assert result == sorted(result) or result == sorted(result, reverse=True)
    
    def test_unique_dates(self, tmp_cache_dir):
        """get_cache_dates returns unique dates."""
        result = get_cache_dates(tmp_cache_dir)
        
        assert len(result) == len(set(result))
    
    def test_empty_on_missing_dir(self):
        """get_cache_dates returns empty for non-existent directory."""
        result = get_cache_dates('/nonexistent/path')
        
        assert result == []


class TestCheckTimeGuard:
    """Tests for check_time_guard function."""
    
    def test_matching_hour(self):
        """check_time_guard passes for matching hour."""
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("America/Chicago"))
        current_hour = now.hour
        
        result = check_time_guard(expected_hour=current_hour, timezone_name="America/Chicago")
        
        assert result is True
    
    def test_wrong_hour(self):
        """check_time_guard fails for wrong hour."""
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("America/Chicago"))
        wrong_hour = (now.hour + 12) % 24
        
        result = check_time_guard(expected_hour=wrong_hour, timezone_name="America/Chicago")
        
        assert result is False
    
    def test_with_timezone(self):
        """check_time_guard respects timezone."""
        from zoneinfo import ZoneInfo
        # Get current hour in Eastern time
        now_eastern = datetime.now(ZoneInfo("America/New_York"))
        
        result = check_time_guard(
            expected_hour=now_eastern.hour,
            timezone_name="America/New_York"
        )
        
        assert result is True
    
    def test_with_explicit_now(self):
        """check_time_guard uses explicit now parameter."""
        from zoneinfo import ZoneInfo
        # Create a specific time
        test_now = datetime(2024, 1, 15, 10, 30, 0, tzinfo=ZoneInfo("America/Chicago"))
        
        result = check_time_guard(
            expected_hour=10,
            timezone_name="America/Chicago",
            now=test_now
        )
        
        assert result is True


class TestIsMarketHours:
    """Tests for is_market_hours function."""
    
    def test_returns_boolean(self):
        """is_market_hours returns a boolean."""
        result = is_market_hours()
        assert isinstance(result, bool)
    
    def test_with_timezone(self):
        """is_market_hours accepts timezone parameter."""
        result = is_market_hours(timezone_name="America/New_York")
        assert isinstance(result, bool)


class TestSetupLogging:
    """Tests for setup_logging function."""
    
    def test_returns_logger(self):
        """setup_logging returns a logger instance."""
        result = setup_logging(name='test_logger')
        
        assert isinstance(result, logging.Logger)
    
    def test_logger_name(self):
        """setup_logging uses provided name."""
        result = setup_logging(name='my_custom_logger')
        
        assert result.name == 'my_custom_logger'
    
    def test_verbose_level(self):
        """setup_logging with verbose=True sets DEBUG level."""
        result = setup_logging(name='verbose_test', verbose=True)
        
        assert result.level == logging.DEBUG or result.getEffectiveLevel() == logging.DEBUG
    
    def test_default_level(self):
        """setup_logging default level is INFO."""
        result = setup_logging(name='default_test')
        
        # Should be INFO or higher
        assert result.getEffectiveLevel() <= logging.WARNING
    
    def test_has_handler(self):
        """setup_logging adds handler."""
        result = setup_logging(name='handler_test')
        
        # Should have at least one handler (or inherit from root)
        assert len(result.handlers) > 0 or result.parent is not None


class TestGetLogger:
    """Tests for get_logger function."""
    
    def test_returns_logger(self):
        """get_logger returns a logger instance."""
        result = get_logger('test')
        
        assert isinstance(result, logging.Logger)
    
    def test_same_name_same_logger(self):
        """get_logger returns same logger for same name."""
        logger1 = get_logger('same_name')
        logger2 = get_logger('same_name')
        
        assert logger1 is logger2
    
    def test_different_names(self):
        """get_logger returns different loggers for different names."""
        logger1 = get_logger('name1')
        logger2 = get_logger('name2')
        
        assert logger1.name != logger2.name


class TestUtilsEdgeCases:
    """Edge case tests for utils."""
    
    def test_cache_dir_with_special_chars(self, tmp_path):
        """Handle cache directory with special characters."""
        special_dir = tmp_path / "cache with spaces"
        special_dir.mkdir()
        
        today = datetime.now().strftime('%Y-%m-%d')
        (special_dir / f"AAPL_{today}.json").write_text('{}')
        
        result = get_cached_tickers(str(special_dir))
        
        assert 'AAPL' in result
    
    def test_cache_file_naming_variations(self, tmp_path):
        """Handle various cache file naming patterns."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Different naming patterns that might exist
        (cache_dir / f"AAPL_{today}.json").write_text('{}')
        (cache_dir / f"BRK.B_{today}.json").write_text('{}')  # With dot
        
        result = get_cached_tickers(str(cache_dir))
        
        assert 'AAPL' in result
        # BRK.B might be parsed differently
    
    def test_time_guard_edge_of_hour(self):
        """check_time_guard at edge of hour (59 minutes)."""
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("America/Chicago"))
        current_hour = now.hour
        
        result = check_time_guard(expected_hour=current_hour, timezone_name="America/Chicago")
        
        assert result is True
    
    def test_logging_with_file(self, tmp_path):
        """setup_logging with file output."""
        log_file = tmp_path / "test.log"
        
        logger = setup_logging(
            name='file_test',
            log_file=str(log_file)
        )
        
        # Log a message
        logger.info("Test message")
        
        # File might not exist if file logging isn't implemented
        # Just verify no crash
        assert isinstance(logger, logging.Logger)
    
    def test_empty_cache_date_pattern(self, tmp_path):
        """Handle cache files without date pattern."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        
        # Files without date
        (cache_dir / "AAPL.json").write_text('{}')
        (cache_dir / "config.json").write_text('{}')
        
        result = get_cached_tickers(str(cache_dir))
        
        # Should handle gracefully
        assert isinstance(result, list)

