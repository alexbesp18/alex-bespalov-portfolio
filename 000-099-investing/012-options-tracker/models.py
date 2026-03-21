"""Simple data models for the drawdown tracker."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class WatchlistItem(BaseModel):
    id: int
    ticker: str
    expiration: date
    strike: Decimal
    option_type: str = "call"
    label: str | None = None
    is_active: bool = True
    peak_mid: Decimal = Decimal("0")
    peak_mid_date: date | None = None
    last_alert_level: int = 0


class DailyPrice(BaseModel):
    watchlist_id: int
    snapshot_date: date
    spot_price: Decimal
    bid: Decimal
    ask: Decimal
    mid_price: Decimal
    implied_vol: float | None = None
    drawdown_pct: float = 0.0
