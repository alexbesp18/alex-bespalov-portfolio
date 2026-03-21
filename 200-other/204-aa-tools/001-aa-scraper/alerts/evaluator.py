"""
Alert evaluator for AA Points Monitor.
Checks deals against thresholds and handles deduplication.
Includes arbitrage intelligence: top pick selection and budget optimization.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from config.settings import get_settings
from core.database import get_database
from core.optimizer import TopPick, AllocationResult, identify_top_pick, optimize_allocation

logger = logging.getLogger(__name__)


def evaluate_deals(
    opportunities: List[Dict[str, Any]],
    deal_type: str = 'stack'
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Evaluate deals and split into immediate alerts and digest candidates.

    Args:
        opportunities: List of deal opportunities
        deal_type: 'stack', 'hotel', or 'portal'

    Returns:
        Tuple of (immediate_alerts, digest_candidates)
    """
    settings = get_settings()
    thresholds = settings.thresholds

    # Get thresholds based on deal type
    if deal_type == 'stack':
        immediate_threshold = thresholds.stack_immediate_alert
        digest_threshold = thresholds.stack_daily_digest
    elif deal_type == 'hotel':
        immediate_threshold = thresholds.hotel_immediate_alert
        digest_threshold = thresholds.hotel_daily_digest
    else:  # portal
        immediate_threshold = thresholds.portal_immediate_alert
        digest_threshold = thresholds.portal_daily_digest

    immediate_alerts = []
    digest_candidates = []

    for opp in opportunities:
        score = opp.get('deal_score', 0)

        if score >= immediate_threshold:
            immediate_alerts.append(opp)
        elif score >= digest_threshold:
            digest_candidates.append(opp)

    logger.info(f"Evaluated {len(opportunities)} {deal_type} deals: "
                f"{len(immediate_alerts)} immediate, {len(digest_candidates)} digest")

    return immediate_alerts, digest_candidates


def should_send_alert(
    deal_identifier: str,
    current_score: float,
    check_improvement: bool = True
) -> Tuple[bool, Optional[str]]:
    """
    Check if we should send an alert for this deal.

    Considers:
    - Cooldown period (don't spam for same deal)
    - Improvement detection (alert if significantly better)

    Args:
        deal_identifier: Unique identifier for the deal (e.g., merchant name)
        current_score: Current deal score
        check_improvement: Whether to check for improvements

    Returns:
        Tuple of (should_send, reason)
    """
    settings = get_settings()
    db = get_database()

    # Check if recently alerted
    was_alerted, previous_score = db.was_recently_alerted(
        deal_identifier=deal_identifier,
        cooldown_hours=settings.thresholds.alert_cooldown_hours
    )

    if not was_alerted:
        return True, "new_deal"

    # Check for improvement
    if check_improvement and previous_score:
        improvement_pct = ((current_score - previous_score) / previous_score) * 100

        if improvement_pct >= settings.thresholds.improvement_threshold_pct:
            return True, f"improved_{improvement_pct:.0f}pct"

    return False, "cooldown_active"


def filter_alertable_deals(
    deals: List[Dict[str, Any]],
    deal_type: str = 'stack'
) -> List[Dict[str, Any]]:
    """
    Filter deals to only those that should trigger alerts.

    For hotels, uses deviation-based filtering (only alert if significantly
    above the hotel's typical yield for that day of week).

    Args:
        deals: List of deals to check
        deal_type: Type of deals

    Returns:
        List of deals that should be alerted
    """
    alertable = []

    # For hotels, first filter to only significant deviations
    if deal_type == 'hotel':
        from core.hotel_scorer import filter_significant_hotels
        deals = filter_significant_hotels(deals)

    for deal in deals:
        # Create identifier
        if deal_type == 'hotel':
            identifier = f"{deal.get('hotel_name', '')}_{deal.get('city', '')}"
        else:
            identifier = deal.get('merchant_name', '')

        should_alert, reason = should_send_alert(
            deal_identifier=identifier,
            current_score=deal.get('deal_score', 0)
        )

        if should_alert:
            deal['alert_reason'] = reason
            alertable.append(deal)
        else:
            logger.debug(f"Skipping alert for {identifier}: {reason}")

    return alertable


def record_alerts(
    deals: List[Dict[str, Any]],
    alert_type: str,
    deal_type: str = 'stack'
):
    """
    Record that alerts were sent for these deals.

    Args:
        deals: List of deals that were alerted
        alert_type: 'immediate' or 'digest'
        deal_type: Type of deals
    """
    db = get_database()
    sent_at = datetime.now().isoformat()

    for deal in deals:
        # Create identifier
        if deal_type == 'hotel':
            identifier = f"{deal.get('hotel_name', '')}_{deal.get('city', '')}"
        else:
            identifier = deal.get('merchant_name', '')

        db.insert_alert(
            alert_type=alert_type,
            deal_type=deal_type,
            deal_identifier=identifier,
            deal_score=deal.get('deal_score', 0),
            sent_at=sent_at
        )

    logger.info(f"Recorded {len(deals)} {alert_type} alerts for {deal_type}")


def get_pending_immediate_alerts() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all pending immediate alerts across deal types.

    Returns:
        Dict mapping deal_type to list of alertable deals
    """
    from core.stack_detector import get_top_opportunities

    db = get_database()
    get_settings()

    pending = {
        'stack': [],
        'hotel': [],
    }

    # Check stacked opportunities
    opportunities = get_top_opportunities(limit=50)
    immediate, _ = evaluate_deals(opportunities, deal_type='stack')
    pending['stack'] = filter_alertable_deals(immediate, deal_type='stack')

    # Check hotel deals
    hotel_deals = db.get_top_hotel_deals(limit=20)
    hotel_immediate, _ = evaluate_deals(hotel_deals, deal_type='hotel')
    pending['hotel'] = filter_alertable_deals(hotel_immediate, deal_type='hotel')

    return pending


def get_full_immediate_alert_data() -> Dict[str, Any]:
    """
    Get complete data for rich immediate alerts with all deal categories.

    Unlike get_pending_immediate_alerts which only returns alertable deals,
    this returns ALL relevant deals across categories for a complete alert.

    Returns:
        Dict with:
        - 'alertable_stack': Stacked deals triggering alert (above threshold, not in cooldown)
        - 'alertable_hotel': Hotel deals triggering alert
        - 'stack': All top stacked deals (for context)
        - 'simplymiles_only': Top SimplyMiles-only deals
        - 'portal_only': Top portal-only deals
        - 'hotel': All top hotel deals
        - 'context': Historical context for enrichment
        - 'has_alerts': Boolean - whether any alertable deals exist
    """
    from core.stack_detector import get_top_opportunities

    db = get_database()
    settings = get_settings()

    # Get stacked opportunities
    opportunities = get_top_opportunities(limit=50)
    immediate_stack, digest_stack = evaluate_deals(opportunities, deal_type='stack')
    alertable_stack = filter_alertable_deals(immediate_stack, deal_type='stack')

    # Get hotel deals
    hotel_deals = db.get_top_hotel_deals(limit=20)
    immediate_hotel, digest_hotel = evaluate_deals(hotel_deals, deal_type='hotel')
    alertable_hotel = filter_alertable_deals(immediate_hotel, deal_type='hotel')

    # Get SimplyMiles-only and Portal-only for complete picture
    sm_only = get_simplymiles_only_deals(limit=10)
    portal_only = get_portal_only_deals(limit=10, min_rate=5.0)

    # Build context for the best deal
    context = {}
    all_immediate = alertable_stack + alertable_hotel
    if all_immediate:
        best_deal = max(all_immediate, key=lambda x: x.get('deal_score', 0))
        best_score = best_deal.get('deal_score', 0)

        # Calculate how this compares to average
        all_stacked_scores = [d.get('deal_score', 0) for d in opportunities if d.get('deal_score', 0) > 0]
        if all_stacked_scores:
            avg_score = sum(all_stacked_scores) / len(all_stacked_scores)
            if avg_score > 0:
                context['vs_average_pct'] = ((best_score / avg_score) - 1) * 100

    return {
        'alertable_stack': alertable_stack,
        'alertable_hotel': alertable_hotel,
        'stack': (immediate_stack + digest_stack)[:10],
        'simplymiles_only': sm_only[:5],
        'portal_only': portal_only[:5],
        'hotel': (immediate_hotel + digest_hotel)[:5],
        'context': context,
        'has_alerts': bool(alertable_stack or alertable_hotel)
    }


def get_digest_candidates() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all candidates for daily digest.

    Returns:
        Dict mapping deal_type to list of digest-worthy deals
    """
    from core.stack_detector import get_top_opportunities, get_expiring_soon_opportunities

    db = get_database()

    candidates = {
        'stack': [],
        'hotel': [],
        'expiring_soon': [],
    }

    # Get top stacked opportunities (already sorted by score)
    opportunities = get_top_opportunities(limit=20)
    _, digest = evaluate_deals(opportunities, deal_type='stack')

    # For digest, include immediate + digest threshold (best deals)
    immediate, _ = evaluate_deals(opportunities, deal_type='stack')
    candidates['stack'] = immediate + digest

    # Get expiring soon
    candidates['expiring_soon'] = get_expiring_soon_opportunities(hours=48)

    # Get hotel deals
    hotel_deals = db.get_top_hotel_deals(limit=10)
    hotel_immediate, hotel_digest = evaluate_deals(hotel_deals, deal_type='hotel')
    candidates['hotel'] = hotel_immediate + hotel_digest

    return candidates


def get_arbitrage_intelligence(
    deals: List[Dict[str, Any]],
    budget: Optional[float] = None
) -> Tuple[Optional[TopPick], Optional[AllocationResult]]:
    """
    Get arbitrage intelligence: top pick and optimal budget allocation.

    Args:
        deals: List of stacked deal opportunities
        budget: Budget to optimize (default from settings)

    Returns:
        Tuple of (top_pick, allocation_result)
    """
    if not deals:
        return None, None

    settings = get_settings()
    budget = budget or settings.monthly_budget

    # Identify the top pick
    top_pick = identify_top_pick(deals)

    # Calculate optimal allocation
    allocation = optimize_allocation(deals, budget=budget)

    logger.info(f"Arbitrage intelligence: Top pick = {top_pick.merchant_name if top_pick else 'None'}, "
                f"Allocation = {allocation.total_miles:,} LPs from ${allocation.total_spent:.0f}")

    return top_pick, allocation


def get_simplymiles_only_deals(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get SimplyMiles offers that don't have a matching Portal merchant.

    These are card-linked offers without portal stacking potential.

    Args:
        limit: Maximum deals to return

    Returns:
        List of SimplyMiles-only deals sorted by value
    """
    db = get_database()

    # Get all data
    sm_offers = db.get_active_simplymiles_offers()
    portal_rates = db.get_latest_portal_rates()
    stacked = db.get_top_stacked_opportunities(limit=200)

    # Get normalized names of stacked merchants
    stacked_normalized = {s['merchant_name'].lower().strip() for s in stacked}
    portal_normalized = {r['merchant_name_normalized'] for r in portal_rates}

    sm_only = []
    for offer in sm_offers:
        # Skip if it's in stacked deals or has portal match
        if offer['merchant_name_normalized'] in portal_normalized:
            continue
        if offer['merchant_name'].lower().strip() in stacked_normalized:
            continue

        # Calculate effective yield for flat bonuses
        min_spend = offer.get('min_spend') or 10  # Default to $10 if not specified
        miles = offer.get('miles_amount', 0)
        lp = offer.get('lp_amount', 0)

        if offer['offer_type'] == 'flat_bonus' and min_spend > 0:
            yield_ratio = (miles + lp) / min_spend
        elif offer['offer_type'] == 'per_dollar':
            yield_ratio = miles + lp  # Per dollar rate
            min_spend = 10  # Assume $10 min for display
        else:
            yield_ratio = miles / 10 if miles else 0

        sm_only.append({
            'merchant_name': offer['merchant_name'],
            'offer_type': offer['offer_type'],
            'miles_amount': miles,
            'lp_amount': lp,
            'min_spend': min_spend,
            'total_miles': miles + lp,
            'yield_ratio': yield_ratio,
            'deal_score': yield_ratio,  # For consistent interface
            'expires_at': offer.get('expires_at'),
            'category': 'simplymiles_only'
        })

    # Sort by yield
    sm_only.sort(key=lambda x: x['yield_ratio'], reverse=True)
    return sm_only[:limit]


def get_portal_only_deals(limit: int = 10, min_rate: float = 8.0) -> List[Dict[str, Any]]:
    """
    Get high-value Portal merchants without SimplyMiles offers.

    These are portal-only opportunities (no stacking).

    Args:
        limit: Maximum deals to return
        min_rate: Minimum miles/$ rate to include

    Returns:
        List of Portal-only deals sorted by rate
    """
    db = get_database()
    settings = get_settings()

    # Get all data
    portal_rates = db.get_latest_portal_rates()
    stacked = db.get_top_stacked_opportunities(limit=200)

    # Get normalized names of stacked merchants
    stacked_normalized = {s['merchant_name'].lower().strip() for s in stacked}

    portal_only = []
    for rate in portal_rates:
        # Skip if it's in stacked deals
        if rate['merchant_name'].lower().strip() in stacked_normalized:
            continue
        if rate['merchant_name_normalized'] in stacked_normalized:
            continue

        miles_rate = rate.get('miles_per_dollar', 0)
        if miles_rate < min_rate:
            continue

        # Add CC miles (1 mi/$) for total yield
        total_yield = miles_rate + settings.scoring.cc_earning_rate

        portal_only.append({
            'merchant_name': rate['merchant_name'],
            'portal_rate': miles_rate,
            'cc_rate': settings.scoring.cc_earning_rate,
            'total_yield': total_yield,
            'deal_score': total_yield,  # For consistent interface
            'is_bonus': rate.get('is_bonus_rate', False),
            'category': 'portal_only'
        })

    # Sort by total yield
    portal_only.sort(key=lambda x: x['total_yield'], reverse=True)
    return portal_only[:limit]


def get_new_discoveries(days: int = 7) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get deals first discovered within the last N days.

    Cross-references discoveries with current active deals to only
    show discoveries that are still available.

    Args:
        days: How many days back to look for first_seen_at

    Returns:
        Dict with 'stack', 'hotel', 'simplymiles', 'portal' keys
    """
    from core.stack_detector import get_top_opportunities

    db = get_database()

    # Get raw discoveries
    raw_discoveries = db.get_new_discoveries(days=days)

    # Get current active deals for cross-reference
    current_stacked = {
        opp['merchant_name'].lower().strip()
        for opp in get_top_opportunities(limit=100)
    }
    current_hotels = {
        f"{h['hotel_name']}_{h['city']}"
        for h in db.get_top_hotel_deals(limit=50)
    }

    new_deals = {
        'stack': [],
        'hotel': [],
        'simplymiles': [],
        'portal': []
    }

    for disc in raw_discoveries:
        deal_type = disc['deal_type']
        identifier = disc['deal_identifier']

        # Only include if still active
        if deal_type == 'stack' and identifier.lower().strip() in current_stacked:
            new_deals['stack'].append(disc)
        elif deal_type == 'hotel' and identifier in current_hotels:
            new_deals['hotel'].append(disc)
        elif deal_type in ('simplymiles', 'portal'):
            # These we include regardless - they were seen recently
            new_deals[deal_type].append(disc)

    return new_deals


def get_full_digest_data() -> Dict[str, Any]:
    """
    Get complete data for daily digest including arbitrage intelligence.

    Returns:
        Dict with all digest data:
        - 'stack': List of stacked deals (Portal + SimplyMiles)
        - 'simplymiles_only': List of SimplyMiles-only deals
        - 'portal_only': List of Portal-only deals
        - 'hotel': List of hotel deals
        - 'expiring_soon': List of expiring deals
        - 'new_this_week': Dict of new discoveries by type
        - 'top_pick': TopPick object or None
        - 'allocation': AllocationResult object or None
        - 'health': Health status dict
    """
    from core.stack_detector import get_top_opportunities, get_expiring_soon_opportunities
    from core.hotel_scorer import filter_significant_hotels

    db = get_database()
    settings = get_settings()

    # Get stacked opportunities
    opportunities = get_top_opportunities(limit=50)

    # Split into immediate and digest
    immediate, digest = evaluate_deals(opportunities, deal_type='stack')
    all_stacked = immediate + digest

    # Get SimplyMiles-only and Portal-only deals
    sm_only = get_simplymiles_only_deals(limit=10)
    portal_only = get_portal_only_deals(limit=10, min_rate=8.0)

    # Get expiring soon
    expiring_soon = get_expiring_soon_opportunities(hours=48)

    # Get hotel deals - apply significance filtering for digest too
    hotel_deals = db.get_top_hotel_deals(limit=20)
    significant_hotels = filter_significant_hotels(hotel_deals)
    hotel_immediate, hotel_digest = evaluate_deals(significant_hotels, deal_type='hotel')
    all_hotels = hotel_immediate + hotel_digest

    # Get new discoveries for "New This Week" section
    new_this_week = get_new_discoveries(days=7)

    # Get arbitrage intelligence
    top_pick, allocation = get_arbitrage_intelligence(
        opportunities,  # Use full list for better optimization
        budget=settings.monthly_budget
    )

    # Get health status
    health_status = {}
    try:
        health_data = db.get_data_freshness_report()
        for scraper, data in health_data.items():
            health_status[scraper] = {
                'is_stale': data.get('is_stale', False),
                'age_hours': data.get('age_hours', 0)
            }
    except Exception as e:
        logger.warning(f"Could not get health status: {e}")

    return {
        'stack': all_stacked[:10],  # Top 10 stacked
        'simplymiles_only': sm_only[:5],  # Top 5 SM-only
        'portal_only': portal_only[:5],  # Top 5 portal-only
        'hotel': all_hotels[:5],  # Top 5 hotels (now filtered by significance)
        'expiring_soon': expiring_soon[:5],
        'new_this_week': new_this_week,
        'top_pick': top_pick,
        'allocation': allocation,
        'health': health_status
    }

