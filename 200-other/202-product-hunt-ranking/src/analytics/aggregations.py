"""Category trend aggregation for analytics."""

import logging
from collections import defaultdict
from datetime import date
from typing import Any

from supabase import Client

from src.db.models import EnrichedProduct

logger = logging.getLogger(__name__)


def aggregate_category_trends(
    products: list[EnrichedProduct],
    week_date: date,
    client: Client,
) -> dict[str, dict[str, Any]]:
    """
    Aggregate products by category and save to category_trends table.

    Args:
        products: List of enriched products for the week
        week_date: The week date
        client: Supabase client

    Returns:
        Dict of category -> stats
    """
    if not products:
        logger.warning("No products to aggregate")
        return {}

    # Group by category
    by_category: dict[str, list[EnrichedProduct]] = defaultdict(list)
    for p in products:
        cat = p.category or "Uncategorized"
        by_category[cat].append(p)

    trends = {}
    rows_to_upsert = []

    for category, prods in by_category.items():
        # Calculate stats
        upvotes = [p.upvotes for p in prods]
        innovation = [p.innovation_score for p in prods if p.innovation_score]
        market_fit = [p.market_fit_score for p in prods if p.market_fit_score]

        # Find top product
        top_product = max(prods, key=lambda x: x.upvotes)

        stats = {
            "week_date": week_date.isoformat(),
            "category": category,
            "product_count": len(prods),
            "avg_upvotes": sum(upvotes) / len(upvotes) if upvotes else 0,
            "avg_innovation_score": sum(innovation) / len(innovation) if innovation else None,
            "avg_market_fit_score": sum(market_fit) / len(market_fit) if market_fit else None,
            "top_product": top_product.name,
            "top_product_upvotes": top_product.upvotes,
        }

        trends[category] = stats
        rows_to_upsert.append(stats)

    # Save to Supabase
    if rows_to_upsert:
        try:
            client.schema("product_hunt").table("category_trends").upsert(
                rows_to_upsert, on_conflict="week_date,category"  # type: ignore[arg-type]
            ).execute()
            logger.info(f"Saved {len(rows_to_upsert)} category trends for {week_date}")
        except Exception as e:
            logger.error(f"Failed to save category trends: {e}")

    return trends


def get_solo_builder_pick(products: list[EnrichedProduct]) -> EnrichedProduct | None:
    """
    Find the best product for a solo builder: solo_friendly + high traction + buildable.

    Args:
        products: List of enriched products

    Returns:
        The best solo builder pick, or None
    """
    candidates = []

    for p in products:
        if not p.maker_info:
            continue

        solo_friendly = p.maker_info.get("solo_friendly", False)
        build_complexity = p.maker_info.get("build_complexity", "year")

        # Must be solo-friendly and buildable in reasonable time
        if solo_friendly and build_complexity in ["weekend", "month"]:
            # Score by upvotes (traction) + innovation
            score: float = float(p.upvotes)
            if p.innovation_score:
                score += p.innovation_score * 20  # Boost innovative ideas
            candidates.append((p, score))

    if not candidates:
        # Fallback: just return highest upvoted product that's not too complex
        for p in products:
            if p.maker_info and p.maker_info.get("build_complexity") in ["weekend", "month"]:
                candidates.append((p, p.upvotes))

    if candidates:
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    return None
