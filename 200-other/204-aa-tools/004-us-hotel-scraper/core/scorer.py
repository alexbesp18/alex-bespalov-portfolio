"""
Hotel scoring with star rating adjustments.

Implements quality-adjusted yield scoring:
- 4-5 star hotels get a bonus
- 1-3 star hotels need exceptional yields to surface
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from config.settings import get_settings


@dataclass
class ScoredHotel:
    """A hotel with quality-adjusted scoring."""
    hotel_name: str
    city_name: str
    state: str
    stars: int
    raw_yield: float
    adjusted_score: float
    is_exceptional: bool
    total_cost: float
    total_miles: int
    check_in: str
    check_out: str
    nights: int
    url: Optional[str] = None

    @property
    def tier(self) -> str:
        """Return tier: 'premium' (4-5 star) or 'budget' (1-3 star)."""
        return 'premium' if self.stars >= 4 else 'budget'


def calculate_deal_score(
    yield_ratio: float,
    total_cost: float,
    stars: int = 3,
) -> float:
    """
    Calculate quality-adjusted deal score.

    Args:
        yield_ratio: Raw miles/$ yield
        total_cost: Total hotel cost
        stars: Hotel star rating (1-5)

    Returns:
        Adjusted deal score
    """
    settings = get_settings()

    # Apply star multiplier
    multiplier = settings.get_star_multiplier(stars)
    score = yield_ratio * multiplier

    # Low commitment bonus (prefer smaller spends)
    if total_cost < 50:
        score *= 1.4  # +40%
    elif total_cost < 100:
        score *= 1.3  # +30%
    elif total_cost < 200:
        score *= 1.1  # +10%
    elif total_cost > 500:
        score *= 0.8  # -20% penalty

    return score


def is_exceptional(yield_ratio: float, stars: int) -> bool:
    """Check if yield is exceptional for the star rating."""
    settings = get_settings()
    threshold = settings.get_exceptional_threshold(stars)
    return yield_ratio >= threshold


def score_hotel(hotel_data: Dict[str, Any]) -> Optional[ScoredHotel]:
    """
    Score a hotel result.

    Args:
        hotel_data: Hotel dict from API parsing

    Returns:
        ScoredHotel or None if invalid
    """
    try:
        yield_ratio = hotel_data.get('yield_ratio', 0)
        if yield_ratio <= 0:
            return None

        stars = hotel_data.get('stars', 0)
        total_cost = hotel_data.get('total_cost', 0)

        adjusted_score = calculate_deal_score(yield_ratio, total_cost, stars)
        exceptional = is_exceptional(yield_ratio, stars)

        return ScoredHotel(
            hotel_name=hotel_data.get('hotel_name', 'Unknown'),
            city_name=hotel_data.get('city_name', ''),
            state=hotel_data.get('state', ''),
            stars=stars,
            raw_yield=yield_ratio,
            adjusted_score=adjusted_score,
            is_exceptional=exceptional,
            total_cost=total_cost,
            total_miles=hotel_data.get('total_miles', 0),
            check_in=hotel_data.get('check_in', ''),
            check_out=hotel_data.get('check_out', ''),
            nights=hotel_data.get('nights', 1),
            url=hotel_data.get('url'),
        )

    except (KeyError, TypeError, ValueError):
        return None


def categorize_hotels(
    hotels: List[Dict[str, Any]],
) -> Tuple[List[ScoredHotel], List[ScoredHotel]]:
    """
    Categorize hotels into premium picks and exceptional budget finds.

    Args:
        hotels: List of hotel dicts

    Returns:
        Tuple of (premium_hotels, exceptional_budget_hotels)
    """
    premium = []
    budget_exceptional = []

    for hotel in hotels:
        scored = score_hotel(hotel)
        if not scored:
            continue

        if scored.tier == 'premium':
            premium.append(scored)
        elif scored.is_exceptional:
            budget_exceptional.append(scored)

    # Sort by adjusted score
    premium.sort(key=lambda x: x.adjusted_score, reverse=True)
    budget_exceptional.sort(key=lambda x: x.raw_yield, reverse=True)

    return premium, budget_exceptional


def format_star_display(stars: int) -> str:
    """Format star rating for display."""
    if stars <= 0:
        return "Unrated"
    return "★" * stars + "☆" * (5 - stars)
