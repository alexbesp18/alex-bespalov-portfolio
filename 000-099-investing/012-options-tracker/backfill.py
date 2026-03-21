"""Backfill historical prices from yfinance OHLC for existing watchlist contracts.

Uses Close price as mid-price proxy (no bid/ask available historically).
Usage: python backfill.py
"""

import logging
import time
from datetime import date

import yfinance as yf

from config import get_settings
from models import WatchlistItem

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def occ_symbol(ticker: str, expiration: date, strike: float, option_type: str = "call") -> str:
    """Build OCC option symbol: NVDA270617C00205000"""
    flag = "C" if option_type == "call" else "P"
    strike_int = int(strike * 1000)
    return f"{ticker}{expiration.strftime('%y%m%d')}{flag}{strike_int:08d}"


def backfill():
    settings = get_settings()
    if not settings.has_supabase:
        logger.error("Supabase not configured")
        return

    from supabase import create_client

    client = create_client(settings.supabase_url, settings.supabase_service_key)

    # Load watchlist
    rows = client.schema("options_tracker").table("watchlist").select("*").eq("is_active", True).execute().data
    items = [WatchlistItem(**r) for r in rows]
    logger.info("Backfilling %d contracts", len(items))

    total = 0
    for item in items:
        symbol = occ_symbol(item.ticker, item.expiration, float(item.strike))
        logger.info("  %s → %s", item.label, symbol)

        try:
            hist = yf.Ticker(symbol).history(period="max")
        except Exception as e:
            logger.warning("    Failed to fetch history: %s", e)
            time.sleep(2)
            continue

        if hist.empty:
            logger.warning("    No historical data")
            time.sleep(2)
            continue

        # Also get spot price history for the underlying
        try:
            spot_hist = yf.Ticker(item.ticker).history(period="6mo")
        except Exception:
            spot_hist = None

        for idx, row in hist.iterrows():
            snap_date = idx.strftime("%Y-%m-%d")
            close = float(row["Close"])
            if close <= 0:
                continue

            spot = 0.0
            if spot_hist is not None and idx in spot_hist.index:
                spot = float(spot_hist.loc[idx, "Close"])

            price_row = {
                "watchlist_id": item.id,
                "snapshot_date": snap_date,
                "spot_price": spot,
                "bid": close,  # Use close as proxy
                "ask": close,
                "mid_price": round(close, 4),
                "drawdown_pct": 0,  # Will be recomputed by pipeline
            }
            try:
                client.schema("options_tracker").table("daily_prices").upsert(
                    price_row, on_conflict="watchlist_id,snapshot_date"
                ).execute()
                total += 1
            except Exception as e:
                logger.warning("    Failed to insert %s: %s", snap_date, e)

        logger.info("    Inserted %d historical rows", len(hist))

        # Update peak_mid from history
        max_close = float(hist["Close"].max())
        max_date = hist["Close"].idxmax().strftime("%Y-%m-%d")
        if max_close > float(item.peak_mid):
            client.schema("options_tracker").table("watchlist").update(
                {"peak_mid": max_close, "peak_mid_date": max_date}
            ).eq("id", item.id).execute()
            logger.info("    Updated peak to $%.2f (%s)", max_close, max_date)

        time.sleep(2)

    logger.info("Backfill complete: %d total rows inserted", total)


if __name__ == "__main__":
    backfill()
