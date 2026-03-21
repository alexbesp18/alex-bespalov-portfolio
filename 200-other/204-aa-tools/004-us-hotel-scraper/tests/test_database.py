"""Tests for database module."""

import pytest
from pathlib import Path
import tempfile
import os

# Set test database path before imports
os.environ["DATABASE_PATH"] = ":memory:"


def test_database_init():
    """Test database initialization."""
    from core.database import Database

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)

        assert db_path.exists()


def test_city_operations():
    """Test city CRUD operations."""
    from core.database import Database

    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(Path(tmpdir) / "test.db")

        # Insert city
        city_id = db.upsert_city(
            msa_name="Test Metro",
            city_name="Test City",
            state="TX",
            agoda_place_id="AGODA_CITY|123",
            population=100000,
        )

        assert city_id > 0

        # Retrieve city
        city = db.get_city_by_name("Test City", "TX")
        assert city is not None
        assert city["agoda_place_id"] == "AGODA_CITY|123"


def test_stats():
    """Test statistics retrieval."""
    from core.database import Database

    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(Path(tmpdir) / "test.db")

        stats = db.get_stats()

        assert "total_cities" in stats
        assert "active_deals" in stats
        assert "avg_yield" in stats
