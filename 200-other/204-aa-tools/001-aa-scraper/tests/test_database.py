"""
Unit tests for database operations.
"""

import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from core.database import Database


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    db = Database(db_path=db_path)
    yield db

    # Cleanup
    if db_path.exists():
        db_path.unlink()


class TestDatabaseSchema:
    """Tests for database initialization."""

    def test_creates_tables(self, temp_db):
        """Test that all tables are created."""
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table'
                ORDER BY name
            """)
            tables = [row['name'] for row in cursor.fetchall()]

        expected_tables = [
            'alert_history',
            'hotel_deals',
            'portal_rates',
            'scraper_health',
            'simplymiles_offers',
            'stacked_opportunities',
        ]

        for table in expected_tables:
            assert table in tables


class TestSimplyMilesOperations:
    """Tests for SimplyMiles CRUD operations."""

    def test_insert_and_retrieve_offer(self, temp_db):
        """Test inserting and retrieving an offer."""
        now = datetime.now().isoformat()

        offer_id = temp_db.insert_simplymiles_offer(
            merchant_name="Amazon Kindle",
            merchant_name_normalized="amazon kindle",
            offer_type="flat_bonus",
            miles_amount=135,
            lp_amount=135,
            min_spend=5.0,
            expires_at=(datetime.now() + timedelta(days=7)).isoformat(),
            expiring_soon=False,
            scraped_at=now
        )

        assert offer_id is not None

        offers = temp_db.get_active_simplymiles_offers()
        assert len(offers) == 1
        assert offers[0]['merchant_name'] == "Amazon Kindle"
        assert offers[0]['offer_type'] == "flat_bonus"

    def test_filters_expired_offers(self, temp_db):
        """Test that expired offers are filtered out."""
        now = datetime.now().isoformat()

        # Insert expired offer
        temp_db.insert_simplymiles_offer(
            merchant_name="Expired Merchant",
            merchant_name_normalized="expired merchant",
            offer_type="flat_bonus",
            miles_amount=100,
            lp_amount=100,
            min_spend=10.0,
            expires_at=(datetime.now() - timedelta(days=1)).isoformat(),
            expiring_soon=False,
            scraped_at=now
        )

        # Insert active offer
        temp_db.insert_simplymiles_offer(
            merchant_name="Active Merchant",
            merchant_name_normalized="active merchant",
            offer_type="flat_bonus",
            miles_amount=200,
            lp_amount=200,
            min_spend=20.0,
            expires_at=(datetime.now() + timedelta(days=7)).isoformat(),
            expiring_soon=False,
            scraped_at=now
        )

        offers = temp_db.get_active_simplymiles_offers()
        assert len(offers) == 1
        assert offers[0]['merchant_name'] == "Active Merchant"

    def test_clear_offers(self, temp_db):
        """Test clearing all offers."""
        now = datetime.now().isoformat()

        temp_db.insert_simplymiles_offer(
            merchant_name="Test",
            merchant_name_normalized="test",
            offer_type="flat_bonus",
            miles_amount=100,
            lp_amount=100,
            min_spend=10.0,
            expires_at=None,
            expiring_soon=False,
            scraped_at=now
        )

        temp_db.clear_simplymiles_offers()
        offers = temp_db.get_active_simplymiles_offers()
        assert len(offers) == 0


class TestPortalOperations:
    """Tests for Portal CRUD operations."""

    def test_insert_and_retrieve_rate(self, temp_db):
        """Test inserting and retrieving a portal rate."""
        now = datetime.now().isoformat()

        rate_id = temp_db.insert_portal_rate(
            merchant_name="Amazon",
            merchant_name_normalized="amazon",
            miles_per_dollar=5.0,
            is_bonus_rate=True,
            category="Shopping",
            url="https://example.com",
            scraped_at=now
        )

        assert rate_id is not None

        rates = temp_db.get_latest_portal_rates()
        assert len(rates) == 1
        assert rates[0]['merchant_name'] == "Amazon"
        assert rates[0]['miles_per_dollar'] == 5.0


class TestHotelOperations:
    """Tests for Hotel CRUD operations."""

    def test_insert_and_retrieve_deal(self, temp_db):
        """Test inserting and retrieving a hotel deal."""
        now = datetime.now().isoformat()
        check_in = (datetime.now() + timedelta(days=7)).isoformat()
        check_out = (datetime.now() + timedelta(days=9)).isoformat()

        deal_id = temp_db.insert_hotel_deal(
            hotel_name="Marriott Downtown",
            city="Las Vegas",
            state="NV",
            check_in=check_in,
            check_out=check_out,
            nightly_rate=150.0,
            base_miles=3000,
            bonus_miles=7000,
            total_miles=10000,
            total_cost=300.0,
            yield_ratio=33.33,
            deal_score=38.0,
            url="https://example.com",
            scraped_at=now
        )

        assert deal_id is not None

        deals = temp_db.get_top_hotel_deals(limit=10)
        assert len(deals) == 1
        assert deals[0]['hotel_name'] == "Marriott Downtown"

    def test_filter_by_city(self, temp_db):
        """Test filtering hotels by city."""
        now = datetime.now().isoformat()
        check_in = (datetime.now() + timedelta(days=7)).isoformat()
        check_out = (datetime.now() + timedelta(days=9)).isoformat()

        # Insert Vegas hotel
        temp_db.insert_hotel_deal(
            hotel_name="Vegas Hotel",
            city="Las Vegas",
            state="NV",
            check_in=check_in,
            check_out=check_out,
            nightly_rate=150.0,
            base_miles=3000,
            bonus_miles=7000,
            total_miles=10000,
            total_cost=300.0,
            yield_ratio=33.33,
            deal_score=38.0,
            url=None,
            scraped_at=now
        )

        # Insert Austin hotel
        temp_db.insert_hotel_deal(
            hotel_name="Austin Hotel",
            city="Austin",
            state="TX",
            check_in=check_in,
            check_out=check_out,
            nightly_rate=200.0,
            base_miles=5000,
            bonus_miles=5000,
            total_miles=10000,
            total_cost=400.0,
            yield_ratio=25.0,
            deal_score=30.0,
            url=None,
            scraped_at=now
        )

        vegas_deals = temp_db.get_top_hotel_deals(city="Las Vegas", limit=10)
        assert len(vegas_deals) == 1
        assert vegas_deals[0]['city'] == "Las Vegas"


class TestAlertHistory:
    """Tests for alert history operations."""

    def test_insert_and_check_alert(self, temp_db):
        """Test inserting and checking alert history."""
        now = datetime.now().isoformat()

        temp_db.insert_alert(
            alert_type="immediate",
            deal_type="stack",
            deal_identifier="amazon",
            deal_score=25.0,
            sent_at=now
        )

        was_alerted, prev_score = temp_db.was_recently_alerted(
            deal_identifier="amazon",
            cooldown_hours=24
        )

        assert was_alerted is True
        assert prev_score == 25.0

    def test_cooldown_expired(self, temp_db):
        """Test that old alerts don't count."""
        old_time = (datetime.now() - timedelta(hours=48)).isoformat()

        temp_db.insert_alert(
            alert_type="immediate",
            deal_type="stack",
            deal_identifier="amazon",
            deal_score=25.0,
            sent_at=old_time
        )

        was_alerted, prev_score = temp_db.was_recently_alerted(
            deal_identifier="amazon",
            cooldown_hours=24
        )

        assert was_alerted is False
        assert prev_score is None


class TestScraperHealth:
    """Tests for scraper health tracking."""

    def test_record_and_check_failures(self, temp_db):
        """Test recording scraper runs and checking failures."""
        # Record 3 failures
        for _ in range(3):
            temp_db.record_scraper_run(
                scraper_name="simplymiles",
                status="failure",
                error_message="Connection timeout"
            )

        failures = temp_db.get_consecutive_failures("simplymiles")
        assert failures == 3

    def test_success_resets_failures(self, temp_db):
        """Test that success resets failure count."""
        # Record 2 failures
        temp_db.record_scraper_run("simplymiles", "failure")
        temp_db.record_scraper_run("simplymiles", "failure")

        # Record success
        temp_db.record_scraper_run("simplymiles", "success", items_scraped=142)

        # Record 1 more failure
        temp_db.record_scraper_run("simplymiles", "failure")

        failures = temp_db.get_consecutive_failures("simplymiles")
        assert failures == 1

    def test_get_last_successful_scrape(self, temp_db):
        """Test getting last successful scrape time."""
        temp_db.record_scraper_run("portal", "success", items_scraped=200)

        last_success = temp_db.get_last_successful_scrape("portal")
        assert last_success is not None


class TestStalenessDetection:
    """Tests for data staleness detection."""

    def test_no_data_is_stale(self, temp_db):
        """Test that missing data is considered stale."""
        assert temp_db.is_data_stale("simplymiles") is True
        assert temp_db.is_data_stale("portal") is True
        assert temp_db.is_data_stale("hotels") is True

    def test_fresh_data_not_stale(self, temp_db):
        """Test that recent data is not stale."""
        now = datetime.now().isoformat()

        temp_db.insert_simplymiles_offer(
            merchant_name="Test",
            merchant_name_normalized="test",
            offer_type="flat_bonus",
            miles_amount=100,
            lp_amount=100,
            min_spend=10.0,
            expires_at=None,
            expiring_soon=False,
            scraped_at=now
        )

        assert temp_db.is_data_stale("simplymiles") is False

    def test_freshness_report(self, temp_db):
        """Test data freshness report."""
        report = temp_db.get_data_freshness_report()

        assert 'simplymiles' in report
        assert 'portal' in report
        assert 'hotels' in report

        # All should be stale (no data)
        for source in report:
            assert report[source]['is_stale'] is True

