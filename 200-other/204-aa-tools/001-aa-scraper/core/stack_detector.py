"""
Stack Detection Engine for AA Points Monitor.

Matches SimplyMiles offers with Portal merchants to find stacking opportunities.
Calculates combined yields and scores deals.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from config.settings import get_settings
from core.database import get_database
from core.normalizer import find_best_match
from core.scorer import StackedDeal

logger = logging.getLogger(__name__)


def detect_stacked_opportunities(
    check_staleness: bool = True,
    min_yield: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Find stacking opportunities by matching SimplyMiles offers with Portal rates.

    Args:
        check_staleness: If True, warn about stale data
        min_yield: Minimum combined yield to include (0 = all)

    Returns:
        List of stacked opportunity dictionaries, sorted by deal_score
    """
    settings = get_settings()
    db = get_database()

    # Check data freshness
    if check_staleness:
        freshness = db.get_data_freshness_report()

        if freshness['simplymiles']['is_stale']:
            logger.warning(f"SimplyMiles data is stale! Last scrape: {freshness['simplymiles']['latest_scrape']}")

        if freshness['portal']['is_stale']:
            logger.warning(f"Portal data is stale! Last scrape: {freshness['portal']['latest_scrape']}")

    # Get latest data
    simplymiles_offers = db.get_active_simplymiles_offers()
    portal_rates = db.get_latest_portal_rates()

    if not simplymiles_offers:
        logger.warning("No SimplyMiles offers available")
        return []

    if not portal_rates:
        logger.warning("No Portal rates available")
        return []

    logger.info(f"Matching {len(simplymiles_offers)} SimplyMiles offers against {len(portal_rates)} Portal merchants")

    # Build lookup for portal rates by normalized name
    portal_lookup = {rate['merchant_name_normalized']: rate for rate in portal_rates}
    portal_names = list(portal_lookup.keys())

    opportunities = []
    matched_count = 0

    for offer in simplymiles_offers:
        # Try exact match first
        sm_normalized = offer['merchant_name_normalized']

        if sm_normalized in portal_lookup:
            portal_rate = portal_lookup[sm_normalized]
            matched_count += 1
        else:
            # Try fuzzy match
            match_result = find_best_match(
                sm_normalized,
                portal_names,
                threshold=settings.matching.fuzzy_threshold
            )

            if match_result:
                matched_name, score = match_result
                portal_rate = portal_lookup[matched_name]
                matched_count += 1
                logger.debug(f"Fuzzy matched '{offer['merchant_name']}' -> '{portal_rate['merchant_name']}' (score: {score})")
            else:
                # No match found
                continue

        # Calculate stacked opportunity
        try:
            stacked = StackedDeal(
                merchant_name=offer['merchant_name'],
                portal_rate=portal_rate['miles_per_dollar'],
                simplymiles_type=offer['offer_type'],
                simplymiles_amount=offer['miles_amount'],
                simplymiles_min_spend=offer['min_spend'],
                simplymiles_expires=offer['expires_at']
            )

            # Skip if below minimum yield
            if stacked.base_yield < min_yield:
                continue

            opportunity = {
                'merchant_name': offer['merchant_name'],
                'portal_rate': portal_rate['miles_per_dollar'],
                'portal_miles': stacked.portal_miles,
                'portal_is_bonus': portal_rate.get('is_bonus_rate', False),
                'simplymiles_type': offer['offer_type'],
                'simplymiles_miles': stacked.simplymiles_miles,
                'simplymiles_min_spend': offer['min_spend'],
                'simplymiles_expires': offer['expires_at'],
                'simplymiles_expiring_soon': offer.get('expiring_soon', False),
                'cc_miles': stacked.cc_miles,
                'min_spend_required': stacked.min_spend,
                'total_miles': stacked.total_miles,
                'combined_yield': stacked.base_yield,
                'deal_score': stacked.deal_score,
            }

            opportunities.append(opportunity)

        except Exception as e:
            logger.warning(f"Error calculating stack for {offer['merchant_name']}: {e}")
            continue

    logger.info(f"Found {matched_count} merchant matches, {len(opportunities)} opportunities above min_yield")

    # Sort by deal score (highest first)
    opportunities.sort(key=lambda x: x['deal_score'], reverse=True)

    return opportunities


def store_opportunities(opportunities: List[Dict[str, Any]]) -> int:
    """
    Store computed opportunities in database.

    Args:
        opportunities: List of opportunity dictionaries

    Returns:
        Number of opportunities stored
    """
    if not opportunities:
        return 0

    db = get_database()
    computed_at = datetime.now().isoformat()

    # Clear old opportunities
    db.clear_stacked_opportunities()

    stored = 0
    for opp in opportunities:
        try:
            db.insert_stacked_opportunity(
                merchant_name=opp['merchant_name'],
                portal_rate=opp['portal_rate'],
                portal_miles=opp['portal_miles'],
                simplymiles_type=opp['simplymiles_type'],
                simplymiles_miles=opp['simplymiles_miles'],
                simplymiles_min_spend=opp['simplymiles_min_spend'],
                simplymiles_expires=opp['simplymiles_expires'],
                cc_miles=opp['cc_miles'],
                min_spend_required=opp['min_spend_required'],
                total_miles=opp['total_miles'],
                combined_yield=opp['combined_yield'],
                deal_score=opp['deal_score'],
                computed_at=computed_at
            )

            # Record discovery for "New This Week" tracking
            db.upsert_discovery(
                deal_type='stack',
                deal_identifier=opp['merchant_name'].lower(),
                yield_value=opp['deal_score']
            )

            stored += 1
        except Exception as e:
            logger.warning(f"Error storing opportunity: {e}")

    logger.info(f"Stored {stored} opportunities in database")
    return stored


def get_top_opportunities(
    limit: int = 20,
    deal_type: str = 'all'
) -> List[Dict[str, Any]]:
    """
    Get top opportunities from database.

    Args:
        limit: Maximum number to return
        deal_type: 'all', 'flat_bonus', or 'per_dollar'

    Returns:
        List of opportunity dictionaries
    """
    db = get_database()
    opportunities = db.get_top_stacked_opportunities(limit=limit * 2)  # Fetch extra for filtering

    if deal_type != 'all':
        opportunities = [o for o in opportunities if o['simplymiles_type'] == deal_type]

    return opportunities[:limit]


def get_expiring_soon_opportunities(hours: int = 48) -> List[Dict[str, Any]]:
    """
    Get opportunities that are expiring within specified hours.

    Args:
        hours: Number of hours until expiration

    Returns:
        List of expiring opportunities
    """
    from core.scorer import is_expiring_soon

    db = get_database()
    opportunities = db.get_top_stacked_opportunities(limit=100)

    expiring = [
        o for o in opportunities
        if o.get('simplymiles_expires') and is_expiring_soon(o['simplymiles_expires'], hours)
    ]

    return sorted(expiring, key=lambda x: x['simplymiles_expires'] or '')


def run_detection(store_results: bool = True) -> Dict[str, Any]:
    """
    Run full stack detection process.

    Args:
        store_results: If True, store results in database

    Returns:
        Dict with detection results
    """
    logger.info("Starting stack detection...")

    result = {
        'status': 'unknown',
        'total_opportunities': 0,
        'above_immediate_threshold': 0,
        'above_digest_threshold': 0,
        'expiring_soon': 0,
        'timestamp': datetime.now().isoformat()
    }

    try:
        settings = get_settings()

        # Detect opportunities
        opportunities = detect_stacked_opportunities(check_staleness=True)
        result['total_opportunities'] = len(opportunities)

        # Count by threshold
        for opp in opportunities:
            if opp['deal_score'] >= settings.thresholds.stack_immediate_alert:
                result['above_immediate_threshold'] += 1
            elif opp['deal_score'] >= settings.thresholds.stack_daily_digest:
                result['above_digest_threshold'] += 1

        # Count expiring soon
        from core.scorer import is_expiring_soon
        result['expiring_soon'] = sum(
            1 for o in opportunities
            if o.get('simplymiles_expires') and is_expiring_soon(o['simplymiles_expires'])
        )

        # Store results
        if store_results:
            store_opportunities(opportunities)

        result['status'] = 'success'

        logger.info(f"Detection complete: {result['total_opportunities']} opportunities found")
        logger.info(f"  - Above immediate threshold: {result['above_immediate_threshold']}")
        logger.info(f"  - Above digest threshold: {result['above_digest_threshold']}")
        logger.info(f"  - Expiring soon: {result['expiring_soon']}")

    except Exception as e:
        logger.error(f"Detection error: {e}")
        result['status'] = 'error'
        result['error'] = str(e)

    return result


if __name__ == "__main__":
    # Run detection when called directly
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    result = run_detection(store_results=True)

    if result['status'] != 'success':
        sys.exit(1)

