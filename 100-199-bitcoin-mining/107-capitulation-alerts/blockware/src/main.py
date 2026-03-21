"""
Main entry point. Called by GitHub Actions every 10 minutes.
"""

import sys
from .blockware_api import fetch_bitcoin_stats, fetch_all_trade_stats, fetch_current_offers
from .alert_engine import find_capitulation_deals, mark_alerts_sent
from .telegram_bot import send_alert, send_summary


def main():
    print("=" * 60)
    print("Blockware Capitulation Alert Bot - Starting run")
    print("=" * 60)

    # 1. Get BTC context
    print("[1/4] Fetching Bitcoin stats...")
    try:
        btc_stats = fetch_bitcoin_stats()
    except Exception as e:
        print(f"ERROR fetching BTC stats: {e}")
        sys.exit(1)

    btc_price = btc_stats["btc_price"]
    hashprice = btc_stats["hashprice_usd"]
    print(f"  BTC: ${btc_price:,.2f} | Hashprice: ${hashprice}/PH/day | "
          f"Difficulty: {btc_stats['difficulty']:,}")

    # 2. Get trade stats (ATH + last trade + 90d window) for all models
    print("[2/4] Fetching trade stats for all target models...")
    trade_stats = fetch_all_trade_stats()
    print(f"  Got stats for {len(trade_stats)} models")

    # 3. Get all current offers
    print("[3/4] Fetching current offers...")
    try:
        offers = fetch_current_offers()
    except Exception as e:
        print(f"ERROR fetching offers: {e}")
        sys.exit(1)

    print(f"  Found {len(offers)} active new-gen offers")

    # 4. Find capitulation deals (60%+ off, quality-filtered)
    print("[4/4] Scanning for 60%+ off deals (efficiency <=17.5 W/TH, score >=50)...")
    alerts = find_capitulation_deals(offers, trade_stats, btc_price, hashprice)

    if not alerts:
        print("  No capitulation deals found this run.")
    else:
        print(f"  FOUND {len(alerts)} CAPITULATION DEAL(S)!")
        sent_alerts = []
        for alert in alerts:
            o = alert.offer
            unit_price = o.price_usd / max(o.offer_count, 1)
            # Show primary discount in console
            if alert.discount_vs_last_trade is not None:
                disc_str = f"{alert.discount_vs_last_trade:.0f}% off last trade ${alert.last_trade_price:,.0f}"
            elif alert.discount_vs_90d_mid is not None:
                disc_str = f"{alert.discount_vs_90d_mid:.0f}% off 90d avg ${alert.range_90d_midpoint:,.0f}"
            else:
                disc_str = "discount unknown"
            print(f"  -> {o.model_description} @ ${unit_price:,.0f} "
                  f"({disc_str}) "
                  f"${o.dollar_per_th:.2f}/TH | Score: {o.deal_score}")
            if send_alert(alert):
                sent_alerts.append(alert)

        # Only mark alerts that were actually delivered to Telegram
        if sent_alerts:
            mark_alerts_sent(sent_alerts)
        print(f"  Sent {len(sent_alerts)}/{len(alerts)} alerts to Telegram")

    send_summary(len(offers), btc_price, len(alerts))
    print("Done.")


if __name__ == "__main__":
    main()
