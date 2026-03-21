"""
Telegram notification sender.
Uses the Telegram Bot API directly via requests (no library dependency).
"""

import os
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def _fmt_discount_line(label: str, pct: float | None, benchmark: float | None, primary: bool = False) -> str:
    """Format a single discount benchmark line."""
    prefix = "\u27a4 " if primary else "   "
    if pct is not None and benchmark is not None:
        return f"{prefix}{pct:.0f}% off {label} (${benchmark:,.0f})"
    return f"{prefix}{label}: no data"


def format_alert(alert) -> str:
    """Format an Alert into a Telegram message with HTML formatting."""
    o = alert.offer
    unit_price = o.price_usd / max(o.offer_count, 1)
    units_str = f" ({o.offer_count} units)" if o.offer_count > 1 else ""

    # ROI calculation: months to break even
    if o.est_monthly_profit and o.est_monthly_profit > 0:
        months_to_roi = unit_price / o.est_monthly_profit
        roi_str = f"{months_to_roi:.1f} months"
    else:
        roi_str = "N/A (negative profit)"

    # Build discount lines
    disc_lines = []
    disc_lines.append(_fmt_discount_line(
        "Last Trade", alert.discount_vs_last_trade, alert.last_trade_price, primary=True))
    disc_lines.append(_fmt_discount_line(
        "ATH", alert.discount_vs_ath, alert.ath_price))
    disc_lines.append(_fmt_discount_line(
        "90d Avg", alert.discount_vs_90d_mid, alert.range_90d_midpoint))
    discounts_block = "\n".join(disc_lines)

    msg = (
        f"\U0001f6a8\U0001f6a8\U0001f6a8 <b>CAPITULATION ALERT</b> \U0001f6a8\U0001f6a8\U0001f6a8\n"
        f"\n"
        f"<b>{o.model_description}</b>{units_str}\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"\U0001f4b0 <b>${unit_price:,.0f}</b>\n"
        f"\n"
        f"<b>Discounts:</b>\n"
        f"{discounts_block}\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"\U0001f4ca ${o.dollar_per_th:.2f}/TH  |  Deal Score: {o.deal_score}/100\n"
        f"\u26cf Hashrate: {o.hashrate_ideal_th:.0f} TH/s (24h: {o.hashrate_24hr_th:.0f} TH/s)\n"
        f"\u26a1 Efficiency: {o.watts_per_th:.1f} W/TH  |  Energy: ${o.energy_price:.3f}/kWh\n"
        f"\U0001f4cd Location: {o.hosting_site}\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"\U0001f4b5 Est. Monthly Revenue: ${o.est_monthly_revenue:,.2f}\n"
        f"\U0001f4b5 Est. Monthly Profit: ${o.est_monthly_profit:,.2f}\n"
        f"\U0001f4b5 Est. Monthly Energy Cost: ${o.monthly_energy_cost:,.2f}\n"
        f"\u23f1 Breakeven: {roi_str}\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"\u20bf BTC: ${alert.btc_price:,.0f}  |  Hashprice: ${alert.hashprice_usd}/PH/day\n"
        f"\n"
        f'\U0001f517 <a href="{o.link}">BUY NOW ON BLOCKWARE</a>'
    )
    return msg


def _primary_discount(alert) -> str:
    """Short string describing the primary discount for dry-run / log output."""
    if alert.discount_vs_last_trade is not None:
        return f"{alert.discount_vs_last_trade:.0f}% off last trade"
    if alert.discount_vs_90d_mid is not None:
        return f"{alert.discount_vs_90d_mid:.0f}% off 90d avg"
    return "discount unknown"


def send_alert(alert) -> bool:
    """Send a single alert to Telegram. Returns True on success."""
    if not BOT_TOKEN or not CHAT_ID:
        print(f"[DRY RUN] Would send alert for offer #{alert.offer.offer_id}: "
              f"{alert.offer.model_description} @ ${alert.offer.price_usd:,.0f} "
              f"({_primary_discount(alert)})")
        return True

    msg = format_alert(alert)
    resp = requests.post(f"{TELEGRAM_API}/sendMessage", json={
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }, timeout=10)

    if resp.status_code == 200:
        return True
    else:
        print(f"Telegram error {resp.status_code}: {resp.text}")
        return False


def send_summary(total_offers: int, btc_price: float, alerts_sent: int):
    """Optional: send a heartbeat summary (call this only once per hour or so)."""
    # Only log, don't spam Telegram with heartbeats
    print(f"[Summary] Scanned {total_offers} offers | BTC ${btc_price:,.0f} | "
          f"Alerts sent this run: {alerts_sent}")


def format_daily_digest(deals, btc_price: float, hashprice: float, total_offers: int) -> str:
    """Format a daily digest message with top deals by $/TH."""
    from datetime import datetime, timezone, timedelta
    ct = datetime.now(timezone(timedelta(hours=-5)))
    date_str = ct.strftime("%b %-d, %Y")

    count = len(deals)
    footer_label = f"Top {count}" if count < 5 else "Top 5"
    if count == total_offers:
        footer_label = f"All {count}"

    lines = [
        f"\U0001f4cb <b>Daily Digest</b> \u2014 {date_str}",
        f"<i>via Blockware</i>",
        f"",
        f"\u26a1 ${hashprice:.2f}/PH/day | {total_offers} offers | BTC ${btc_price:,.0f}",
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501",
    ]

    for i, deal in enumerate(deals, 1):
        o = deal.offer
        unit_price = o.price_usd / max(o.offer_count, 1)

        # Discount line
        if deal.discount_vs_last_trade is not None:
            pct = deal.discount_vs_last_trade
            bench = deal.last_trade_price
            label = "last"
        elif deal.discount_vs_90d_mid is not None:
            pct = deal.discount_vs_90d_mid
            bench = deal.range_90d_midpoint
            label = "90d"
        else:
            pct = None
            bench = None
            label = ""

        if pct is not None and bench is not None:
            if pct > 0:
                disc_str = f"-{pct:.0f}% {label} ${bench:,.0f}"
            else:
                disc_str = f"+{abs(pct):.0f}% above {label} ${bench:,.0f}"
        else:
            disc_str = "no trade data"

        # ROI
        if o.est_monthly_profit and o.est_monthly_profit > 0:
            months_roi = unit_price / o.est_monthly_profit
            roi_str = f"ROI {months_roi:.1f}mo"
        else:
            roi_str = "ROI N/A"

        lines.append(f"")
        lines.append(f"<b>{i}.</b> <b>{o.model_description}</b> \u2014 <b>${unit_price:,.0f}</b> (${o.dollar_per_th:.2f}/TH)")
        lines.append(f"   {disc_str} | Profit ${o.est_monthly_profit:,.0f}/mo | {roi_str}")
        lines.append(f"   Score {int(o.deal_score)} | \U0001f4cd {o.hosting_site} | <a href=\"{o.link}\">View deal</a>")

    lines.append(f"")
    lines.append(f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501")
    lines.append(f"<i>{footer_label} by $/TH (new-gen, \u226417.5 W/TH, score \u226550).\n60%+ off capitulation alerts sent separately.</i>")

    return "\n".join(lines)


def send_daily_digest(deals, btc_price: float, hashprice: float, total_offers: int) -> bool:
    """Send the daily digest to Telegram. Returns True on success."""
    if not deals:
        print("[Digest] No qualified offers. Skipping digest.")
        return False

    msg = format_daily_digest(deals, btc_price, hashprice, total_offers)

    if not BOT_TOKEN or not CHAT_ID:
        print(f"[DRY RUN] Daily digest ({len(deals)} deals):")
        print(msg)
        return True

    resp = requests.post(f"{TELEGRAM_API}/sendMessage", json={
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }, timeout=10)

    if resp.status_code == 200:
        print(f"[Digest] Sent daily digest with {len(deals)} deals.")
        return True
    else:
        print(f"[Digest] Telegram error {resp.status_code}: {resp.text}")
        return False
