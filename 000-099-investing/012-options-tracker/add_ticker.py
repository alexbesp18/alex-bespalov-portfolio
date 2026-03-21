"""Auto-add a ticker to the watchlist by finding ATM + OTM strikes via delta.

Usage:
    python add_ticker.py AMZN
    python add_ticker.py AMZN --exp 2028-01-21
    python add_ticker.py AMZN --atm-delta 0.50 --otm-delta 0.25
    python add_ticker.py AMZN --dry-run
"""

import argparse
import logging
from datetime import datetime, timedelta

import yfinance as yf
from py_vollib.black_scholes_merton.greeks.analytical import delta as bsm_delta

from config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def find_best_expiration(ticker: yf.Ticker, target_exp: str | None = None) -> str:
    """Find the LEAPS expiration closest to target (default: Dec 2027)."""
    exps = ticker.options
    if target_exp and target_exp in exps:
        return target_exp

    # Default: closest to Dec 2027
    target = datetime(2027, 12, 17)
    leaps = [e for e in exps if datetime.strptime(e, "%Y-%m-%d") > datetime.now() + timedelta(days=365)]
    if not leaps:
        raise ValueError(f"No LEAPS expirations found for {ticker.ticker}")

    return min(leaps, key=lambda e: abs(datetime.strptime(e, "%Y-%m-%d") - target))


def compute_deltas(chain_calls, spot: float, t_years: float, rfr: float, div_yield: float) -> list[dict]:
    """Compute BSM delta for each strike in the chain."""
    results = []
    for _, row in chain_calls.iterrows():
        strike = float(row["strike"])
        iv = float(row.get("impliedVolatility") or 0)
        if iv <= 0 or strike <= 0:
            continue
        try:
            d = bsm_delta("c", spot, strike, t_years, rfr, iv, div_yield)
            results.append({"strike": strike, "delta": d, "iv": iv, "bid": row.get("bid", 0), "ask": row.get("ask", 0)})
        except Exception:
            continue
    return results


def find_closest_strike(deltas: list[dict], target: float) -> dict:
    """Find the strike with delta closest to target."""
    return min(deltas, key=lambda d: abs(d["delta"] - target))


def get_risk_free_rate() -> float:
    try:
        tnx = yf.Ticker("^TNX")
        hist = tnx.history(period="1d")
        if not hist.empty:
            return float(hist["Close"].iloc[-1]) / 100
    except Exception:
        pass
    return 0.045


def add_ticker(symbol: str, exp: str | None = None, atm_delta: float = 0.50, otm_delta: float = 0.30, dry_run: bool = False):
    """Add ATM + OTM LEAPS for a ticker to the watchlist."""
    ticker = yf.Ticker(symbol)
    spot = ticker.info.get("regularMarketPrice") or ticker.info.get("currentPrice")
    if not spot:
        logger.error("Could not get spot price for %s", symbol)
        return

    raw_div = float(ticker.info.get("dividendYield") or 0)
    div_yield = raw_div if raw_div < 0.20 else raw_div / 100  # yfinance sometimes returns % instead of decimal
    rfr = get_risk_free_rate()

    # Find expiration
    best_exp = find_best_expiration(ticker, exp)
    exp_dt = datetime.strptime(best_exp, "%Y-%m-%d")
    t_years = (exp_dt - datetime.now()).days / 365.0

    logger.info("%s: spot=$%.2f, exp=%s (%.1f yrs), rfr=%.3f, div=%.4f", symbol, spot, best_exp, t_years, rfr, div_yield)

    # Fetch chain and compute deltas
    chain = ticker.option_chain(best_exp)
    deltas = compute_deltas(chain.calls, float(spot), t_years, rfr, div_yield)
    if not deltas:
        logger.error("No valid strikes with IV for %s %s", symbol, best_exp)
        return

    # Find ATM and OTM strikes
    atm = find_closest_strike(deltas, atm_delta)
    otm = find_closest_strike(deltas, otm_delta)

    # Format expiration label
    exp_label = exp_dt.strftime("%b%y")  # e.g., "Dec27"

    picks = [
        {"strike": atm["strike"], "delta": atm["delta"], "label": f"{symbol} ATM {exp_label}", "type": "ATM"},
        {"strike": otm["strike"], "delta": otm["delta"], "label": f"{symbol} OTM {exp_label}", "type": "OTM"},
    ]

    for p in picks:
        logger.info("  %s: $%.0f strike (delta=%.3f)", p["type"], p["strike"], p["delta"])

    if dry_run:
        logger.info("Dry run — not inserting into watchlist")
        return

    # Insert into Supabase watchlist
    settings = get_settings()
    if not settings.has_supabase:
        logger.error("Supabase not configured")
        return

    from supabase import create_client

    client = create_client(settings.supabase_url, settings.supabase_service_key)

    for p in picks:
        row = {
            "ticker": symbol.upper(),
            "expiration": best_exp,
            "strike": p["strike"],
            "option_type": "call",
            "label": p["label"],
            "is_active": True,
            "peak_mid": 0,
            "last_alert_level": 0,
        }
        try:
            client.schema("options_tracker").table("watchlist").upsert(
                row, on_conflict="ticker,expiration,strike,option_type"
            ).execute()
            logger.info("  Inserted %s into watchlist", p["label"])
        except Exception as e:
            logger.error("  Failed to insert %s: %s", p["label"], e)


def main():
    parser = argparse.ArgumentParser(description="Add a ticker to LEAPS watchlist (auto ATM + OTM)")
    parser.add_argument("symbol", help="Ticker symbol (e.g., AMZN)")
    parser.add_argument("--exp", help="Target expiration (YYYY-MM-DD)")
    parser.add_argument("--atm-delta", type=float, default=0.50, help="ATM delta target (default: 0.50)")
    parser.add_argument("--otm-delta", type=float, default=0.30, help="OTM delta target (default: 0.30)")
    parser.add_argument("--dry-run", action="store_true", help="Print selections without inserting")
    args = parser.parse_args()

    add_ticker(args.symbol, args.exp, args.atm_delta, args.otm_delta, args.dry_run)


if __name__ == "__main__":
    main()
