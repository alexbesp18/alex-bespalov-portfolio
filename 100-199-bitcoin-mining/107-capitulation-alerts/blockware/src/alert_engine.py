"""
Core alert logic — multi-benchmark with quality filters:
1. Quality gate: skip offers with watts_per_th > 17.5 or deal_score < 50
2. Primary trigger: >= 60% off last_trade_price
3. Fallback trigger: >= 60% off range_90d_midpoint (if no last trade)
4. No data: skip (no reliable benchmark)
5. All 3 discount percentages computed for context in the alert message.
"""

import json
import os
from typing import List, Dict, Optional
from .models import MinerOffer, TradeStats, Alert
from .config import TARGET_MODELS, DISCOUNT_THRESHOLD, SENT_ALERTS_PATH, MAX_EFFICIENCY_WTH, MIN_DEAL_SCORE


def load_sent_alerts() -> set:
    """Load previously alerted offer IDs from JSON file."""
    if os.path.exists(SENT_ALERTS_PATH):
        with open(SENT_ALERTS_PATH, "r") as f:
            data = json.load(f)
            return set(data.get("sent_ids", []))
    return set()


def save_sent_alerts(sent_ids: set):
    """Persist alerted offer IDs to JSON file."""
    os.makedirs(os.path.dirname(SENT_ALERTS_PATH), exist_ok=True)
    # Keep only the last 2000 IDs to prevent unbounded growth
    trimmed = sorted(sent_ids)[-2000:]
    with open(SENT_ALERTS_PATH, "w") as f:
        json.dump({"sent_ids": trimmed}, f)


def _discount_pct(price: float, benchmark: Optional[float]) -> Optional[float]:
    """Compute discount percentage. Returns None if benchmark is missing or invalid."""
    if benchmark is None or benchmark <= 0:
        return None
    return round((1 - price / benchmark) * 100, 1)


def _get_ath(model_id: Optional[int], trade_stats: Dict[int, TradeStats]) -> Optional[float]:
    """Get ATH price: prefer API, fall back to static config."""
    if model_id and model_id in trade_stats:
        api_ath = trade_stats[model_id].ath_price
        if api_ath and api_ath > 0:
            return api_ath
    if model_id and model_id in TARGET_MODELS:
        return TARGET_MODELS[model_id].get("static_ath")
    return None


def find_capitulation_deals(
    offers: List[MinerOffer],
    trade_stats: Dict[int, TradeStats],
    btc_price: float,
    hashprice_usd: float,
) -> List[Alert]:
    """
    Scan all offers and return those meeting quality gates + discount threshold.
    Quality gates: watts_per_th <= 17.5 and deal_score >= 50.
    Primary trigger: >= DISCOUNT_THRESHOLD% off last trade.
    Fallback trigger: >= DISCOUNT_THRESHOLD% off 90d midpoint.
    No benchmark data: skip.
    """
    sent_ids = load_sent_alerts()
    alerts = []

    for offer in offers:
        if offer.offer_id in sent_ids:
            continue

        # Quality gate 1: efficiency
        if offer.watts_per_th > MAX_EFFICIENCY_WTH:
            continue

        # Quality gate 2: deal score
        if offer.deal_score < MIN_DEAL_SCORE:
            continue

        per_unit_price = offer.price_usd / max(offer.offer_count, 1)

        # Resolve stats for this model
        stats = trade_stats.get(offer.model_id_matched) if offer.model_id_matched else None

        last_trade = stats.last_trade_price if stats else None
        midpoint_90d = stats.range_90d_midpoint if stats else None
        ath = _get_ath(offer.model_id_matched, trade_stats)

        # Compute all discounts for context
        disc_last = _discount_pct(per_unit_price, last_trade)
        disc_ath = _discount_pct(per_unit_price, ath)
        disc_mid = _discount_pct(per_unit_price, midpoint_90d)

        # Trigger decision: last trade first, then 90d midpoint fallback
        triggered = False
        if disc_last is not None and disc_last >= DISCOUNT_THRESHOLD:
            triggered = True
        elif disc_last is None and disc_mid is not None and disc_mid >= DISCOUNT_THRESHOLD:
            triggered = True

        if not triggered:
            continue

        alerts.append(Alert(
            offer=offer,
            btc_price=btc_price,
            hashprice_usd=hashprice_usd,
            last_trade_price=last_trade,
            discount_vs_last_trade=disc_last,
            ath_price=ath,
            discount_vs_ath=disc_ath,
            range_90d_midpoint=midpoint_90d,
            discount_vs_90d_mid=disc_mid,
        ))

    return alerts


def find_top_deals(
    offers: List[MinerOffer],
    trade_stats: Dict[int, TradeStats],
    btc_price: float,
    hashprice_usd: float,
    top_n: int = 5,
) -> List[Alert]:
    """
    Return the top N cheapest offers by $/TH for the daily digest.
    Applies quality gates but NO discount threshold and NO sent_alerts dedup.
    """
    qualified = []

    for offer in offers:
        if offer.watts_per_th > MAX_EFFICIENCY_WTH:
            continue
        if offer.deal_score < MIN_DEAL_SCORE:
            continue

        per_unit_price = offer.price_usd / max(offer.offer_count, 1)
        stats = trade_stats.get(offer.model_id_matched) if offer.model_id_matched else None

        last_trade = stats.last_trade_price if stats else None
        midpoint_90d = stats.range_90d_midpoint if stats else None
        ath = _get_ath(offer.model_id_matched, trade_stats)

        disc_last = _discount_pct(per_unit_price, last_trade)
        disc_ath = _discount_pct(per_unit_price, ath)
        disc_mid = _discount_pct(per_unit_price, midpoint_90d)

        qualified.append(Alert(
            offer=offer,
            btc_price=btc_price,
            hashprice_usd=hashprice_usd,
            last_trade_price=last_trade,
            discount_vs_last_trade=disc_last,
            ath_price=ath,
            discount_vs_ath=disc_ath,
            range_90d_midpoint=midpoint_90d,
            discount_vs_90d_mid=disc_mid,
        ))

    # Sort by $/TH ascending
    qualified.sort(key=lambda a: a.offer.dollar_per_th)
    return qualified[:top_n]


def mark_alerts_sent(alerts: List[Alert]):
    """Add alerted offer IDs to the sent set and save."""
    sent_ids = load_sent_alerts()
    for alert in alerts:
        sent_ids.add(alert.offer.offer_id)
    save_sent_alerts(sent_ids)
