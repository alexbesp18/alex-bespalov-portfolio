"""
Hotel scoring with star rating preferences for AA Points Monitor.

Implements quality-adjusted yield scoring:
- 4-5 star hotels get a bonus
- 1-3 star hotels need exceptional yields to surface
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import statistics

# Star rating multipliers for adjusted scoring
STAR_MULTIPLIERS = {
    5: 1.25,   # 5-star gets 25% boost
    4: 1.15,   # 4-star gets 15% boost
    3: 1.00,   # 3-star neutral
    2: 0.85,   # 2-star needs 15% better yield to compete
    1: 0.70,   # 1-star needs 30% better yield
    0: 0.60,   # Unknown/unrated
}

# Thresholds for "exceptional" deals by star rating
# A budget hotel must exceed this to surface alongside premium options
EXCEPTIONAL_THRESHOLDS = {
    5: 20.0,   # 5-star at 20+ LP/$ is exceptional
    4: 22.0,   # 4-star at 22+ LP/$ is exceptional
    3: 28.0,   # 3-star needs 28+ to be noteworthy
    2: 40.0,   # 2-star needs 40+ LP/$ ("once in a lifetime")
    1: 50.0,   # 1-star needs 50+ LP/$ (unicorn)
    0: 50.0,   # Unknown needs to be exceptional
}


@dataclass
class ScoredHotel:
    """A hotel with quality-adjusted scoring."""
    hotel_name: str
    city: str
    stars: int
    raw_yield: float
    adjusted_score: float
    is_exceptional: bool
    total_cost: float
    total_miles: int
    check_in: str
    check_out: str

    @property
    def tier(self) -> str:
        """Return tier: 'premium' (4-5 star) or 'budget' (1-3 star)."""
        return 'premium' if self.stars >= 4 else 'budget'


def get_star_multiplier(stars: int) -> float:
    """Get the score multiplier for a star rating."""
    return STAR_MULTIPLIERS.get(stars, STAR_MULTIPLIERS[0])


def get_exceptional_threshold(stars: int) -> float:
    """Get the exceptional yield threshold for a star rating."""
    return EXCEPTIONAL_THRESHOLDS.get(stars, EXCEPTIONAL_THRESHOLDS[0])


def calculate_hotel_score(
    yield_ratio: float,
    stars: int,
    is_austin: bool = False
) -> Tuple[float, bool]:
    """
    Calculate quality-adjusted hotel score.

    Args:
        yield_ratio: Raw miles/$ yield
        stars: Hotel star rating (1-5)
        is_austin: Whether this is a local Austin hotel

    Returns:
        Tuple of (adjusted_score, is_exceptional)
    """
    multiplier = get_star_multiplier(stars)
    adjusted_score = yield_ratio * multiplier

    # Austin bonus
    if is_austin:
        adjusted_score *= 1.15

    # Check if exceptional for its tier
    threshold = get_exceptional_threshold(stars)
    is_exceptional = yield_ratio >= threshold

    return adjusted_score, is_exceptional


def score_hotel_result(
    hotel_data: Dict[str, Any],
    city: str,
    is_austin: bool = False
) -> Optional[ScoredHotel]:
    """
    Score a hotel result from the API.

    Args:
        hotel_data: Raw hotel dict from search
        city: City name
        is_austin: Whether this is Austin (local)

    Returns:
        ScoredHotel or None if invalid
    """
    try:
        stars = hotel_data.get('stars', 0)
        yield_ratio = hotel_data.get('yield_ratio', 0)

        if yield_ratio <= 0:
            return None

        adjusted_score, is_exceptional = calculate_hotel_score(
            yield_ratio, stars, is_austin
        )

        return ScoredHotel(
            hotel_name=hotel_data.get('hotel_name', 'Unknown'),
            city=city,
            stars=stars,
            raw_yield=yield_ratio,
            adjusted_score=adjusted_score,
            is_exceptional=is_exceptional,
            total_cost=hotel_data.get('total_cost', 0),
            total_miles=hotel_data.get('total_miles', 0),
            check_in=hotel_data.get('check_in', ''),
            check_out=hotel_data.get('check_out', '')
        )

    except (KeyError, TypeError, ValueError):
        return None


def categorize_hotels(
    hotels: List[Dict[str, Any]],
    city: str,
    is_austin: bool = False
) -> Tuple[List[ScoredHotel], List[ScoredHotel]]:
    """
    Categorize hotels into premium picks and exceptional budget finds.

    Args:
        hotels: List of hotel dicts
        city: City name
        is_austin: Whether this is Austin

    Returns:
        Tuple of (premium_hotels, exceptional_budget_hotels)
    """
    premium = []
    budget_exceptional = []

    for hotel in hotels:
        scored = score_hotel_result(hotel, city, is_austin)
        if not scored:
            continue

        if scored.tier == 'premium':
            premium.append(scored)
        elif scored.is_exceptional:
            # Only include budget if truly exceptional
            budget_exceptional.append(scored)

    # Sort by adjusted score
    premium.sort(key=lambda x: x.adjusted_score, reverse=True)
    budget_exceptional.sort(key=lambda x: x.raw_yield, reverse=True)

    return premium, budget_exceptional


def calculate_matrix_stats(hotels: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate comprehensive statistics for yield matrix.

    Args:
        hotels: List of hotel dicts with 'yield_ratio' and 'stars'

    Returns:
        Dict with all stats needed for matrix entry
    """
    if not hotels:
        return {
            'avg_yield': None,
            'max_yield': None,
            'min_yield': None,
            'median_yield': None,
            'deal_count': 0,
            'avg_yield_5star': None,
            'avg_yield_4star': None,
            'avg_yield_3star': None,
            'avg_yield_2star': None,
            'avg_yield_1star': None,
            'count_5star': 0,
            'count_4star': 0,
            'count_3star': 0,
            'count_2star': 0,
            'count_1star': 0,
        }

    yields = [h['yield_ratio'] for h in hotels if h.get('yield_ratio', 0) > 0]

    if not yields:
        return {
            'avg_yield': None,
            'max_yield': None,
            'min_yield': None,
            'median_yield': None,
            'deal_count': 0,
            'avg_yield_5star': None,
            'avg_yield_4star': None,
            'avg_yield_3star': None,
            'avg_yield_2star': None,
            'avg_yield_1star': None,
            'count_5star': 0,
            'count_4star': 0,
            'count_3star': 0,
            'count_2star': 0,
            'count_1star': 0,
        }

    # Group by stars
    by_stars = {1: [], 2: [], 3: [], 4: [], 5: []}
    for h in hotels:
        stars = h.get('stars', 0)
        yield_val = h.get('yield_ratio', 0)
        if stars in by_stars and yield_val > 0:
            by_stars[stars].append(yield_val)

    def safe_avg(lst):
        return sum(lst) / len(lst) if lst else None

    return {
        'avg_yield': safe_avg(yields),
        'max_yield': max(yields),
        'min_yield': min(yields),
        'median_yield': statistics.median(yields) if yields else None,
        'deal_count': len(yields),
        'avg_yield_5star': safe_avg(by_stars[5]),
        'avg_yield_4star': safe_avg(by_stars[4]),
        'avg_yield_3star': safe_avg(by_stars[3]),
        'avg_yield_2star': safe_avg(by_stars[2]),
        'avg_yield_1star': safe_avg(by_stars[1]),
        'count_5star': len(by_stars[5]),
        'count_4star': len(by_stars[4]),
        'count_3star': len(by_stars[3]),
        'count_2star': len(by_stars[2]),
        'count_1star': len(by_stars[1]),
    }


def find_top_hotels(
    hotels: List[Dict[str, Any]],
    city: str,
    is_austin: bool = False
) -> Tuple[Optional[Dict], Optional[Dict]]:
    """
    Find the top premium and top exceptional budget hotel.

    Args:
        hotels: List of hotel dicts
        city: City name
        is_austin: Whether Austin

    Returns:
        Tuple of (top_premium_hotel, top_budget_hotel)
        Each is a dict with hotel_name, yield_ratio, total_cost, total_miles, stars
        or None if no qualifying hotel found
    """
    premium, budget = categorize_hotels(hotels, city, is_austin)

    top_premium = None
    if premium:
        best = premium[0]
        top_premium = {
            'hotel_name': best.hotel_name,
            'yield_ratio': best.raw_yield,
            'total_cost': best.total_cost,
            'total_miles': best.total_miles,
            'stars': best.stars,
        }

    top_budget = None
    if budget:
        best = budget[0]
        top_budget = {
            'hotel_name': best.hotel_name,
            'yield_ratio': best.raw_yield,
            'total_cost': best.total_cost,
            'total_miles': best.total_miles,
            'stars': best.stars,
        }

    return top_premium, top_budget


def format_star_display(stars: int) -> str:
    """Format star rating for display."""
    if stars <= 0:
        return "☆"
    return "★" * stars + "☆" * (5 - stars)


def is_hotel_significant(
    hotel_name: str,
    city: str,
    day_of_week: int,
    star_rating: int,
    yield_ratio: float,
    db=None
) -> Tuple[bool, str, Optional[float]]:
    """
    Determine if a hotel deal is significant enough to alert on.

    Uses deviation-based alerting with OR logic:
    1. Statistical outlier: yield > avg + 1.5 * stddev
    2. Percentage above typical: yield > avg * 1.25
    3. Cold start: Use city star-tier average as baseline

    Args:
        hotel_name: Hotel name
        city: City name
        day_of_week: 0=Monday to 6=Sunday
        star_rating: Hotel star rating (1-5)
        yield_ratio: Current yield observation
        db: Database instance (optional, will get singleton if not provided)

    Returns:
        Tuple of (is_significant, reason, deviation_pct)
        - is_significant: True if should alert
        - reason: Human-readable explanation
        - deviation_pct: Percentage above baseline (or None)
    """
    if db is None:
        from core.database import get_database
        db = get_database()

    # Get hotel-specific baseline
    baseline = db.get_hotel_baseline(hotel_name, city, day_of_week)

    if baseline and baseline.get('observation_count', 0) >= 3:
        avg = baseline['avg_yield']
        stddev = baseline.get('stddev_yield') or 0

        # Statistical outlier check (1.5σ)
        if stddev > 0:
            threshold_1_5_sigma = avg + 1.5 * stddev
            if yield_ratio > threshold_1_5_sigma:
                pct = ((yield_ratio - avg) / avg) * 100 if avg > 0 else 0
                return True, f"{pct:.0f}% above typical (statistical outlier)", pct

        # 25% above typical check
        threshold_25_pct = avg * 1.25
        if yield_ratio > threshold_25_pct:
            pct = ((yield_ratio - avg) / avg) * 100 if avg > 0 else 0
            return True, f"{pct:.0f}% above typical", pct

        # Within normal range
        return False, "within normal range", None

    # Cold start: use city star-tier average as baseline
    tier_avg = db.get_city_star_tier_average(city, star_rating, day_of_week)

    if tier_avg is None:
        # Fall back to matrix prediction
        matrix_pred = db.get_matrix_yield_prediction(city, day_of_week, duration=1, advance_days=14)
        if matrix_pred:
            tier_key = f'avg_yield_{star_rating}star'
            tier_avg = matrix_pred.get(tier_key) or matrix_pred.get('avg_yield')

    if tier_avg and tier_avg > 0:
        if yield_ratio > tier_avg * 1.25:
            pct = ((yield_ratio - tier_avg) / tier_avg) * 100
            return True, f"above {star_rating}-star avg for {city} ({pct:.0f}%)", pct

        return False, f"below {star_rating}-star city average", None

    # No baseline data at all - apply standard exceptional threshold
    threshold = get_exceptional_threshold(star_rating)
    if yield_ratio >= threshold:
        return True, f"exceptional for {star_rating}-star (no baseline yet)", None

    return False, "insufficient baseline data", None


def filter_significant_hotels(
    hotels: List[Dict[str, Any]],
    db=None
) -> List[Dict[str, Any]]:
    """
    Filter hotels to only those with significant deviations from their baseline.

    Args:
        hotels: List of hotel dicts with hotel_name, city, check_in, stars, yield_ratio
        db: Database instance (optional)

    Returns:
        List of hotels that pass significance check, with added 'significance_reason' key
    """
    if db is None:
        from core.database import get_database
        db = get_database()

    significant = []

    for hotel in hotels:
        try:
            from datetime import datetime
            check_in_dt = datetime.fromisoformat(hotel['check_in'])
            day_of_week = check_in_dt.weekday()

            is_sig, reason, deviation_pct = is_hotel_significant(
                hotel_name=hotel['hotel_name'],
                city=hotel['city'],
                day_of_week=day_of_week,
                star_rating=hotel.get('stars', 3),
                yield_ratio=hotel['yield_ratio'],
                db=db
            )

            if is_sig:
                hotel_copy = hotel.copy()
                hotel_copy['significance_reason'] = reason
                hotel_copy['deviation_pct'] = deviation_pct
                significant.append(hotel_copy)

        except (KeyError, ValueError, TypeError):
            continue

    return significant
