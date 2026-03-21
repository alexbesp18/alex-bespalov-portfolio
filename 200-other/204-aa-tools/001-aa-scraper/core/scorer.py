"""
Deal scoring logic for AA Points Monitor.
Calculates yields and applies modifiers based on Alex's preferences.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class StackedDeal:
    """Represents a stacked earning opportunity."""

    merchant_name: str

    # Portal layer
    portal_rate: float  # miles per dollar

    # SimplyMiles layer
    simplymiles_type: str  # 'flat_bonus' or 'per_dollar'
    simplymiles_amount: int  # bonus amount or per-dollar rate
    simplymiles_min_spend: Optional[float]
    simplymiles_expires: Optional[str]

    # Computed values
    min_spend: float = 0.0
    portal_miles: int = 0
    simplymiles_miles: int = 0
    cc_miles: int = 0
    total_miles: int = 0
    base_yield: float = 0.0
    deal_score: float = 0.0

    def __post_init__(self):
        """Calculate all derived values."""
        self.min_spend = self._calculate_min_spend()
        self.portal_miles = int(self.portal_rate * self.min_spend)
        self.simplymiles_miles = self._calculate_simplymiles_miles()
        self.cc_miles = int(self.min_spend * get_settings().scoring.cc_earning_rate)
        self.total_miles = self.portal_miles + self.simplymiles_miles + self.cc_miles
        self.base_yield = self.total_miles / self.min_spend if self.min_spend > 0 else 0
        self.deal_score = calculate_deal_score(
            base_yield=self.base_yield,
            min_spend=self.min_spend,
            expires_at=self.simplymiles_expires,
            is_austin=False
        )

    def _calculate_min_spend(self) -> float:
        """Determine minimum spend for this deal."""
        if self.simplymiles_type == 'flat_bonus' and self.simplymiles_min_spend:
            return self.simplymiles_min_spend
        # For per-dollar offers or no min spend, use a reasonable default
        return max(self.simplymiles_min_spend or 10.0, 10.0)

    def _calculate_simplymiles_miles(self) -> int:
        """Calculate SimplyMiles contribution."""
        if self.simplymiles_type == 'flat_bonus':
            return self.simplymiles_amount
        else:  # per_dollar
            return int(self.simplymiles_amount * self.min_spend)


@dataclass
class HotelDeal:
    """Represents a hotel earning opportunity."""

    hotel_name: str
    city: str
    state: str
    nightly_rate: float
    nights: int
    base_miles: int
    bonus_miles: int

    # Computed values
    total_cost: float = 0.0
    total_miles: int = 0
    base_yield: float = 0.0
    deal_score: float = 0.0

    def __post_init__(self):
        """Calculate all derived values."""
        self.total_cost = self.nightly_rate * self.nights
        self.total_miles = self.base_miles + self.bonus_miles
        self.base_yield = self.total_miles / self.total_cost if self.total_cost > 0 else 0

        # Check if Austin (local bonus)
        is_austin = self.city.lower() == 'austin' and self.state.upper() == 'TX'

        self.deal_score = calculate_deal_score(
            base_yield=self.base_yield,
            min_spend=self.total_cost,
            expires_at=None,  # Hotels don't expire the same way
            is_austin=is_austin
        )


def calculate_stack_yield(
    portal_rate: float,
    simplymiles_type: str,
    simplymiles_amount: int,
    spend_amount: float
) -> float:
    """
    Calculate combined yield from stacking portal + simplymiles + CC.

    Args:
        portal_rate: Miles per dollar from eShopping portal
        simplymiles_type: 'flat_bonus' or 'per_dollar'
        simplymiles_amount: Bonus amount or per-dollar rate
        spend_amount: How much we're spending

    Returns:
        Combined yield as LP per dollar
    """
    if spend_amount <= 0:
        return 0.0

    settings = get_settings()

    # Layer 1: Portal
    portal_miles = portal_rate * spend_amount

    # Layer 2: SimplyMiles
    if simplymiles_type == 'flat_bonus':
        simplymiles_miles = simplymiles_amount
    else:  # per_dollar
        simplymiles_miles = simplymiles_amount * spend_amount

    # Layer 3: Credit Card
    cc_miles = spend_amount * settings.scoring.cc_earning_rate

    total_miles = portal_miles + simplymiles_miles + cc_miles
    yield_ratio = total_miles / spend_amount

    return yield_ratio


def calculate_hotel_yield(total_miles: int, total_cost: float) -> float:
    """
    Calculate yield for a hotel deal.

    Args:
        total_miles: Total miles earned (base + bonus)
        total_cost: Total cost of stay

    Returns:
        Yield as LP per dollar
    """
    if total_cost <= 0:
        return 0.0

    return total_miles / total_cost


def calculate_deal_score(
    base_yield: float,
    min_spend: float,
    expires_at: Optional[str] = None,
    is_austin: bool = False
) -> float:
    """
    Apply modifiers to base yield based on Alex's preferences.

    Framework: "Minimal dollar commitment, maximum LP yield"

    Args:
        base_yield: Raw LP/$ ratio
        min_spend: Minimum spend required
        expires_at: ISO date string of expiration (if any)
        is_austin: Whether this is an Austin hotel (local bonus)

    Returns:
        Modified deal score
    """
    settings = get_settings()
    scoring = settings.scoring

    score = base_yield

    # Low commitment bonus (prefer smaller spends)
    if min_spend < 50:
        score *= scoring.bonus_under_50
    elif min_spend < 100:
        score *= scoring.bonus_under_100
    elif min_spend < 200:
        score *= scoring.bonus_under_200
    elif min_spend > 500:
        score *= scoring.penalty_over_500

    # Urgency bonus (expiring within 48 hours)
    if expires_at:
        try:
            expiry = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            if isinstance(expiry, datetime):
                # Handle timezone-naive comparison
                now = datetime.now()
                if expiry.tzinfo:
                    now = datetime.now(expiry.tzinfo)

                time_until_expiry = expiry - now
                if time_until_expiry <= timedelta(hours=48):
                    score *= scoring.urgency_bonus
        except (ValueError, TypeError) as e:
            logger.debug(f"Could not parse expiration date '{expires_at}': {e}")

    # Austin local bonus (for hotels)
    if is_austin:
        score *= scoring.austin_bonus

    return round(score, 2)


def is_expiring_soon(expires_at: Optional[str], hours: int = 48) -> bool:
    """
    Check if an offer is expiring within the specified hours.

    Args:
        expires_at: ISO date string of expiration
        hours: Threshold in hours (default 48)

    Returns:
        True if expiring within threshold
    """
    if not expires_at:
        return False

    try:
        expiry = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        now = datetime.now()

        if expiry.tzinfo:
            now = datetime.now(expiry.tzinfo)

        time_until_expiry = expiry - now
        return timedelta(0) < time_until_expiry <= timedelta(hours=hours)
    except (ValueError, TypeError):
        return False


def categorize_deal(deal_score: float, deal_type: str = 'stack') -> str:
    """
    Categorize a deal based on its score.

    Args:
        deal_score: The calculated deal score
        deal_type: 'stack', 'hotel', or 'portal'

    Returns:
        Category: 'exceptional', 'good', 'average', or 'skip'
    """
    settings = get_settings()
    thresholds = settings.thresholds

    if deal_type == 'stack':
        immediate = thresholds.stack_immediate_alert
        digest = thresholds.stack_daily_digest
    elif deal_type == 'hotel':
        immediate = thresholds.hotel_immediate_alert
        digest = thresholds.hotel_daily_digest
    else:  # portal
        immediate = thresholds.portal_immediate_alert
        digest = thresholds.portal_daily_digest

    if deal_score >= immediate:
        return 'exceptional'
    elif deal_score >= digest:
        return 'good'
    elif deal_score >= digest * 0.7:
        return 'average'
    else:
        return 'skip'


def format_yield(yield_value: float) -> str:
    """Format yield for display."""
    return f"{yield_value:.1f} LP/$"


def format_deal_summary(
    merchant_name: str,
    min_spend: float,
    total_miles: int,
    deal_score: float,
    expires_at: Optional[str] = None
) -> str:
    """
    Format a deal summary for display.

    Returns:
        Human-readable deal summary
    """
    summary = f"{merchant_name} — {deal_score:.1f} LP/$ (spend ${min_spend:.0f}, earn {total_miles:,} LPs)"

    if expires_at:
        if is_expiring_soon(expires_at):
            summary += " — EXPIRING SOON!"
        else:
            try:
                expiry = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                summary += f" — Expires {expiry.strftime('%m/%d')}"
            except ValueError:
                pass

    return summary

