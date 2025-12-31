"""Tests for data models."""

import pytest
from pydantic import ValidationError

from src.scanner.models import ConfigEntry, Task


class TestConfigEntry:
    """Tests for ConfigEntry model."""

    def test_valid_config_entry(self):
        """Test creating a valid ConfigEntry."""
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
        assert entry.enabled is True
        assert entry.ticker == "AAPL"
        assert entry.price == 150.0
        assert entry.type == "Call"

    def test_config_entry_defaults(self):
        """Test ConfigEntry with default values."""
        entry = ConfigEntry(
            enabled=True,
            ticker="TSLA",
            price=200.0,
            type="Put",
            month="February",
            year="2025",
            start_date="2025-01-01",
            end_date="2025-12-31",
        )
        assert entry.strike == 0.0
        assert entry.otm_min == 0.0
        assert entry.otm_max == 100.0
        assert entry.open_interest == 0

    def test_invalid_option_type(self):
        """Test that invalid option type raises ValidationError."""
        with pytest.raises(ValidationError):
            ConfigEntry(
                enabled=True,
                ticker="AAPL",
                price=150.0,
                type="Invalid",
                month="January",
                year="2025",
                start_date="2025-01-01",
                end_date="2025-12-31",
            )


class TestTask:
    """Tests for Task model."""

    def test_valid_task(self):
        """Test creating a valid Task."""
        task = Task(
            ticker="NVDA",
            date="2025-06-20",
            price=500.0,
            strike=550.0,
            type="Call",
            otm_min=5.0,
            otm_max=20.0,
            open_interest=100,
        )
        assert task.ticker == "NVDA"
        assert task.date == "2025-06-20"
        assert task.price == 500.0
        assert task.type == "Call"

    def test_invalid_task_type(self):
        """Test that invalid task type raises ValidationError."""
        with pytest.raises(ValidationError):
            Task(
                ticker="NVDA",
                date="2025-06-20",
                price=500.0,
                strike=550.0,
                type="Invalid",
                otm_min=5.0,
                otm_max=20.0,
                open_interest=100,
            )

