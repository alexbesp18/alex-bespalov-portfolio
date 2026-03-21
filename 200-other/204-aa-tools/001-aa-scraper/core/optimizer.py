"""
Budget allocation optimizer for AA Points Monitor.
Implements greedy allocation strategy for maximum LP yield.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class AllocationItem:
    """A single allocation in the optimal spending plan."""
    merchant_name: str
    quantity: int  # How many times to purchase
    spend_per: float  # Min spend per purchase
    total_spend: float
    miles_per: int  # Miles per purchase
    total_miles: int
    yield_ratio: float  # LP/$
    deal_score: float


@dataclass
class AllocationResult:
    """Result of budget optimization."""
    budget: float
    total_spent: float
    total_miles: int
    blended_yield: float  # Total miles / total spent
    allocations: List[AllocationItem] = field(default_factory=list)
    remaining_budget: float = 0.0

    @property
    def utilization_pct(self) -> float:
        """Percentage of budget utilized."""
        if self.budget <= 0:
            return 0.0
        return (self.total_spent / self.budget) * 100


@dataclass
class TopPick:
    """The single best deal with explanation."""
    merchant_name: str
    deal_score: float
    base_yield: float
    min_spend: float
    total_miles: int
    expires_at: Optional[str]
    why_reasons: List[str] = field(default_factory=list)

    @property
    def why_text(self) -> str:
        """Formatted explanation."""
        return ", ".join(self.why_reasons) if self.why_reasons else "Best available deal"


def calculate_efficiency(deal: Dict[str, Any]) -> float:
    """
    Calculate deal efficiency for allocation priority.

    Efficiency = deal_score / min_spend
    Higher is better - we want high-scoring deals with low commitment.
    """
    score = deal.get('deal_score', 0)
    min_spend = deal.get('min_spend_required', deal.get('min_spend', 10))

    if min_spend <= 0:
        return 0.0

    return score / min_spend


def identify_top_pick(deals: List[Dict[str, Any]]) -> Optional[TopPick]:
    """
    Identify the single best deal and explain why.

    Selection criteria (weighted):
    1. Deal score (primary)
    2. Efficiency (score / spend)
    3. Low commitment (prefer <$50)
    4. Urgency (expiring soon)
    """
    if not deals:
        return None

    get_settings()

    # Score each deal on multiple factors
    scored_deals = []
    for deal in deals:
        deal_score = deal.get('deal_score', 0)
        min_spend = deal.get('min_spend_required', deal.get('min_spend', 10))
        base_yield = deal.get('base_yield', deal_score)
        deal.get('total_miles', 0)
        expires = deal.get('simplymiles_expires')

        # Composite score
        efficiency = calculate_efficiency(deal)

        # Factors contributing to "top pick" status
        reasons = []
        composite = deal_score  # Start with raw score

        # Efficiency bonus
        if efficiency > 0.3:  # >0.3 means great efficiency
            composite *= 1.2
            reasons.append("high efficiency")

        # Low commitment is gold
        if min_spend < 20:
            composite *= 1.3
            reasons.append(f"very low commitment (${min_spend:.0f})")
        elif min_spend < 50:
            composite *= 1.15
            reasons.append(f"low commitment (${min_spend:.0f})")

        # Urgency
        if expires:
            from core.scorer import is_expiring_soon
            if is_expiring_soon(expires, hours=48):
                composite *= 1.1
                reasons.append("expiring soon")

        # High raw yield
        if base_yield >= 20:
            reasons.append(f"exceptional yield ({base_yield:.0f} LP/$)")
        elif base_yield >= 15:
            reasons.append(f"high yield ({base_yield:.0f} LP/$)")

        scored_deals.append({
            'deal': deal,
            'composite': composite,
            'reasons': reasons,
            'base_yield': base_yield,
        })

    # Sort by composite score
    scored_deals.sort(key=lambda x: x['composite'], reverse=True)

    top = scored_deals[0]
    deal = top['deal']

    return TopPick(
        merchant_name=deal.get('merchant_name', 'Unknown'),
        deal_score=deal.get('deal_score', 0),
        base_yield=top['base_yield'],
        min_spend=deal.get('min_spend_required', deal.get('min_spend', 10)),
        total_miles=deal.get('total_miles', 0),
        expires_at=deal.get('simplymiles_expires'),
        why_reasons=top['reasons'] if top['reasons'] else ["highest overall score"]
    )


def optimize_allocation(
    deals: List[Dict[str, Any]],
    budget: Optional[float] = None,
    max_per_merchant: int = 5,
    min_deal_score: float = 8.0
) -> AllocationResult:
    """
    Optimize budget allocation across available deals.

    Uses greedy algorithm:
    1. Filter deals by minimum score
    2. Sort by efficiency (deal_score / min_spend)
    3. Allocate to highest efficiency first
    4. Limit purchases per merchant for diversity
    5. Continue until budget exhausted

    Args:
        deals: List of deal opportunities
        budget: Total budget to allocate (default from settings)
        max_per_merchant: Maximum purchases per merchant (diversity)
        min_deal_score: Minimum deal score to consider

    Returns:
        AllocationResult with optimal allocation
    """
    settings = get_settings()
    budget = budget or settings.monthly_budget

    if not deals:
        return AllocationResult(
            budget=budget,
            total_spent=0,
            total_miles=0,
            blended_yield=0,
            remaining_budget=budget
        )

    # Filter and prepare deals
    valid_deals = []
    for deal in deals:
        score = deal.get('deal_score', 0)
        min_spend = deal.get('min_spend_required', deal.get('min_spend', 0))

        if score >= min_deal_score and min_spend > 0:
            valid_deals.append({
                **deal,
                'efficiency': calculate_efficiency(deal)
            })

    # Sort by efficiency (highest first)
    valid_deals.sort(key=lambda x: x['efficiency'], reverse=True)

    # Greedy allocation
    allocations = []
    merchant_counts: Dict[str, int] = {}
    remaining = budget
    total_spent = 0
    total_miles = 0

    # Keep going until we can't allocate any more
    changed = True
    while changed and remaining > 0:
        changed = False

        for deal in valid_deals:
            merchant = deal.get('merchant_name', 'Unknown')
            min_spend = deal.get('min_spend_required', deal.get('min_spend', 10))
            deal_miles = deal.get('total_miles', 0)
            deal_score = deal.get('deal_score', 0)
            base_yield = deal.get('base_yield', deal_score)

            # Check if we can afford this and haven't maxed out this merchant
            current_count = merchant_counts.get(merchant, 0)

            if min_spend <= remaining and current_count < max_per_merchant:
                # Allocate one purchase
                merchant_counts[merchant] = current_count + 1
                remaining -= min_spend
                total_spent += min_spend
                total_miles += deal_miles

                # Find or create allocation item
                existing = next((a for a in allocations if a.merchant_name == merchant), None)
                if existing:
                    existing.quantity += 1
                    existing.total_spend += min_spend
                    existing.total_miles += deal_miles
                else:
                    allocations.append(AllocationItem(
                        merchant_name=merchant,
                        quantity=1,
                        spend_per=min_spend,
                        total_spend=min_spend,
                        miles_per=deal_miles,
                        total_miles=deal_miles,
                        yield_ratio=base_yield,
                        deal_score=deal_score
                    ))

                changed = True
                break  # Start over from highest efficiency

    # Sort allocations by total miles (most valuable first)
    allocations.sort(key=lambda x: x.total_miles, reverse=True)

    blended_yield = total_miles / total_spent if total_spent > 0 else 0

    result = AllocationResult(
        budget=budget,
        total_spent=total_spent,
        total_miles=total_miles,
        blended_yield=blended_yield,
        allocations=allocations,
        remaining_budget=remaining
    )

    logger.info(f"Optimized ${budget:.0f} budget: ${total_spent:.0f} spent → "
                f"{total_miles:,} LPs ({blended_yield:.1f} LP/$ blended)")

    return result


def format_allocation_summary(result: AllocationResult) -> str:
    """Format allocation result for text display."""
    if not result.allocations:
        return "No deals meet minimum criteria for allocation."

    lines = [f"OPTIMAL ${result.budget:.0f} ALLOCATION:"]

    for alloc in result.allocations:
        qty_str = f"{alloc.quantity}×" if alloc.quantity > 1 else ""
        lines.append(
            f"  {qty_str} {alloc.merchant_name} "
            f"(${alloc.total_spend:.0f}) → {alloc.total_miles:,} LPs"
        )

    lines.append("")
    lines.append(f"Total: ${result.total_spent:.0f} → {result.total_miles:,} LPs")
    lines.append(f"Blended yield: {result.blended_yield:.1f} LP/$")

    if result.remaining_budget > 10:
        lines.append(f"Remaining: ${result.remaining_budget:.0f} (no good deals)")

    return "\n".join(lines)
