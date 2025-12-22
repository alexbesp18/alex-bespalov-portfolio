"""
Unit tests for shared_core.models module.

Tests TickerResult, ScanResult, Watchlist, and config models.
"""

import pytest
import json
from datetime import datetime
from pathlib import Path

from shared_core.models import (
    TickerResult,
    ScanResult,
    WatchlistEntry,
    Watchlist,
    ScanConfig,
    OutputFormat,
)


class TestTickerResult:
    """Tests for TickerResult dataclass."""
    
    def test_create_ticker_result(self):
        """Create TickerResult with all fields."""
        result = TickerResult(
            symbol='AAPL',
            close=150.0,
            score=8.5,
            action='BUY',
            rsi=35.0,
        )
        
        assert result.symbol == 'AAPL'
        assert result.close == 150.0
        assert result.score == 8.5
        assert result.action == 'BUY'
    
    def test_to_dict_roundtrip(self):
        """to_dict and from_dict roundtrip correctly."""
        original = TickerResult(
            symbol='NVDA',
            close=500.0,
            score=7.0,
            action='SELL',
            rsi=75.0,
        )
        
        d = original.to_dict()
        recreated = TickerResult.from_dict(d)
        
        assert recreated.symbol == original.symbol
        assert recreated.close == original.close
        assert recreated.score == original.score
        assert recreated.action == original.action
    
    def test_from_dict_handles_missing(self):
        """from_dict handles missing optional fields."""
        minimal = {'symbol': 'AAPL', 'close': 100.0}
        
        result = TickerResult.from_dict(minimal)
        
        assert result.symbol == 'AAPL'
        assert result.close == 100.0
        # Optional fields should have defaults
        assert result.action == 'HOLD'
    
    def test_to_dict_all_fields(self):
        """to_dict includes all fields."""
        result = TickerResult(
            symbol='AAPL',
            close=150.0,
            score=8.0,
            action='BUY',
            rsi=40.0,
            message='Test message',
        )
        
        d = result.to_dict()
        
        assert 'symbol' in d
        assert 'close' in d
        assert 'score' in d
        assert 'action' in d
        assert 'rsi' in d


class TestScanResult:
    """Tests for ScanResult dataclass."""
    
    def test_create_scan_result(self):
        """Create ScanResult with results."""
        results = [
            TickerResult(symbol='AAPL', close=150.0, score=8.0, action='BUY'),
            TickerResult(symbol='NVDA', close=500.0, score=3.0, action='SELL'),
        ]
        
        scan = ScanResult(tickers=results)
        
        assert len(scan.tickers) == 2
        assert len(scan.buy_signals) == 1
        assert len(scan.sell_signals) == 1
    
    def test_has_signals(self):
        """ScanResult.has_signals property works."""
        with_signals = ScanResult(tickers=[
            TickerResult(symbol='AAPL', close=150.0, action='BUY'),
        ])
        without_signals = ScanResult()
        
        assert with_signals.has_signals is True
        assert without_signals.has_signals is False
    
    def test_empty_scan_result(self):
        """ScanResult with no results."""
        scan = ScanResult()
        
        assert len(scan.tickers) == 0
        assert scan.has_signals is False


class TestWatchlistEntry:
    """Tests for WatchlistEntry dataclass."""
    
    def test_create_entry(self):
        """Create WatchlistEntry."""
        entry = WatchlistEntry(
            symbol='AAPL',
            list_type='portfolio',
            triggers=[{'type': 'score_above', 'value': 7}],
        )
        
        assert entry.symbol == 'AAPL'
        assert entry.list_type == 'portfolio'
        assert len(entry.triggers) == 1
    
    def test_entry_defaults(self):
        """WatchlistEntry has sensible defaults."""
        entry = WatchlistEntry(symbol='NVDA')
        
        assert entry.symbol == 'NVDA'
        assert entry.list_type == 'watchlist'
    
    def test_to_dict(self):
        """to_dict serializes entry."""
        entry = WatchlistEntry(
            symbol='AAPL',
            list_type='portfolio',
            triggers=[{'type': 'score_above', 'value': 7}],
        )
        
        d = entry.to_dict()
        
        assert d['symbol'] == 'AAPL'
        assert d['list_type'] == 'portfolio'


class TestWatchlist:
    """Tests for Watchlist dataclass."""
    
    def test_from_json_file_new_format(self, sample_watchlist_json):
        """Load watchlist from new JSON format."""
        watchlist = Watchlist.from_json_file(sample_watchlist_json)
        
        assert isinstance(watchlist, Watchlist)
        assert len(watchlist.entries) > 0
    
    def test_from_json_file_legacy_format(self, sample_legacy_watchlist_json):
        """Load watchlist from legacy JSON format."""
        watchlist = Watchlist.from_json_file(sample_legacy_watchlist_json)
        
        assert isinstance(watchlist, Watchlist)
        assert len(watchlist.entries) > 0
    
    def test_portfolio_property(self, sample_watchlist_json):
        """Watchlist.portfolio returns portfolio entries."""
        watchlist = Watchlist.from_json_file(sample_watchlist_json)
        
        portfolio = watchlist.portfolio
        
        assert isinstance(portfolio, list)
        for entry in portfolio:
            assert entry.list_type == 'portfolio'
    
    def test_watchlist_property(self, sample_watchlist_json):
        """Watchlist.watchlist returns watchlist entries."""
        watchlist = Watchlist.from_json_file(sample_watchlist_json)
        
        watch = watchlist.watchlist
        
        assert isinstance(watch, list)
        for entry in watch:
            assert entry.list_type == 'watchlist'
    
    def test_get_entry_case_insensitive(self, sample_watchlist_json):
        """get_entry is case-insensitive."""
        watchlist = Watchlist.from_json_file(sample_watchlist_json)
        
        # Try different cases
        entry1 = watchlist.get_entry('AAPL')
        entry2 = watchlist.get_entry('aapl')
        entry3 = watchlist.get_entry('Aapl')
        
        assert entry1 == entry2 == entry3
    
    def test_get_entry_missing(self, sample_watchlist_json):
        """get_entry returns None for missing symbol."""
        watchlist = Watchlist.from_json_file(sample_watchlist_json)
        
        result = watchlist.get_entry('NONEXISTENT')
        
        assert result is None
    
    def test_symbols_property(self, sample_watchlist_json):
        """symbols returns all symbols."""
        watchlist = Watchlist.from_json_file(sample_watchlist_json)
        
        symbols = watchlist.symbols
        
        assert isinstance(symbols, list)
        assert all(isinstance(s, str) for s in symbols)
    
    def test_empty_watchlist(self, tmp_path):
        """Handle empty watchlist file."""
        path = tmp_path / "empty.json"
        path.write_text('{"entries": []}')
        
        watchlist = Watchlist.from_json_file(str(path))
        
        assert len(watchlist.entries) == 0
        assert watchlist.portfolio == []
        assert watchlist.watchlist == []
    
    def test_missing_file_returns_empty(self):
        """Missing file returns empty watchlist."""
        watchlist = Watchlist.from_json_file('/nonexistent/path/watchlist.json')
        assert len(watchlist.entries) == 0


class TestScanConfig:
    """Tests for ScanConfig dataclass."""
    
    def test_create_config(self):
        """Create ScanConfig."""
        config = ScanConfig(
            tickers=['AAPL', 'NVDA'],
            output_format=OutputFormat.JSON,
            min_score=7.0,
        )
        
        assert config.tickers == ['AAPL', 'NVDA']
        assert config.output_format == OutputFormat.JSON
        assert config.min_score == 7.0
    
    def test_from_dict(self):
        """Create ScanConfig from dictionary."""
        d = {
            'tickers': ['AAPL', 'NVDA'],
            'output_format': 'json',
            'min_score': 7.0,
        }
        
        config = ScanConfig.from_dict(d)
        
        assert config.tickers == ['AAPL', 'NVDA']
        assert config.min_score == 7.0
    
    def test_defaults(self):
        """ScanConfig has sensible defaults."""
        config = ScanConfig()
        
        assert config.tickers == []
        assert config.output_format == OutputFormat.TABLE
        assert config.dry_run is False


class TestOutputFormat:
    """Tests for OutputFormat enum."""
    
    def test_enum_values(self):
        """OutputFormat has expected values."""
        assert OutputFormat.JSON is not None
        assert OutputFormat.TABLE is not None
        assert OutputFormat.HTML is not None
        assert OutputFormat.CSV is not None
    
    def test_enum_value_strings(self):
        """OutputFormat values are lowercase strings."""
        assert OutputFormat.JSON.value == 'json'
        assert OutputFormat.TABLE.value == 'table'
        assert OutputFormat.HTML.value == 'html'


class TestModelEdgeCases:
    """Edge case tests for models."""
    
    def test_ticker_result_defaults(self):
        """TickerResult with minimal fields."""
        result = TickerResult(symbol='AAPL', close=100.0)
        
        assert result.action == 'HOLD'
        assert result.score == 0.0
        assert result.flags == {}
    
    def test_watchlist_duplicate_symbols(self, tmp_path):
        """Handle duplicate symbols in watchlist."""
        path = tmp_path / "dupes.json"
        path.write_text(json.dumps({
            "entries": [
                {"symbol": "AAPL", "list_type": "portfolio"},
                {"symbol": "AAPL", "list_type": "watchlist"},
            ]
        }))
        
        watchlist = Watchlist.from_json_file(str(path))
        
        # Should load both entries
        assert len(watchlist.entries) == 2
    
    def test_scan_result_to_dict(self):
        """ScanResult.to_dict includes all fields."""
        scan = ScanResult(
            tickers=[TickerResult(symbol='AAPL', close=150.0, action='BUY')],
            scan_time='2024-12-21T12:00:00',
        )
        
        d = scan.to_dict()
        
        assert 'tickers' in d
        assert 'buy_signals' in d
        assert 'sell_signals' in d
        assert 'scan_time' in d
