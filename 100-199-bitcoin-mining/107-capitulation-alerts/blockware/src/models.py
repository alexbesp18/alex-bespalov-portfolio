from dataclasses import dataclass
from typing import Optional


@dataclass
class MinerOffer:
    offer_id: int
    model_name: str
    model_description: str
    model_id_matched: Optional[int]  # the itemModel ID if we can determine it
    price_usd: float
    price_btc: float
    dollar_per_th: float
    deal_score: int
    hashrate_ideal_th: float    # converted from raw to TH/s
    hashrate_24hr_th: float
    watts_per_th: float
    energy_price: float
    monthly_energy_cost: float
    est_monthly_revenue: float
    est_monthly_profit: float
    hosting_site: str
    offer_count: int            # number of units in the bundle
    created_at: str
    link: str


@dataclass
class TradeStats:
    model_id: int
    ath_price: Optional[float]
    atl_price: Optional[float]
    last_trade_price: Optional[float]
    current_lowest_offer: Optional[float]
    highest_bid: Optional[float]
    range_90d_high: Optional[float]
    range_90d_low: Optional[float]
    range_90d_midpoint: Optional[float]  # (high + low) / 2


@dataclass
class Alert:
    offer: MinerOffer
    btc_price: float
    hashprice_usd: float
    # Primary benchmark (trigger)
    last_trade_price: Optional[float]
    discount_vs_last_trade: Optional[float]
    # Context benchmarks
    ath_price: Optional[float]
    discount_vs_ath: Optional[float]
    range_90d_midpoint: Optional[float]
    discount_vs_90d_mid: Optional[float]
