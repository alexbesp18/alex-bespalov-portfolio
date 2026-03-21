"""
Unit tests for deal scoring logic.
"""

import pytest
from datetime import datetime, timedelta

from core.scorer import (
    calculate_stack_yield,
    calculate_hotel_yield,
    calculate_deal_score,
    is_expiring_soon,
    categorize_deal,
    format_yield,
    format_deal_summary,
    StackedDeal,
    HotelDeal,
)


class TestCalculateStackYield:
    """Tests for calculate_stack_yield function."""

    def test_basic_yield_calculation(self):
        """Test basic yield with all three layers."""
        # Portal: 5 mi/$, SimplyMiles: flat 100 bonus, CC: 1 mi/$
        # Spend $20: Portal=100, Simply=100, CC=20 = 220 / 20 = 11 LP/$
        yield_result = calculate_stack_yield(
            portal_rate=5.0,
            simplymiles_type='flat_bonus',
            simplymiles_amount=100,
            spend_amount=20.0
        )
        assert yield_result == pytest.approx(11.0, rel=0.01)

    def test_per_dollar_simplymiles(self):
        """Test with per-dollar SimplyMiles offer."""
        # Portal: 3 mi/$, SimplyMiles: 5 mi/$, CC: 1 mi/$
        # Spend $100: Portal=300, Simply=500, CC=100 = 900 / 100 = 9 LP/$
        yield_result = calculate_stack_yield(
            portal_rate=3.0,
            simplymiles_type='per_dollar',
            simplymiles_amount=5,
            spend_amount=100.0
        )
        assert yield_result == pytest.approx(9.0, rel=0.01)

    def test_zero_spend(self):
        """Test with zero spend returns zero."""
        yield_result = calculate_stack_yield(
            portal_rate=5.0,
            simplymiles_type='flat_bonus',
            simplymiles_amount=100,
            spend_amount=0.0
        )
        assert yield_result == 0.0

    def test_kindle_example_from_docs(self):
        """Test the Kindle example from project docs."""
        # $5 spend: Portal 2mi/$=10, Simply 135 bonus, CC=5 = 150/5 = 30 LP/$
        yield_result = calculate_stack_yield(
            portal_rate=2.0,
            simplymiles_type='flat_bonus',
            simplymiles_amount=135,
            spend_amount=5.0
        )
        assert yield_result == pytest.approx(30.0, rel=0.01)

    def test_viator_example_from_docs(self):
        """Test the Viator example from project docs."""
        # $200 spend: Portal 5mi/$=1000, Simply 1000 bonus, CC=200 = 2200/200 = 11 LP/$
        yield_result = calculate_stack_yield(
            portal_rate=5.0,
            simplymiles_type='flat_bonus',
            simplymiles_amount=1000,
            spend_amount=200.0
        )
        assert yield_result == pytest.approx(11.0, rel=0.01)


class TestCalculateHotelYield:
    """Tests for calculate_hotel_yield function."""

    def test_basic_hotel_yield(self):
        """Test basic hotel yield calculation."""
        # 10,000 miles on $300 = 33.33 LP/$
        yield_result = calculate_hotel_yield(total_miles=10000, total_cost=300.0)
        assert yield_result == pytest.approx(33.33, rel=0.01)

    def test_zero_cost(self):
        """Test with zero cost returns zero."""
        yield_result = calculate_hotel_yield(total_miles=5000, total_cost=0.0)
        assert yield_result == 0.0


class TestCalculateDealScore:
    """Tests for calculate_deal_score function."""

    def test_low_commitment_bonus_under_50(self):
        """Test 1.4x bonus for spend under $50."""
        base = 10.0
        score = calculate_deal_score(base_yield=base, min_spend=25.0)
        assert score == pytest.approx(base * 1.4, rel=0.01)

    def test_low_commitment_bonus_under_100(self):
        """Test 1.3x bonus for spend $50-100."""
        base = 10.0
        score = calculate_deal_score(base_yield=base, min_spend=75.0)
        assert score == pytest.approx(base * 1.3, rel=0.01)

    def test_low_commitment_bonus_under_200(self):
        """Test 1.1x bonus for spend $100-200."""
        base = 10.0
        score = calculate_deal_score(base_yield=base, min_spend=150.0)
        assert score == pytest.approx(base * 1.1, rel=0.01)

    def test_high_commitment_penalty(self):
        """Test 0.8x penalty for spend over $500."""
        base = 10.0
        score = calculate_deal_score(base_yield=base, min_spend=750.0)
        assert score == pytest.approx(base * 0.8, rel=0.01)

    def test_no_modifier_in_middle(self):
        """Test no modifier for spend $200-500."""
        base = 10.0
        score = calculate_deal_score(base_yield=base, min_spend=350.0)
        assert score == pytest.approx(base, rel=0.01)

    def test_urgency_bonus(self):
        """Test 1.2x bonus for expiring within 48 hours."""
        base = 10.0
        # Expires in 24 hours
        expires = (datetime.now() + timedelta(hours=24)).isoformat()
        score = calculate_deal_score(
            base_yield=base,
            min_spend=350.0,  # No commitment modifier
            expires_at=expires
        )
        assert score == pytest.approx(base * 1.2, rel=0.01)

    def test_austin_bonus(self):
        """Test 1.15x bonus for Austin hotels."""
        base = 10.0
        score = calculate_deal_score(
            base_yield=base,
            min_spend=350.0,  # No commitment modifier
            is_austin=True
        )
        assert score == pytest.approx(base * 1.15, rel=0.01)

    def test_stacked_modifiers(self):
        """Test multiple modifiers stack multiplicatively."""
        base = 10.0
        expires = (datetime.now() + timedelta(hours=24)).isoformat()
        score = calculate_deal_score(
            base_yield=base,
            min_spend=25.0,  # 1.4x
            expires_at=expires,  # 1.2x
            is_austin=True  # 1.15x
        )
        expected = base * 1.4 * 1.2 * 1.15
        assert score == pytest.approx(expected, rel=0.01)


class TestIsExpiringSoon:
    """Tests for is_expiring_soon function."""

    def test_expiring_within_threshold(self):
        """Test returns True when expiring within hours."""
        expires = (datetime.now() + timedelta(hours=24)).isoformat()
        assert is_expiring_soon(expires, hours=48) is True

    def test_not_expiring_soon(self):
        """Test returns False when not expiring soon."""
        expires = (datetime.now() + timedelta(days=7)).isoformat()
        assert is_expiring_soon(expires, hours=48) is False

    def test_already_expired(self):
        """Test returns False when already expired."""
        expires = (datetime.now() - timedelta(hours=1)).isoformat()
        assert is_expiring_soon(expires) is False

    def test_no_expiration(self):
        """Test returns False when no expiration."""
        assert is_expiring_soon(None) is False
        assert is_expiring_soon("") is False


class TestCategorizeDeal:
    """Tests for categorize_deal function."""

    def test_exceptional_stack(self):
        """Test exceptional category for stacked deals."""
        # Threshold is 15 LP/$ for immediate
        assert categorize_deal(20.0, 'stack') == 'exceptional'

    def test_good_stack(self):
        """Test good category for stacked deals."""
        # Threshold is 10 LP/$ for digest
        assert categorize_deal(12.0, 'stack') == 'good'

    def test_average_stack(self):
        """Test average category (70% of digest threshold)."""
        assert categorize_deal(8.0, 'stack') == 'average'

    def test_skip_stack(self):
        """Test skip category for low-value deals."""
        assert categorize_deal(3.0, 'stack') == 'skip'

    def test_hotel_thresholds(self):
        """Test hotel-specific thresholds."""
        # Hotel immediate is 25 LP/$
        assert categorize_deal(30.0, 'hotel') == 'exceptional'
        assert categorize_deal(20.0, 'hotel') == 'good'


class TestStackedDeal:
    """Tests for StackedDeal dataclass."""

    def test_flat_bonus_deal(self):
        """Test StackedDeal with flat bonus."""
        deal = StackedDeal(
            merchant_name="Kindle",
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

    def test_per_dollar_deal(self):
        """Test StackedDeal with per-dollar offer."""
        deal = StackedDeal(
            merchant_name="TurboTax",
            portal_rate=3.0,
            simplymiles_type='per_dollar',
            simplymiles_amount=13,
            simplymiles_min_spend=50.0,
            simplymiles_expires=None
        )

        assert deal.min_spend == 50.0
        assert deal.portal_miles == 150  # 3 * 50
        assert deal.simplymiles_miles == 650  # 13 * 50
        assert deal.cc_miles == 50  # 1 * 50
        assert deal.total_miles == 850
        assert deal.base_yield == pytest.approx(17.0, rel=0.01)


class TestHotelDeal:
    """Tests for HotelDeal dataclass."""

    def test_hotel_deal_calculation(self):
        """Test HotelDeal calculations."""
        deal = HotelDeal(
            hotel_name="Marriott Downtown",
            city="Las Vegas",
            state="NV",
            nightly_rate=150.0,
            nights=2,
            base_miles=3000,
            bonus_miles=7000
        )

        assert deal.total_cost == 300.0
        assert deal.total_miles == 10000
        assert deal.base_yield == pytest.approx(33.33, rel=0.01)

    def test_austin_hotel_bonus(self):
        """Test Austin hotel gets local bonus."""
        deal = HotelDeal(
            hotel_name="Hilton Austin",
            city="Austin",
            state="TX",
            nightly_rate=200.0,
            nights=1,
            base_miles=2000,
            bonus_miles=3000
        )

        # Base yield = 5000/200 = 25, with Austin bonus = 25 * 1.15 = 28.75
        # But also has low commitment bonus for <$200
        assert deal.base_yield == pytest.approx(25.0, rel=0.01)
        # Score should be higher than base_yield due to Austin bonus
        assert deal.deal_score > deal.base_yield


class TestFormatFunctions:
    """Tests for formatting functions."""

    def test_format_yield(self):
        """Test yield formatting."""
        assert format_yield(15.5) == "15.5 LP/$"
        assert format_yield(10.0) == "10.0 LP/$"

    def test_format_deal_summary(self):
        """Test deal summary formatting."""
        summary = format_deal_summary(
            merchant_name="Amazon",
            min_spend=50.0,
            total_miles=500,
            deal_score=15.0
        )
        assert "Amazon" in summary
        assert "15.0 LP/$" in summary
        assert "$50" in summary
        assert "500" in summary

    def test_format_deal_summary_with_expiry(self):
        """Test deal summary with expiration."""
        expires = (datetime.now() + timedelta(hours=24)).isoformat()
        summary = format_deal_summary(
            merchant_name="Amazon",
            min_spend=50.0,
            total_miles=500,
            deal_score=15.0,
            expires_at=expires
        )
        assert "EXPIRING SOON" in summary

