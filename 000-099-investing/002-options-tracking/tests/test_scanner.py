"""Tests for scanner core functionality."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.scanner.core import OptionsScanner
from src.scanner.models import Task


class TestOptionsScanner:
    """Tests for OptionsScanner class."""

    def test_date_list_valid_range(self):
        """Test filtering dates within valid range."""
        scanner = OptionsScanner()
        dates = ["2025-01-01", "2025-02-01", "2025-03-01", "2025-04-01"]
        result = scanner.date_list(dates, "2025-01-15", "2025-03-15")
        assert "2025-02-01" in result
        assert "2025-03-01" in result
        assert "2025-01-01" not in result  # Before start
        assert "2025-04-01" not in result  # After end

    def test_date_list_empty_result(self):
        """Test date filtering with no matches."""
        scanner = OptionsScanner()
        dates = ["2025-01-01", "2025-02-01"]
        result = scanner.date_list(dates, "2025-03-01", "2025-04-01")
        assert result == []

    def test_date_list_invalid_format(self):
        """Test date filtering with invalid date format."""
        scanner = OptionsScanner()
        dates = ["2025-01-01", "invalid-date", "2025-03-01"]
        result = scanner.date_list(dates, "2025-01-01", "2025-12-31")
        assert "2025-01-01" in result
        assert "2025-03-01" in result
        assert "invalid-date" not in result

    def test_check_config_file_exists(self):
        """Test config check when file exists."""
        scanner = OptionsScanner()
        scanner.config_filename = MagicMock()
        scanner.config_filename.exists.return_value = True
        scanner.config_filename.stat.return_value.st_mtime = 1000.0

        result = scanner.check_config()
        assert result is False  # First check, no previous timestamp

        scanner.config_prev = 1000.0
        scanner.config_curr = 1000.0
        result = scanner.check_config()
        assert result is False  # No change

        scanner.config_prev = 1000.0
        scanner.config_curr = 2000.0
        result = scanner.check_config()
        assert result is True  # File changed

    def test_check_config_file_missing(self):
        """Test config check when file doesn't exist."""
        scanner = OptionsScanner()
        scanner.config_filename = MagicMock()
        scanner.config_filename.exists.return_value = False

        result = scanner.check_config()
        assert result is False

    @patch("src.scanner.core.yf")
    def test_get_ticker_success(self, mock_yf):
        """Test successful ticker retrieval."""
        scanner = OptionsScanner()
        mock_ticker_instance = MagicMock()
        mock_yf.Ticker.return_value = mock_ticker_instance

        result = scanner._get_ticker("AAPL")
        assert result == mock_ticker_instance
        mock_yf.Ticker.assert_called_once_with("AAPL")

    def test_signal_handler(self):
        """Test signal handler sets running to False."""
        scanner = OptionsScanner()
        assert scanner.running is True
        scanner._signal_handler(None, None)
        assert scanner.running is False

    @patch("src.scanner.core.logger")
    def test_send_notification(self, mock_logger):
        """Test notification logging."""
        scanner = OptionsScanner()
        task = Task(
            ticker="AAPL",
            date="2025-06-20",
            price=150.0,
            strike=160.0,
            type="Call",
            otm_min=5.0,
            otm_max=20.0,
            open_interest=100,
        )
        scanner.send_notification(task)
        # Verify logger.info was called with the expected message
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "Found OTM options" in call_args
        assert "AAPL" in call_args

