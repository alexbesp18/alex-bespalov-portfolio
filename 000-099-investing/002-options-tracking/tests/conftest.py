"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path
import tempfile
import os


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        config_data = {
            "enabled": True,
            "ticker": "AAPL",
            "price": 150.0,
            "type": "Call",
            "month": "January",
            "year": "2025",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
        }
        import json

        f.write(json.dumps(config_data))
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        os.unlink(temp_path)


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    from src.scanner.models import Task

    return Task(
        ticker="AAPL",
        date="2025-06-20",
        price=150.0,
        strike=160.0,
        type="Call",
        otm_min=5.0,
        otm_max=20.0,
        open_interest=100,
    )

