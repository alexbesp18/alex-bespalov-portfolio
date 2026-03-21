"""
Daily digest entry point. Called by GitHub Actions once per day.
Sends a Telegram message with the top 5 cheapest offers by $/TH.
"""

import sys
from .blockware_api import fetch_bitcoin_stats, fetch_all_trade_stats, fetch_current_offers
from .alert_engine import find_top_deals
from .telegram_bot import send_daily_digest


def main():
    print("=" * 60)
    print("Blockware Daily Digest - Starting run")
    print("=" * 60)

    try:
        # 1. Get BTC context
        print("[1/3] Fetching Bitcoin stats...")
        btc_stats = fetch_bitcoin_stats()
        btc_price = btc_stats["btc_price"]
        hashprice = btc_stats["hashprice_usd"]
        print(f"  BTC: ${btc_price:,.2f} | Hashprice: ${hashprice}/PH/day")

        # 2. Get trade stats for all models
        print("[2/3] Fetching trade stats for all target models...")
        trade_stats = fetch_all_trade_stats()
        print(f"  Got stats for {len(trade_stats)} models")

        # 3. Get all current offers
        print("[3/3] Fetching current offers...")
        offers = fetch_current_offers()
        total_count = len(offers)
        print(f"  Found {total_count} active new-gen offers")

        # Find top deals by $/TH
        deals = find_top_deals(offers, trade_stats, btc_price, hashprice)
        print(f"  Top deals found: {len(deals)}")

        # Send digest
        send_daily_digest(deals, btc_price, hashprice, total_count)

    except Exception as e:
        print(f"Digest failed (non-fatal): {e}")
        # Exit 0 — digest is non-critical, don't fail the workflow

    print("Done.")


if __name__ == "__main__":
    main()
