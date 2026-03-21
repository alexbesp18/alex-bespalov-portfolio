"""Model validation tests."""

from datetime import date
from decimal import Decimal

from models import DailyPrice, WatchlistItem


class TestWatchlistItem:
    def test_basic_creation(self):
        item = WatchlistItem(
            id=1, ticker="NVDA", expiration=date(2027, 6, 17),
            strike=Decimal("205"), label="NVDA ATM Jun27",
        )
        assert item.ticker == "NVDA"
        assert item.peak_mid == Decimal("0")
        assert item.last_alert_level == 0

    def test_defaults(self):
        item = WatchlistItem(
            id=1, ticker="MU", expiration=date(2027, 6, 17), strike=Decimal("420"),
        )
        assert item.option_type == "call"
        assert item.is_active is True


class TestDailyPrice:
    def test_basic_creation(self):
        price = DailyPrice(
            watchlist_id=1, snapshot_date=date.today(),
            spot_price=Decimal("175.87"), bid=Decimal("27.60"),
            ask=Decimal("27.85"), mid_price=Decimal("27.725"),
        )
        assert price.drawdown_pct == 0.0

    def test_with_drawdown(self):
        price = DailyPrice(
            watchlist_id=1, snapshot_date=date.today(),
            spot_price=Decimal("175"), bid=Decimal("20"),
            ask=Decimal("22"), mid_price=Decimal("21"),
            drawdown_pct=-23.5,
        )
        assert price.drawdown_pct == -23.5
