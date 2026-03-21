"""
Integration tests for AA Points Monitor.
Tests the full pipeline from mock data to alert evaluation.
"""

import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from core.database import Database
from core.normalizer import normalize_merchant
from core.scorer import calculate_stack_yield, calculate_deal_score, StackedDeal
from core.stack_detector import detect_stacked_opportunities
from alerts.evaluator import evaluate_deals, should_send_alert


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


@pytest.fixture
def populated_db(temp_db):
    """Create a database with sample data."""
    now = datetime.now().isoformat()

    # Insert SimplyMiles offers
    offers = [
        ("Amazon Kindle", "flat_bonus", 135, 135, 5.0, None),
        ("Stitch Fix", "flat_bonus", 1065, 1065, 50.0, None),
        ("TurboTax", "per_dollar", 13, 13, None, None),
        ("Lyft", "per_dollar", 4, 4, None, None),
    ]

    for name, offer_type, miles, lp, min_spend, expires in offers:
        temp_db.insert_simplymiles_offer(
            merchant_name=name,
            merchant_name_normalized=normalize_merchant(name),
            offer_type=offer_type,
            miles_amount=miles,
            lp_amount=lp,
            min_spend=min_spend,
            expires_at=expires,
            expiring_soon=False,
            scraped_at=now
        )

    # Insert Portal rates
    portal_merchants = [
        ("Amazon Kindle", 2.0, False, "Electronics"),
        ("Stitch Fix", 3.0, True, "Clothing"),
        ("TurboTax", 5.0, True, "Services"),
        ("Lyft", 2.0, False, "Travel"),
        ("Target", 1.0, False, "Shopping"),
    ]

    for name, rate, is_bonus, category in portal_merchants:
        temp_db.insert_portal_rate(
            merchant_name=name,
            merchant_name_normalized=normalize_merchant(name),
            miles_per_dollar=rate,
            is_bonus_rate=is_bonus,
            category=category,
            url=None,
            scraped_at=now
        )

    return temp_db


class TestFullPipeline:
    """Tests for the complete pipeline flow."""

    def test_scrape_to_detection_flow(self, populated_db):
        """Test data flows correctly from scrape to detection."""
        # Verify data was inserted
        offers = populated_db.get_active_simplymiles_offers()
        assert len(offers) == 4

        rates = populated_db.get_latest_portal_rates()
        assert len(rates) == 5

    def test_stacked_deal_calculation(self):
        """Test StackedDeal calculates correctly."""
        # Kindle example from docs
        deal = StackedDeal(
            merchant_name="Amazon Kindle",
            portal_rate=2.0,
            simplymiles_type='flat_bonus',
            simplymiles_amount=135,
            simplymiles_min_spend=5.0,
            simplymiles_expires=None
        )

        assert deal.min_spend == 5.0
        assert deal.portal_miles == 10  # 2 * 5
        assert deal.simplymiles_miles == 135
        assert deal.cc_miles == 5  # 1 * 5
        assert deal.total_miles == 150
        assert deal.base_yield == pytest.approx(30.0, rel=0.01)

    def test_stitch_fix_calculation(self):
        """Test Stitch Fix example."""
        deal = StackedDeal(
            merchant_name="Stitch Fix",
            portal_rate=3.0,
            simplymiles_type='flat_bonus',
            simplymiles_amount=1065,
            simplymiles_min_spend=50.0,
            simplymiles_expires=None
        )

        # Portal: 3 * 50 = 150
        # Simply: 1065
        # CC: 1 * 50 = 50
        # Total: 1265 / 50 = 25.3
        assert deal.total_miles == 1265
        assert deal.base_yield == pytest.approx(25.3, rel=0.01)


class TestAlertEvaluation:
    """Tests for alert evaluation logic."""

    def test_immediate_threshold(self):
        """Test deals above immediate threshold are flagged."""
        deals = [
            {'merchant_name': 'High Yield', 'deal_score': 20.0},
            {'merchant_name': 'Medium Yield', 'deal_score': 12.0},
            {'merchant_name': 'Low Yield', 'deal_score': 5.0},
        ]

        immediate, digest = evaluate_deals(deals, deal_type='stack')

        # Threshold is 15 for immediate, 10 for digest
        assert len(immediate) == 1
        assert immediate[0]['merchant_name'] == 'High Yield'

        assert len(digest) == 1
        assert digest[0]['merchant_name'] == 'Medium Yield'

    def test_deduplication(self, temp_db):
        """Test that recently alerted deals are deduplicated."""
        # Record an alert
        temp_db.insert_alert(
            alert_type='immediate',
            deal_type='stack',
            deal_identifier='Amazon',
            deal_score=25.0,
            sent_at=datetime.now().isoformat()
        )

        # Check if should alert again - directly using the database
        was_alerted, prev_score = temp_db.was_recently_alerted(
            deal_identifier='Amazon',
            cooldown_hours=24
        )

        assert was_alerted is True
        assert prev_score == 25.0

    def test_improvement_detection(self, temp_db):
        """Test that significant improvements trigger new alerts."""
        from config.settings import get_settings

        # Record an alert with lower score
        temp_db.insert_alert(
            alert_type='immediate',
            deal_type='stack',
            deal_identifier='Amazon',
            deal_score=20.0,
            sent_at=datetime.now().isoformat()
        )

        # Check with significantly higher score (>20% improvement)
        was_alerted, prev_score = temp_db.was_recently_alerted(
            deal_identifier='Amazon',
            cooldown_hours=24
        )

        assert was_alerted is True
        assert prev_score == 20.0

        # Calculate improvement
        current_score = 30.0  # 50% improvement
        improvement_pct = ((current_score - prev_score) / prev_score) * 100
        settings = get_settings()

        # Should trigger new alert if improvement > threshold
        assert improvement_pct >= settings.thresholds.improvement_threshold_pct


class TestMerchantMatching:
    """Tests for merchant matching between sources."""

    def test_exact_match(self):
        """Test exact matches work."""
        simplymiles_name = normalize_merchant("Amazon Kindle")
        portal_name = normalize_merchant("Amazon Kindle")

        assert simplymiles_name == portal_name

    def test_fuzzy_match(self):
        """Test fuzzy matching catches variations."""
        from core.normalizer import find_best_match

        candidates = [
            normalize_merchant("Amazon"),
            normalize_merchant("Walmart"),
            normalize_merchant("Target"),
        ]

        # Should match despite slight difference
        result = find_best_match(
            normalize_merchant("Amazon.com"),
            candidates,
            threshold=80
        )

        assert result is not None
        assert result[0] == "amazon"

    def test_alias_resolution(self):
        """Test that aliases are resolved correctly."""
        # "uber eats" should become "ubereats"
        normalized = normalize_merchant("Uber Eats")
        assert normalized == "ubereats"


class TestScoringIntegration:
    """Tests for scoring with real-world scenarios."""

    def test_low_commitment_bonus(self):
        """Test low spend gets bonus."""
        base_yield = 10.0

        # $25 spend should get 1.4x bonus
        score_low = calculate_deal_score(base_yield, min_spend=25.0)

        # $300 spend should get no bonus
        score_high = calculate_deal_score(base_yield, min_spend=300.0)

        assert score_low > score_high
        assert score_low == pytest.approx(14.0, rel=0.01)  # 10 * 1.4
        assert score_high == pytest.approx(10.0, rel=0.01)

    def test_expiring_urgency(self):
        """Test expiring deals get bonus."""
        base_yield = 10.0
        expires_soon = (datetime.now() + timedelta(hours=24)).isoformat()
        expires_later = (datetime.now() + timedelta(days=7)).isoformat()

        score_urgent = calculate_deal_score(
            base_yield,
            min_spend=300.0,
            expires_at=expires_soon
        )

        score_not_urgent = calculate_deal_score(
            base_yield,
            min_spend=300.0,
            expires_at=expires_later
        )

        assert score_urgent > score_not_urgent
        assert score_urgent == pytest.approx(12.0, rel=0.01)  # 10 * 1.2


class TestDataFreshness:
    """Tests for data freshness handling."""

    def test_staleness_detection(self, temp_db):
        """Test that stale data is detected."""
        # Fresh database should have no data -> stale
        assert temp_db.is_data_stale('simplymiles') is True
        assert temp_db.is_data_stale('portal') is True

        # Insert fresh data
        temp_db.insert_simplymiles_offer(
            merchant_name="Test",
            merchant_name_normalized="test",
            offer_type="flat_bonus",
            miles_amount=100,
            lp_amount=100,
            min_spend=10.0,
            expires_at=None,
            expiring_soon=False,
            scraped_at=datetime.now().isoformat()
        )

        # Now should not be stale
        assert temp_db.is_data_stale('simplymiles') is False

    def test_freshness_report(self, temp_db):
        """Test freshness report generation."""
        report = temp_db.get_data_freshness_report()

        assert 'simplymiles' in report
        assert 'portal' in report
        assert 'hotels' in report

        # All should be stale initially
        for source in report:
            assert report[source]['is_stale'] is True


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_full_flow_mock_data(self, populated_db):
        """Test the full flow with mock data."""
        # Get offers and rates
        offers = populated_db.get_active_simplymiles_offers()
        rates = populated_db.get_latest_portal_rates()

        assert len(offers) > 0
        assert len(rates) > 0

        # Verify we can create stacked deals
        for offer in offers[:2]:
            deal = StackedDeal(
                merchant_name=offer['merchant_name'],
                portal_rate=2.0,  # Mock portal rate
                simplymiles_type=offer['offer_type'],
                simplymiles_amount=offer['miles_amount'],
                simplymiles_min_spend=offer['min_spend'],
                simplymiles_expires=offer['expires_at']
            )

            assert deal.total_miles > 0
            assert deal.base_yield > 0
            assert deal.deal_score > 0

        # Verify alert evaluation works
        mock_deals = [
            {'merchant_name': 'Test', 'deal_score': 20.0},
        ]

        immediate, digest = evaluate_deals(mock_deals, deal_type='stack')
        assert len(immediate) == 1  # 20 > 15 threshold

