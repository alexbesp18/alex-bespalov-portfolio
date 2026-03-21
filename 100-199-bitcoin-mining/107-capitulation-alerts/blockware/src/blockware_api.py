"""
Blockware Solutions GraphQL API client.

Endpoint: https://marketplace.api.blockwaresolutions.com/api/opengraphql
Method: POST, Content-Type: application/json
Auth: None required for read queries (endpoint is named "opengraphql").
"""

import requests
from typing import List, Dict, Optional
from .config import GRAPHQL_URL, TARGET_MODELS, POLL_LIMIT, RANGE_WINDOW_DAYS
from .models import MinerOffer, TradeStats


def _gql(query: str, variables: dict = None) -> dict:
    """Execute a GraphQL query. Returns the 'data' dict or raises on error."""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    resp = requests.post(GRAPHQL_URL, json=payload, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    if result.get("errors"):
        raise Exception(f"GraphQL errors: {result['errors']}")
    return result["data"]


def fetch_bitcoin_stats() -> dict:
    """Get current BTC price and hashprice."""
    data = _gql("""
    {
        bitcoinStats {
            exchangeRate { btcToUsd }
            difficulty
            blockSubsidy
            hashprice { usd }
        }
    }
    """)
    stats = data["bitcoinStats"]
    return {
        "btc_price": stats["exchangeRate"]["btcToUsd"],
        "difficulty": stats["difficulty"],
        "hashprice_usd": float(stats["hashprice"]["usd"]),
    }


def _fetch_windowed_stats(model_id: int) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Fetch 90-day windowed high/low for a model. Returns (high, low, midpoint).
    Non-fatal: returns (None, None, None) on any failure.
    """
    try:
        data = _gql(f"""
        {{
            tradeStatsByModel(itemModelId: {model_id}, rangeLastNDays: {RANGE_WINDOW_DAYS}) {{
                tradeRangeMax {{ priceUsd }}
                tradeRangeMin {{ priceUsd }}
            }}
        }}
        """)
        s = data["tradeStatsByModel"]
        high = float(s["tradeRangeMax"]["priceUsd"]) if s.get("tradeRangeMax") else None
        low = float(s["tradeRangeMin"]["priceUsd"]) if s.get("tradeRangeMin") else None
        midpoint = (high + low) / 2 if high and low else None
        return high, low, midpoint
    except Exception:
        return None, None, None


def fetch_trade_stats(model_id: int) -> Optional[TradeStats]:
    """
    Get historical trade stats for a single model.
    Makes two calls: all-time stats + 90-day windowed stats.
    """
    try:
        data = _gql(f"""
        {{
            tradeStatsByModel(itemModelId: {model_id}) {{
                itemModelId
                tradeRangeMax {{ priceUsd }}
                tradeRangeMin {{ priceUsd }}
                lastTrade {{ priceUsd }}
                lowestOffer {{ priceUsd }}
                highestBid {{ priceUsd }}
            }}
        }}
        """)
        s = data["tradeStatsByModel"]

        # Second call: 90-day windowed stats (non-fatal)
        range_high, range_low, range_mid = _fetch_windowed_stats(model_id)

        return TradeStats(
            model_id=model_id,
            ath_price=float(s["tradeRangeMax"]["priceUsd"]) if s.get("tradeRangeMax") else None,
            atl_price=float(s["tradeRangeMin"]["priceUsd"]) if s.get("tradeRangeMin") else None,
            last_trade_price=float(s["lastTrade"]["priceUsd"]) if s.get("lastTrade") else None,
            current_lowest_offer=float(s["lowestOffer"]["priceUsd"]) if s.get("lowestOffer") else None,
            highest_bid=float(s["highestBid"]["priceUsd"]) if s.get("highestBid") else None,
            range_90d_high=range_high,
            range_90d_low=range_low,
            range_90d_midpoint=range_mid,
        )
    except Exception:
        return None


def fetch_all_trade_stats() -> Dict[int, TradeStats]:
    """Fetch trade stats for every target model. Returns dict keyed by model_id."""
    stats = {}
    for model_id in TARGET_MODELS:
        result = fetch_trade_stats(model_id)
        if result:
            stats[model_id] = result
    return stats


def fetch_current_offers() -> List[MinerOffer]:
    """
    Fetch ALL active offers for target new-gen models, sorted by $/TH ascending.
    Paginates through all results.
    """
    model_ids = list(TARGET_MODELS.keys())
    all_offers = []
    offset = 0

    while True:
        data = _gql("""
        query GetOffers($modelIds: [Int!], $first: Int!, $after: String!) {
            listOffersBundlesWithTotal(
                pagination: { first: $first, after: $after }
                filter: {
                    active: { eq: true }
                    itemModelId: { inside: $modelIds }
                }
                sorting: { field: "DOLLAR_PER_TH", order: "ASC" }
            ) {
                total
                results {
                    id
                    itemMasterName
                    itemMasterModel
                    itemMasterDescription
                    totalHashRateIdeal
                    totalHashRate24Hr
                    energyPrice
                    hostingSiteName
                    numHostingFee
                    monthlyEnergyCost
                    wattsPerTeraHash
                    offerCount
                    createdAt
                    pricePerTh { dollarPerTh btcPerTh }
                    dealScoreDetails {
                        dealScore
                        profitScore
                        capitalEfficiencyScore
                        breakEvenScore
                    }
                    aggregationDetails {
                        price { priceUsd priceBtc }
                        estimatedMonthlyRevenue { priceUsd }
                        estimatedMonthlyProfit { priceUsd }
                        hashRate24Hr
                        hashRateIdeal
                    }
                }
            }
        }
        """, variables={
            "modelIds": model_ids,
            "first": POLL_LIMIT,
            "after": str(offset),
        })

        result = data["listOffersBundlesWithTotal"]
        total = result["total"]

        for r in result["results"]:
            agg = r["aggregationDetails"]
            # Convert raw hashrate (H/s) to TH/s
            hashrate_ideal_th = r["totalHashRateIdeal"] / 1e12 if r["totalHashRateIdeal"] else 0
            hashrate_24hr_th = (r["totalHashRate24Hr"] or 0) / 1e12

            offer = MinerOffer(
                offer_id=r["id"],
                model_name=r["itemMasterName"],
                model_description=r["itemMasterDescription"],
                model_id_matched=_match_model_id(r["itemMasterDescription"]),
                price_usd=float(agg["price"]["priceUsd"]),
                price_btc=float(agg["price"]["priceBtc"]),
                dollar_per_th=r["pricePerTh"]["dollarPerTh"],
                deal_score=r["dealScoreDetails"]["dealScore"],
                hashrate_ideal_th=round(hashrate_ideal_th, 2),
                hashrate_24hr_th=round(hashrate_24hr_th, 2),
                watts_per_th=r["wattsPerTeraHash"],
                energy_price=r["energyPrice"],
                monthly_energy_cost=r.get("monthlyEnergyCost") or 0,
                est_monthly_revenue=float(agg["estimatedMonthlyRevenue"]["priceUsd"]),
                est_monthly_profit=float(agg["estimatedMonthlyProfit"]["priceUsd"]) if agg.get("estimatedMonthlyProfit") else 0,
                hosting_site=r["hostingSiteName"] or "Unknown",
                offer_count=r["offerCount"],
                created_at=r["createdAt"],
                link=f"https://marketplace.blockwaresolutions.com/detail/{r['id']}?Tab=offers",
            )
            all_offers.append(offer)

        offset += POLL_LIMIT
        if offset >= total:
            break

    return all_offers


def _match_model_id(description: str) -> Optional[int]:
    """Match an offer's description to our TARGET_MODELS dict."""
    if not description:
        return None
    for model_id, info in TARGET_MODELS.items():
        if info["name"].lower() == description.lower():
            return model_id
    # Fuzzy fallback: check if description contains the model name
    for model_id, info in TARGET_MODELS.items():
        if info["name"].lower() in description.lower() or description.lower() in info["name"].lower():
            return model_id
    return None
