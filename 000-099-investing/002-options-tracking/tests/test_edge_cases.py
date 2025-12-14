"""Tests for edge cases and error handling."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from src.scanner.core import OptionsScanner
from src.scanner.models import ConfigEntry, Task


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_process_request_empty_stocks_cache(self):
        """Test processing request when ticker not in cache."""
        scanner = OptionsScanner()
        scanner.stocks = {}
        task = Task(
            ticker="UNKNOWN",
            date="2025-06-20",
            price=100.0,
            strike=110.0,
            type="Call",
            otm_min=5.0,
            otm_max=20.0,
            open_interest=0,
        )
        result = scanner.process_request(task)
        assert result is False

    def test_process_request_invalid_price(self):
        """Test processing request with invalid (zero) price."""
        scanner = OptionsScanner()
        mock_stock = MagicMock()
        mock_chain = MagicMock()
        mock_chain.calls.empty = False
        mock_chain.calls.__getitem__ = MagicMock(return_value=MagicMock(empty=False))
        mock_stock.option_chain.return_value = mock_chain
        scanner.stocks["TEST"] = mock_stock

        # Create task with valid data, then modify price to test runtime validation
        task = Task(
            ticker="TEST",
            date="2025-06-20",
            price=100.0,
            strike=110.0,
            type="Call",
            otm_min=5.0,
            otm_max=20.0,
            open_interest=0,
        )
        # Manually set invalid price to test runtime check
        task.price = 0.0
        result = scanner.process_request(task)
        assert result is False

    def test_process_request_invalid_otm_range(self):
        """Test processing request with invalid OTM range."""
        scanner = OptionsScanner()
        mock_stock = MagicMock()
        mock_chain = MagicMock()
        mock_chain.calls.empty = False
        mock_chain.calls.__getitem__ = MagicMock(return_value=MagicMock(empty=False))
        mock_stock.option_chain.return_value = mock_chain
        scanner.stocks["TEST"] = mock_stock

        # Create task with valid data, then modify OTM to test runtime validation
        task = Task(
            ticker="TEST",
            date="2025-06-20",
            price=100.0,
            strike=110.0,
            type="Call",
            otm_min=5.0,
            otm_max=20.0,
            open_interest=0,
        )
        # Manually set invalid OTM range to test runtime check
        task.otm_min = 20.0
        task.otm_max = 10.0
        result = scanner.process_request(task)
        assert result is False

    def test_date_list_empty_dates(self):
        """Test date_list with empty input."""
        scanner = OptionsScanner()
        result = scanner.date_list([], "2025-01-01", "2025-12-31")
        assert result == []

    def test_date_list_invalid_range(self):
        """Test date_list with invalid date range."""
        scanner = OptionsScanner()
        dates = ["2025-06-20"]
        result = scanner.date_list(dates, "2025-12-31", "2025-01-01")  # End before start
        assert result == []

    def test_config_entry_validation(self):
        """Test ConfigEntry validation."""
        # Valid entry
        entry = ConfigEntry(
            enabled=True,
            ticker="AAPL",
            price=150.0,
            type="Call",
            month="January",
            year="2025",
            start_date="2025-01-01",
            end_date="2025-12-31",
        )
        assert entry.ticker == "AAPL"

        # Invalid: end_date before start_date
        with pytest.raises(Exception):
            ConfigEntry(
                enabled=True,
                ticker="AAPL",
                price=150.0,
                type="Call",
                month="January",
                year="2025",
                start_date="2025-12-31",
                end_date="2025-01-01",
            )

        # Invalid: otm_max <= otm_min
        with pytest.raises(Exception):
            ConfigEntry(
                enabled=True,
                ticker="AAPL",
                price=150.0,
                type="Call",
                month="January",
                year="2025",
                start_date="2025-01-01",
                end_date="2025-12-31",
                otm_min=20.0,
                otm_max=10.0,
            )

    def test_task_validation(self):
        """Test Task validation."""
        # Invalid: otm_max <= otm_min
        with pytest.raises(Exception):
            Task(
                ticker="AAPL",
                date="2025-06-20",
                price=150.0,
                strike=160.0,
                type="Call",
                otm_min=20.0,
                otm_max=10.0,
                open_interest=100,
            )

        # Invalid: zero price
        with pytest.raises(Exception):
            Task(
                ticker="AAPL",
                date="2025-06-20",
                price=0.0,
                strike=160.0,
                type="Call",
                otm_min=5.0,
                otm_max=20.0,
                open_interest=100,
            )

    def test_check_config_race_condition(self):
        """Test check_config handles file deletion gracefully."""
        scanner = OptionsScanner()
        scanner.config_filename = Path("/nonexistent/file.jsonl")
        result = scanner.check_config()
        assert result is False

    def test_run_with_no_tasks(self):
        """Test run() exits gracefully when no tasks."""
        scanner = OptionsScanner()
        scanner.task_list = []
        scanner.process_config = MagicMock()
        scanner.process_config.return_value = None
        scanner.check_config = MagicMock(return_value=False)
        scanner.running = True

        # Should not raise exception
        scanner.run()

