"""Pipeline: load watchlist -> fetch prices -> compute drawdown -> alert -> persist."""

import logging
from collections import defaultdict
from datetime import date, timedelta

import requests

from config import Settings
from fetcher import fetch_chain_for_expiration, fetch_strikes_from_chain
from models import WatchlistItem

logger = logging.getLogger(__name__)

ALERT_THRESHOLDS = [20, 40, 60]
RESET_THRESHOLDS = {20: -10, 40: -25, 60: -45}  # recover to X% before re-arming


def _get_client(settings: Settings):
    from supabase import create_client

    return create_client(settings.supabase_url, settings.supabase_service_key)


def load_watchlist(settings: Settings) -> list[WatchlistItem]:
    client = _get_client(settings)
    rows = (
        client.schema("options_tracker")
        .table("watchlist")
        .select("*")
        .eq("is_active", True)
        .execute()
        .data
    )
    return [WatchlistItem(**r) for r in rows]


def deactivate_expired(settings: Settings, today: date) -> int:
    """Deactivate contracts past expiration before fetching."""
    client = _get_client(settings)
    result = (
        client.schema("options_tracker")
        .table("watchlist")
        .update({"is_active": False, "updated_at": "now()"})
        .lt("expiration", today.isoformat())
        .eq("is_active", True)
        .execute()
    )
    count = len(result.data) if result.data else 0
    if count:
        logger.info("Deactivated %d expired contracts", count)
    return count


def fetch_rolling_peaks(settings: Settings, ids: list[int], today: date) -> dict[int, float]:
    """Batch-fetch 30-day rolling peak for all contracts."""
    client = _get_client(settings)
    cutoff = (today - timedelta(days=30)).isoformat()
    try:
        rows = (
            client.schema("options_tracker")
            .rpc("rolling_peaks", {"p_cutoff": cutoff, "p_ids": ids})
            .execute()
            .data
        )
        return {int(r["watchlist_id"]): float(r["peak_30d"]) for r in rows} if rows else {}
    except Exception as e:
        logger.warning("Failed to fetch rolling peaks: %s", e)
        return {}


def fetch_previous_data(settings: Settings, ids: list[int], today: date) -> dict[int, tuple[float, float]]:
    """Batch-fetch previous day's spot and mid for all contracts."""
    client = _get_client(settings)
    try:
        rows = (
            client.schema("options_tracker")
            .rpc("previous_spots", {"p_today": today.isoformat(), "p_ids": ids})
            .execute()
            .data
        )
        return {
            int(r["watchlist_id"]): (float(r["prev_spot"]), float(r["prev_mid"]))
            for r in rows
        } if rows else {}
    except Exception as e:
        logger.warning("Failed to fetch previous data: %s", e)
        return {}


def send_telegram_alert(
    settings: Settings, item: WatchlistItem, mid: float, drawdown: float,
    threshold: int, source: str, spot: float, prev_spot: float | None,
):
    if not settings.has_telegram:
        logger.warning("Telegram not configured, skipping alert")
        return
    spot_ctx = ""
    if prev_spot and prev_spot > 0:
        spot_chg = ((spot - prev_spot) / prev_spot) * 100
        spot_ctx = f"\n{item.ticker} spot: ${spot:.2f} ({spot_chg:+.1f}% vs prev close)"
    text = (
        f"🔴 LEAPS DRAWDOWN ALERT\n\n"
        f"{item.label} (${item.strike} call, exp {item.expiration})\n"
        f"Mid: ${mid:.2f} | Drawdown: {drawdown:.1f}% from {source}\n"
        f"Threshold: -{threshold}% crossed"
        f"{spot_ctx}"
    )
    try:
        requests.post(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
            data={"chat_id": settings.telegram_chat_id, "text": text},
            timeout=10,
        )
        logger.info("Sent Telegram alert for %s at -%d%% (%s)", item.label, threshold, source)
    except Exception as e:
        logger.error("Failed to send Telegram alert: %s", e)


def log_alert(settings: Settings, wl_id: int, today: date, threshold: int, dd: float, mid: float, peak: float, source: str):
    client = _get_client(settings)
    try:
        client.schema("options_tracker").table("alert_log").insert({
            "watchlist_id": wl_id, "alert_date": today.isoformat(),
            "threshold": threshold, "drawdown_pct": round(dd, 4),
            "mid_price": round(mid, 4), "peak_ref": round(peak, 4), "source": source,
        }).execute()
    except Exception as e:
        logger.error("Failed to log alert: %s", e)


def run_snapshot(settings: Settings) -> int:
    """Run daily snapshot. Returns number of prices persisted."""
    client = _get_client(settings)
    today = date.today()

    # Step 0: deactivate expired contracts
    deactivate_expired(settings, today)

    # Step 1: load active watchlist
    watchlist = load_watchlist(settings)
    if not watchlist:
        logger.warning("Watchlist is empty")
        return 0

    # Step 2: batch-fetch rolling peaks + previous data
    ids = [item.id for item in watchlist]
    rolling_map = fetch_rolling_peaks(settings, ids, today)
    prev_map = fetch_previous_data(settings, ids, today)

    # Step 3: group by (ticker, expiration) to minimize API calls
    groups: dict[tuple[str, str], list[WatchlistItem]] = defaultdict(list)
    for item in watchlist:
        groups[(item.ticker, item.expiration.isoformat())].append(item)

    persisted = 0
    summary_data = []  # Collect for daily Telegram summary
    alerts_fired = 0

    for (ticker, exp_str), items in groups.items():
        logger.info("Fetching %s %s (%d strikes)...", ticker, exp_str, len(items))

        try:
            spot, calls_df = fetch_chain_for_expiration(
                ticker, exp_str, delay=settings.fetch_delay_seconds
            )
        except Exception as e:
            logger.error("Failed to fetch %s %s: %s", ticker, exp_str, e)
            continue

        wanted = {float(item.strike) for item in items}
        filtered = fetch_strikes_from_chain(calls_df, wanted)

        for item in items:
            rows = filtered[filtered["strike"] == float(item.strike)]
            if rows.empty:
                logger.warning("No data for %s strike=%s", ticker, item.strike)
                continue

            row = rows.iloc[0]
            bid = float(row.get("bid") or 0)
            ask = float(row.get("ask") or 0)
            iv = float(row.get("impliedVolatility") or 0)

            if bid == 0 and ask == 0:
                logger.warning("Zero bid/ask for %s, skipping", item.label)
                continue

            mid = (bid + ask) / 2
            ath_peak = float(item.peak_mid)

            # Compute ATH drawdown FIRST (before updating peak)
            ath_dd = ((mid - ath_peak) / ath_peak * 100) if ath_peak > 0 else 0.0

            # Then update ATH peak if new high
            if mid > ath_peak:
                ath_peak = mid
                ath_dd = 0.0  # At new ATH, no drawdown
                client.schema("options_tracker").table("watchlist").update(
                    {"peak_mid": mid, "peak_mid_date": today.isoformat(), "updated_at": "now()"}
                ).eq("id", item.id).execute()
            peak_30d = rolling_map.get(item.id, mid)
            rolling_dd = ((mid - peak_30d) / peak_30d * 100) if peak_30d > 0 else 0.0
            effective_dd = min(ath_dd, rolling_dd)
            worst_source = "30d" if rolling_dd < ath_dd else "ATH"
            peak_ref = peak_30d if worst_source == "30d" else ath_peak

            # Get previous spot for alert context
            prev_spot = prev_map.get(item.id, (None, None))[0]

            # Check alert thresholds (ordinal, dual drawdown)
            for threshold in ALERT_THRESHOLDS:
                if effective_dd <= -threshold and item.last_alert_level < threshold:
                    send_telegram_alert(settings, item, mid, effective_dd, threshold, worst_source, spot, prev_spot)
                    log_alert(settings, item.id, today, threshold, effective_dd, mid, peak_ref, worst_source)
                    client.schema("options_tracker").table("watchlist").update(
                        {"last_alert_level": threshold, "updated_at": "now()"}
                    ).eq("id", item.id).execute()
                    item.last_alert_level = threshold
                    alerts_fired += 1

            # Graduated reset (prevents bounce spam)
            if item.last_alert_level > 0:
                reset_at = RESET_THRESHOLDS.get(item.last_alert_level, -10)
                if effective_dd > reset_at:
                    client.schema("options_tracker").table("watchlist").update(
                        {"last_alert_level": 0, "updated_at": "now()"}
                    ).eq("id", item.id).execute()

            # Persist daily price
            price_row = {
                "watchlist_id": item.id,
                "snapshot_date": today.isoformat(),
                "spot_price": spot,
                "bid": bid,
                "ask": ask,
                "mid_price": round(mid, 4),
                "implied_vol": round(iv, 6) if iv else None,
                "drawdown_pct": round(ath_dd, 4),
            }
            try:
                client.schema("options_tracker").table("daily_prices").upsert(
                    price_row, on_conflict="watchlist_id,snapshot_date"
                ).execute()
                persisted += 1
                logger.info(
                    "  %s: mid=$%.2f ath_dd=%.1f%% 30d_dd=%.1f%%",
                    item.label, mid, ath_dd, rolling_dd,
                )
            except Exception as e:
                logger.error("Failed to persist %s: %s", item.label, e)

            # Collect for daily summary
            prev_mid_val = prev_map.get(item.id, (None, None))[1]
            mid_chg = mid - prev_mid_val if prev_mid_val else None
            summary_data.append({
                "label": item.label or f"{ticker} ${item.strike}",
                "mid": mid, "ath_dd": ath_dd, "rolling_dd": rolling_dd,
                "mid_chg": mid_chg, "spot": spot, "prev_spot": prev_spot,
            })

    # Send daily Telegram summary
    if summary_data:
        send_daily_summary(settings, today, summary_data, alerts_fired)

    return persisted


def _heat_dot(dd: float) -> str:
    if dd > -10:
        return "\U0001f7e2"  # green
    if dd > -20:
        return "\U0001f7e1"  # yellow
    if dd > -40:
        return "\U0001f7e0"  # orange
    return "\U0001f534"  # red


def send_daily_summary(settings: Settings, today: date, data: list[dict], alerts_fired: int):
    if not settings.has_telegram:
        return

    # Heat summary
    dots = [_heat_dot(min(d["ath_dd"], d["rolling_dd"])) for d in data]
    from collections import Counter
    counts = Counter(dots)
    heat_line = " ".join(f"{v}x{k}" for k, v in counts.most_common())

    # Split ATM / OTM
    atm = [d for d in data if "ATM" in d["label"]]
    otm = [d for d in data if "OTM" in d["label"]]

    lines = [f"LEAPS Daily Report — {today.strftime('%b %d, %Y')}", "", f"Heat: {heat_line}", ""]

    for section_name, section in [("ATM", atm), ("OTM", otm)]:
        if not section:
            continue
        lines.append(f"── {section_name} ──")
        for d in section:
            dot = _heat_dot(min(d["ath_dd"], d["rolling_dd"]))
            mc = d["mid_chg"]
            if mc is not None:
                sign = "+" if mc >= 0 else ""
                chg_str = f"  {sign}${mc:.2f} d/d"
            else:
                chg_str = "  -- d/d"
            spot_chg = ""
            if d["prev_spot"] and d["prev_spot"] > 0:
                pct = ((d["spot"] - d["prev_spot"]) / d["prev_spot"]) * 100
                spot_str = f"${d['spot']:.2f}"
                spot_chg = f"  Spot: {spot_str} ({pct:+.1f}%)"
            label = d["label"]
            mid = d["mid"]
            ath = d["ath_dd"]
            r30 = d["rolling_dd"]
            lines.append(f"{dot} {label}")
            lines.append(f"   Mid: ${mid:.2f}{chg_str}  ATH: {ath:.1f}%  30d: {r30:.1f}%")
            if spot_chg:
                lines.append(spot_chg)
        lines.append("")

    if alerts_fired:
        lines.append(f"{alerts_fired} alert(s) triggered today")
    else:
        lines.append("No alerts triggered today")

    text = "\n".join(lines)
    try:
        requests.post(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
            data={"chat_id": settings.telegram_chat_id, "text": text},
            timeout=10,
        )
        logger.info("Sent daily summary to Telegram")
    except Exception as e:
        logger.error("Failed to send daily summary: %s", e)
