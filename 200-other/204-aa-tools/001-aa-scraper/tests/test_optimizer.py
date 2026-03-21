"""
Tests for the budget optimizer and arbitrage intelligence.
"""

import pytest
from datetime import datetime, timedelta

from core.optimizer import (
    TopPick,
    AllocationResult,
    AllocationItem,
    calculate_efficiency,
    identify_top_pick,
    optimize_allocation,
    format_allocation_summary,
)


class TestCalculateEfficiency:
    """Tests for efficiency calculation."""

    def test_basic_efficiency(self):
        """Efficiency = deal_score / min_spend."""
        deal = {'deal_score': 30.0, 'min_spend': 5}
        assert calculate_efficiency(deal) == 6.0

    def test_efficiency_with_min_spend_required(self):
        """Should use min_spend_required if present."""
        deal = {'deal_score': 20.0, 'min_spend_required': 10, 'min_spend': 50}
        assert calculate_efficiency(deal) == 2.0

    def test_zero_spend_returns_zero(self):
        """Zero spend should return zero efficiency (not divide by zero)."""
        deal = {'deal_score': 30.0, 'min_spend': 0}
        assert calculate_efficiency(deal) == 0.0

    def test_negative_spend_returns_zero(self):
        """Negative spend should return zero."""
        deal = {'deal_score': 30.0, 'min_spend': -10}
        assert calculate_efficiency(deal) == 0.0

    def test_missing_score_uses_zero(self):
        """Missing deal_score should default to 0."""
        deal = {'min_spend': 10}
        assert calculate_efficiency(deal) == 0.0


class TestIdentifyTopPick:
    """Tests for top pick identification."""

    def test_empty_deals_returns_none(self):
        """Empty list should return None."""
        assert identify_top_pick([]) is None

    def test_single_deal_is_top_pick(self):
        """Single deal should be the top pick."""
        deals = [{'merchant_name': 'Test', 'deal_score': 15.0, 'min_spend': 10, 'total_miles': 150}]
        top = identify_top_pick(deals)
        assert top is not None
        assert top.merchant_name == 'Test'
        assert top.deal_score == 15.0

    def test_highest_score_wins(self):
        """Highest deal_score should generally win."""
        deals = [
            {'merchant_name': 'Low', 'deal_score': 10.0, 'min_spend': 50, 'total_miles': 500},
            {'merchant_name': 'High', 'deal_score': 30.0, 'min_spend': 50, 'total_miles': 1500},
        ]
        top = identify_top_pick(deals)
        assert top.merchant_name == 'High'

    def test_low_commitment_bonus(self):
        """Low commitment deals get boosted."""
        deals = [
            {'merchant_name': 'Expensive', 'deal_score': 20.0, 'min_spend': 100, 'total_miles': 2000},
            {'merchant_name': 'Cheap', 'deal_score': 18.0, 'min_spend': 5, 'total_miles': 90},
        ]
        top = identify_top_pick(deals)
        # Cheap should win due to low commitment bonus (1.3x for <$20)
        assert top.merchant_name == 'Cheap'

    def test_why_reasons_populated(self):
        """Top pick should have why_reasons."""
        deals = [{'merchant_name': 'Kindle', 'deal_score': 30.0, 'min_spend': 5, 'total_miles': 150}]
        top = identify_top_pick(deals)
        assert len(top.why_reasons) > 0
        assert 'low commitment' in top.why_text.lower() or 'efficiency' in top.why_text.lower()

    def test_expiring_soon_bonus(self):
        """Expiring deals get urgency bonus."""
        tomorrow = (datetime.now() + timedelta(hours=24)).isoformat()
        next_month = (datetime.now() + timedelta(days=30)).isoformat()

        deals = [
            {'merchant_name': 'Later', 'deal_score': 15.0, 'min_spend': 10, 'total_miles': 150, 'simplymiles_expires': next_month},
            {'merchant_name': 'Soon', 'deal_score': 14.0, 'min_spend': 10, 'total_miles': 140, 'simplymiles_expires': tomorrow},
        ]
        top = identify_top_pick(deals)
        # Soon should win due to urgency bonus
        assert top.merchant_name == 'Soon'


class TestOptimizeAllocation:
    """Tests for budget allocation optimization."""

    def test_empty_deals_returns_empty_allocation(self):
        """Empty deals list should return empty allocation."""
        result = optimize_allocation([], budget=500)
        assert result.total_spent == 0
        assert result.total_miles == 0
        assert len(result.allocations) == 0
        assert result.remaining_budget == 500

    def test_single_deal_allocation(self):
        """Single deal should be allocated up to max_per_merchant."""
        deals = [{'merchant_name': 'Test', 'deal_score': 15.0, 'min_spend': 10, 'total_miles': 150}]
        result = optimize_allocation(deals, budget=100, max_per_merchant=5)

        assert result.total_spent == 50  # 5 × $10
        assert result.total_miles == 750  # 5 × 150
        assert len(result.allocations) == 1
        assert result.allocations[0].quantity == 5

    def test_budget_constraint(self):
        """Should not exceed budget."""
        deals = [{'merchant_name': 'Test', 'deal_score': 15.0, 'min_spend': 100, 'total_miles': 1500}]
        result = optimize_allocation(deals, budget=250)

        assert result.total_spent <= 250
        assert result.allocations[0].quantity == 2

    def test_diversity_across_merchants(self):
        """Should allocate across multiple merchants."""
        deals = [
            {'merchant_name': 'A', 'deal_score': 20.0, 'min_spend': 10, 'total_miles': 200},
            {'merchant_name': 'B', 'deal_score': 18.0, 'min_spend': 10, 'total_miles': 180},
            {'merchant_name': 'C', 'deal_score': 15.0, 'min_spend': 10, 'total_miles': 150},
        ]
        result = optimize_allocation(deals, budget=200, max_per_merchant=5)

        # Should have multiple merchants
        assert len(result.allocations) >= 2

    def test_efficiency_priority(self):
        """Higher efficiency deals should be prioritized."""
        deals = [
            {'merchant_name': 'Low Efficiency', 'deal_score': 10.0, 'min_spend': 100, 'total_miles': 1000},
            {'merchant_name': 'High Efficiency', 'deal_score': 30.0, 'min_spend': 5, 'total_miles': 150},
        ]
        result = optimize_allocation(deals, budget=50, max_per_merchant=5)

        # High efficiency should be fully allocated first
        high_eff = next((a for a in result.allocations if a.merchant_name == 'High Efficiency'), None)
        assert high_eff is not None
        assert high_eff.quantity == 5

    def test_min_deal_score_filter(self):
        """Deals below min_deal_score should be excluded."""
        deals = [
            {'merchant_name': 'Good', 'deal_score': 15.0, 'min_spend': 10, 'total_miles': 150},
            {'merchant_name': 'Bad', 'deal_score': 5.0, 'min_spend': 10, 'total_miles': 50},
        ]
        result = optimize_allocation(deals, budget=100, min_deal_score=10.0)

        # Only Good should be allocated
        assert len(result.allocations) == 1
        assert result.allocations[0].merchant_name == 'Good'

    def test_blended_yield_calculation(self):
        """Blended yield should be total_miles / total_spent."""
        deals = [
            {'merchant_name': 'A', 'deal_score': 20.0, 'min_spend': 10, 'total_miles': 200},
        ]
        result = optimize_allocation(deals, budget=50, max_per_merchant=5)

        expected_blended = result.total_miles / result.total_spent
        assert abs(result.blended_yield - expected_blended) < 0.01

    def test_remaining_budget_calculated(self):
        """Remaining budget should be budget - total_spent."""
        deals = [{'merchant_name': 'Test', 'deal_score': 15.0, 'min_spend': 30, 'total_miles': 450}]
        result = optimize_allocation(deals, budget=100, max_per_merchant=3)

        assert result.remaining_budget == 100 - result.total_spent

    def test_real_world_kindle_scenario(self):
        """Test with realistic Kindle deal data."""
        deals = [
            {'merchant_name': 'Kindle', 'deal_score': 30.0, 'min_spend': 5, 'total_miles': 150, 'base_yield': 30.0},
            {'merchant_name': 'TurboTax', 'deal_score': 17.0, 'min_spend': 50, 'total_miles': 850, 'base_yield': 17.0},
            {'merchant_name': 'DoorDash', 'deal_score': 12.0, 'min_spend': 20, 'total_miles': 240, 'base_yield': 12.0},
        ]
        result = optimize_allocation(deals, budget=500)

        # Should allocate meaningfully
        assert result.total_spent > 0
        assert result.total_miles > 0
        assert result.blended_yield > 10.0  # Should be decent yield


class TestAllocationResult:
    """Tests for AllocationResult dataclass."""

    def test_utilization_percentage(self):
        """Utilization should be (total_spent / budget) * 100."""
        result = AllocationResult(
            budget=500,
            total_spent=375,
            total_miles=5000,
            blended_yield=13.3,
            remaining_budget=125
        )
        assert result.utilization_pct == 75.0

    def test_zero_budget_utilization(self):
        """Zero budget should return 0% utilization."""
        result = AllocationResult(
            budget=0,
            total_spent=0,
            total_miles=0,
            blended_yield=0,
            remaining_budget=0
        )
        assert result.utilization_pct == 0.0


class TestTopPick:
    """Tests for TopPick dataclass."""

    def test_why_text_joins_reasons(self):
        """why_text should join reasons with commas."""
        pick = TopPick(
            merchant_name='Test',
            deal_score=20.0,
            base_yield=20.0,
            min_spend=10,
            total_miles=200,
            expires_at=None,
            why_reasons=['high efficiency', 'low commitment']
        )
        assert pick.why_text == 'high efficiency, low commitment'

    def test_why_text_empty_reasons(self):
        """Empty reasons should give default text."""
        pick = TopPick(
            merchant_name='Test',
            deal_score=20.0,
            base_yield=20.0,
            min_spend=10,
            total_miles=200,
            expires_at=None,
            why_reasons=[]
        )
        assert pick.why_text == 'Best available deal'


class TestFormatAllocationSummary:
    """Tests for allocation summary formatting."""

    def test_empty_allocation_message(self):
        """Empty allocation should return helpful message."""
        result = AllocationResult(
            budget=500,
            total_spent=0,
            total_miles=0,
            blended_yield=0,
            allocations=[],
            remaining_budget=500
        )
        summary = format_allocation_summary(result)
        assert 'No deals' in summary

    def test_format_with_allocations(self):
        """Should format allocations nicely."""
        result = AllocationResult(
            budget=500,
            total_spent=375,
            total_miles=5000,
            blended_yield=13.3,
            allocations=[
                AllocationItem('Kindle', 5, 5, 25, 150, 750, 30.0, 30.0),
                AllocationItem('TurboTax', 3, 50, 150, 850, 2550, 17.0, 17.0),
            ],
            remaining_budget=125
        )
        summary = format_allocation_summary(result)

        assert 'OPTIMAL $500 ALLOCATION' in summary
        assert 'Kindle' in summary
        assert 'TurboTax' in summary
        assert '5,000 LPs' in summary or '5000 LPs' in summary
        assert 'Blended yield' in summary
