"""
Multi-Horizon Technical Analysis Calculator.

Calculates technical indicators across three time horizons:
- Short-term (1-2 weeks): 5-10 trading days
- Mid-term (1-3 months): 20-60 trading days (primary focus)
- Long-term (3-12 months): 60-250 trading days

Each horizon uses appropriate indicator periods for meaningful signals.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Tuple

import pandas as pd

from ..market_data.technical import TechnicalCalculator


class TimeHorizon(Enum):
    """Time horizon classification."""
    SHORT_TERM = "short_term"   # 1-2 weeks
    MID_TERM = "mid_term"       # 1-3 months
    LONG_TERM = "long_term"     # 3-12 months


@dataclass
class HorizonConfig:
    """Configuration for each time horizon's indicator periods."""
    rsi_period: int
    macd_fast: int
    macd_slow: int
    macd_signal: int
    stoch_k: int
    stoch_d: int
    adx_period: int
    ema_period: int
    sma_period: int
    vol_avg_period: int
    obv_trend_period: int
    divergence_lookback: int


# Indicator configurations for each time horizon
HORIZON_CONFIGS = {
    TimeHorizon.SHORT_TERM: HorizonConfig(
        rsi_period=7,
        macd_fast=8,
        macd_slow=17,
        macd_signal=9,
        stoch_k=5,
        stoch_d=3,
        adx_period=7,
        ema_period=10,
        sma_period=20,
        vol_avg_period=5,
        obv_trend_period=10,
        divergence_lookback=10,
    ),
    TimeHorizon.MID_TERM: HorizonConfig(
        rsi_period=14,
        macd_fast=12,
        macd_slow=26,
        macd_signal=9,
        stoch_k=14,
        stoch_d=3,
        adx_period=14,
        ema_period=21,
        sma_period=50,
        vol_avg_period=20,
        obv_trend_period=20,
        divergence_lookback=20,
    ),
    TimeHorizon.LONG_TERM: HorizonConfig(
        rsi_period=21,
        macd_fast=19,
        macd_slow=39,
        macd_signal=9,
        stoch_k=21,
        stoch_d=5,
        adx_period=21,
        ema_period=50,
        sma_period=200,
        vol_avg_period=50,
        obv_trend_period=50,
        divergence_lookback=40,
    ),
}


class MultiHorizonCalculator:
    """
    Calculates technical indicators across all three time horizons.

    Provides a comprehensive view of a stock's technical position
    for short-term, mid-term, and long-term investors.
    """

    def __init__(self):
        self.calc = TechnicalCalculator()

    def calculate_all(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate all indicators for all three time horizons.

        Args:
            df: DataFrame with OHLCV data (datetime, open, high, low, close, volume)

        Returns:
            Dict with all indicator values organized by horizon prefix
        """
        if df is None or len(df) < 50:
            return self._empty_result()

        result = {}

        # Base data
        current_price = float(df['close'].iloc[-1])
        result['Price'] = round(current_price, 2)
        result['Change%'] = self._calculate_change_pct(df)

        # Calculate each horizon
        result.update(self._calculate_short_term(df, current_price))
        result.update(self._calculate_mid_term(df, current_price))
        result.update(self._calculate_long_term(df, current_price))

        return result

    def _calculate_change_pct(self, df: pd.DataFrame) -> str:
        """Calculate daily change percentage."""
        if len(df) < 2:
            return "+0.00%"
        current = float(df['close'].iloc[-1])
        previous = float(df['close'].iloc[-2])
        change = ((current - previous) / previous) * 100 if previous > 0 else 0
        return f"{change:+.2f}%"

    def _calculate_short_term(self, df: pd.DataFrame, current_price: float) -> Dict[str, Any]:
        """Calculate short-term (1-2 week) indicators."""
        cfg = HORIZON_CONFIGS[TimeHorizon.SHORT_TERM]

        # RSI
        rsi_series = self.calc.rsi(df['close'], cfg.rsi_period)
        st_rsi = self._safe_float(rsi_series.iloc[-1], 50.0)

        # Stochastic
        stoch_k, stoch_d = self.calc.stochastic(df, cfg.stoch_k, cfg.stoch_d)
        st_stoch_k = self._safe_float(stoch_k.iloc[-1], 50.0)

        # MACD
        macd_line, signal_line, histogram = self.calc.macd(
            df['close'], cfg.macd_fast, cfg.macd_slow, cfg.macd_signal
        )
        st_macd_hist = self._safe_float(histogram.iloc[-1], 0.0)

        # Price vs EMA
        ema = self.calc.ema(df['close'], cfg.ema_period)
        ema_val = self._safe_float(ema.iloc[-1], current_price)
        st_price_vs_ema = round(((current_price - ema_val) / ema_val) * 100, 2) if ema_val > 0 else 0.0

        # Volume ratio
        avg_vol = df['volume'].tail(cfg.vol_avg_period).mean()
        current_vol = df['volume'].iloc[-1]
        st_vol_ratio = round(current_vol / avg_vol, 2) if avg_vol > 0 else 1.0

        return {
            'ST_RSI_7': round(st_rsi, 1),
            'ST_Stoch_K': round(st_stoch_k, 1),
            'ST_MACD_Hist': round(st_macd_hist, 4),
            'ST_Price_vs_EMA10': f"{st_price_vs_ema:+.2f}%",
            'ST_Vol_Ratio_5d': f"{st_vol_ratio:.1f}x",
        }

    def _calculate_mid_term(self, df: pd.DataFrame, current_price: float) -> Dict[str, Any]:
        """Calculate mid-term (1-3 month) indicators."""
        cfg = HORIZON_CONFIGS[TimeHorizon.MID_TERM]

        # RSI
        rsi_series = self.calc.rsi(df['close'], cfg.rsi_period)
        mt_rsi = self._safe_float(rsi_series.iloc[-1], 50.0)

        # MACD
        macd_line, signal_line, histogram = self.calc.macd(
            df['close'], cfg.macd_fast, cfg.macd_slow, cfg.macd_signal
        )
        mt_macd_hist = self._safe_float(histogram.iloc[-1], 0.0)

        # Price vs SMA50
        sma50 = self.calc.sma(df['close'], cfg.sma_period)
        sma50_val = self._safe_float(sma50.iloc[-1], current_price)
        mt_price_vs_sma50 = round(((current_price - sma50_val) / sma50_val) * 100, 2) if sma50_val > 0 else 0.0

        # ADX
        mt_adx = self.calc.adx(df, cfg.adx_period)

        # Divergence (RSI + OBV combined)
        mt_divergence = self._detect_combined_divergence(df, cfg.divergence_lookback)

        # Volume trend (OBV slope)
        obv = self.calc.obv(df)
        mt_vol_trend = self._classify_obv_trend(obv, cfg.obv_trend_period)

        # Reversal score (from reversal_scoring_v2 logic)
        mt_reversal_score, mt_conviction = self._calculate_reversal_score(df)

        # Entry score (broader metric)
        mt_entry_score = self._calculate_entry_score(
            df, current_price, mt_rsi, mt_macd_hist, mt_adx,
            mt_price_vs_sma50, mt_vol_trend, mt_divergence
        )

        return {
            'MT_RSI_14': round(mt_rsi, 1),
            'MT_MACD_Hist': round(mt_macd_hist, 4),
            'MT_Price_vs_SMA50': f"{mt_price_vs_sma50:+.2f}%",
            'MT_ADX': round(mt_adx, 1),
            'MT_Divergence': mt_divergence,
            'MT_Vol_Trend_20d': mt_vol_trend,
            'MT_Reversal_Score': round(mt_reversal_score, 1),
            'MT_Entry_Score': round(mt_entry_score, 1),
            'MT_Conviction': mt_conviction,
        }

    def _calculate_long_term(self, df: pd.DataFrame, current_price: float) -> Dict[str, Any]:
        """Calculate long-term (3-12 month) indicators."""
        cfg = HORIZON_CONFIGS[TimeHorizon.LONG_TERM]

        # RSI
        rsi_series = self.calc.rsi(df['close'], cfg.rsi_period)
        lt_rsi = self._safe_float(rsi_series.iloc[-1], 50.0)

        # MACD
        macd_line, signal_line, histogram = self.calc.macd(
            df['close'], cfg.macd_fast, cfg.macd_slow, cfg.macd_signal
        )
        lt_macd_hist = self._safe_float(histogram.iloc[-1], 0.0)

        # Price vs SMA200
        sma200 = self.calc.sma(df['close'], min(200, len(df)))
        sma200_val = self._safe_float(sma200.iloc[-1], current_price)
        lt_price_vs_sma200 = round(((current_price - sma200_val) / sma200_val) * 100, 2) if sma200_val > 0 else 0.0

        # SMA50 vs SMA200 (Golden/Death cross)
        sma50 = self.calc.sma(df['close'], 50)
        sma50_val = self._safe_float(sma50.iloc[-1], current_price)
        lt_cross_status = self._classify_ma_cross(sma50, sma200)

        # ADX
        lt_adx = self.calc.adx(df, cfg.adx_period)

        # OBV trend
        obv = self.calc.obv(df)
        lt_obv_trend = self._classify_obv_trend(obv, cfg.obv_trend_period)

        # 52-week position
        high_52w = float(df['high'].max())
        low_52w = float(df['low'].min())
        lt_52w_position = round(((current_price - low_52w) / (high_52w - low_52w)) * 100, 1) if high_52w > low_52w else 50.0

        # Long-term trend classification
        lt_trend = self._classify_long_term_trend(current_price, sma50_val, sma200_val, lt_adx)

        # Months in trend
        lt_months_in_trend = self._estimate_trend_duration(df, sma200)

        # Long-term score
        lt_score = self._calculate_long_term_score(
            lt_rsi, lt_macd_hist, lt_price_vs_sma200, lt_cross_status,
            lt_adx, lt_obv_trend, lt_52w_position, lt_trend
        )

        return {
            'LT_RSI_21': round(lt_rsi, 1),
            'LT_MACD_Hist': round(lt_macd_hist, 4),
            'LT_Price_vs_SMA200': f"{lt_price_vs_sma200:+.2f}%",
            'LT_SMA50_vs_SMA200': lt_cross_status,
            'LT_ADX_21': round(lt_adx, 1),
            'LT_OBV_Trend_50d': lt_obv_trend,
            'LT_52W_Position': f"{lt_52w_position:.0f}%",
            'LT_Trend': lt_trend,
            'LT_Months_in_Trend': lt_months_in_trend,
            'LT_Score': round(lt_score, 1),
        }

    def _detect_combined_divergence(self, df: pd.DataFrame, lookback: int) -> str:
        """Detect combined RSI + OBV divergence."""
        if len(df) < lookback + 5:
            return "NONE"

        recent = df.iloc[-lookback:]
        price_start = float(recent['close'].iloc[0])
        price_end = float(recent['close'].iloc[-1])

        # RSI divergence
        rsi = self.calc.rsi(df['close'], 14)
        rsi_start = self._safe_float(rsi.iloc[-lookback], 50)
        rsi_end = self._safe_float(rsi.iloc[-1], 50)

        # OBV divergence
        obv = self.calc.obv(df)
        obv_start = float(obv.iloc[-lookback])
        obv_end = float(obv.iloc[-1])

        # Bullish: price lower, RSI or OBV higher
        bullish_rsi = price_end < price_start and rsi_end > rsi_start
        bullish_obv = price_end < price_start and obv_end > obv_start

        # Bearish: price higher, RSI or OBV lower
        bearish_rsi = price_end > price_start and rsi_end < rsi_start
        bearish_obv = price_end > price_start and obv_end < obv_start

        if bullish_rsi and bullish_obv:
            return "STRONG_BULLISH"
        elif bullish_rsi or bullish_obv:
            return "BULLISH"
        elif bearish_rsi and bearish_obv:
            return "STRONG_BEARISH"
        elif bearish_rsi or bearish_obv:
            return "BEARISH"
        return "NONE"

    def _classify_obv_trend(self, obv: pd.Series, period: int) -> str:
        """Classify OBV trend over period."""
        if len(obv) < period:
            return "NEUTRAL"

        obv_start = float(obv.iloc[-period])
        obv_end = float(obv.iloc[-1])

        if obv_start == 0:
            return "NEUTRAL"

        change_pct = ((obv_end - obv_start) / abs(obv_start)) * 100

        if change_pct > 10:
            return "ACCUMULATING"
        elif change_pct < -10:
            return "DISTRIBUTING"
        return "NEUTRAL"

    def _classify_ma_cross(self, sma50: pd.Series, sma200: pd.Series) -> str:
        """Classify SMA50 vs SMA200 relationship."""
        if len(sma50) < 5 or len(sma200) < 5:
            return "NEUTRAL"

        sma50_now = self._safe_float(sma50.iloc[-1], 0)
        sma200_now = self._safe_float(sma200.iloc[-1], 0)
        sma50_5d_ago = self._safe_float(sma50.iloc[-5], 0)
        sma200_5d_ago = self._safe_float(sma200.iloc[-5], 0)

        if sma200_now == 0:
            return "NEUTRAL"

        # Check for recent cross
        above_now = sma50_now > sma200_now
        above_before = sma50_5d_ago > sma200_5d_ago

        if above_now and not above_before:
            return "GOLDEN_CROSS"
        elif not above_now and above_before:
            return "DEATH_CROSS"
        elif above_now:
            return "BULLISH"
        else:
            return "BEARISH"

    def _classify_long_term_trend(self, price: float, sma50: float, sma200: float, adx: float) -> str:
        """Classify the long-term trend."""
        if sma200 == 0:
            return "UNDEFINED"

        above_200 = price > sma200
        above_50 = price > sma50
        strong_trend = adx > 25

        if above_200 and above_50 and strong_trend:
            return "STRONG_UPTREND"
        elif above_200 and above_50:
            return "UPTREND"
        elif not above_200 and not above_50 and strong_trend:
            return "STRONG_DOWNTREND"
        elif not above_200 and not above_50:
            return "DOWNTREND"
        else:
            return "SIDEWAYS"

    def _estimate_trend_duration(self, df: pd.DataFrame, sma200: pd.Series) -> str:
        """Estimate how long the current trend has persisted."""
        if len(df) < 60:
            return "< 1 month"

        current_price = float(df['close'].iloc[-1])
        sma200_now = self._safe_float(sma200.iloc[-1], current_price)
        above_now = current_price > sma200_now

        # Count consecutive days in same position
        days_in_trend = 0
        for i in range(1, min(len(df), 252)):  # Max 1 year
            idx = -i - 1
            if idx < -len(df):
                break

            past_price = float(df['close'].iloc[idx])
            past_sma = self._safe_float(sma200.iloc[idx], past_price)
            past_above = past_price > past_sma

            if past_above == above_now:
                days_in_trend += 1
            else:
                break

        # Convert to months
        months = days_in_trend / 21  # ~21 trading days per month

        if months < 1:
            return "< 1 month"
        elif months < 3:
            return f"~{int(months)} months"
        elif months < 6:
            return "3-6 months"
        elif months < 12:
            return "6-12 months"
        else:
            return "> 12 months"

    def _calculate_reversal_score(self, df: pd.DataFrame) -> Tuple[float, str]:
        """
        Calculate reversal score using v3 logic from reversal_scoring_v2.

        Returns:
            Tuple of (score, conviction_level)
        """
        try:
            from .reversal_scoring_v2 import ReversalScorerV3
            scorer = ReversalScorerV3()
            result = scorer.score(df, direction="up")
            return result.total_score, result.conviction.value
        except ImportError:
            # Fallback to simple calculation
            return self._simple_reversal_score(df)

    def _simple_reversal_score(self, df: pd.DataFrame) -> Tuple[float, str]:
        """Simple fallback reversal scoring."""
        rsi = self.calc.rsi(df['close'], 14)
        rsi_val = self._safe_float(rsi.iloc[-1], 50)

        # Simple scoring based on RSI
        if rsi_val < 25:
            return 8.0, "HIGH"
        elif rsi_val < 30:
            return 7.0, "MEDIUM"
        elif rsi_val < 35:
            return 6.0, "LOW"
        else:
            return 4.0, "NONE"

    def _calculate_entry_score(
        self, df: pd.DataFrame, price: float, rsi: float, macd_hist: float,
        adx: float, price_vs_sma50: float, vol_trend: str, divergence: str
    ) -> float:
        """
        Calculate mid-term entry score (1-10).

        This is broader than reversal score - considers:
        - Trend quality (not just oversold)
        - Entry timing (pullback to support)
        - Momentum confirmation
        - Risk/reward setup
        """
        score = 5.0  # Start neutral

        # Trend position (2 points max)
        # Near SMA50 is good entry (within 5%)
        if -5 <= price_vs_sma50 <= 0:
            score += 2.0  # Pullback to support
        elif 0 < price_vs_sma50 <= 3:
            score += 1.5  # Slight above, still good
        elif -10 <= price_vs_sma50 < -5:
            score += 1.0  # Deeper pullback, more risk
        elif price_vs_sma50 < -10:
            score -= 1.0  # Too far below, trend may be broken
        elif price_vs_sma50 > 10:
            score -= 0.5  # Extended, wait for pullback

        # RSI position (1.5 points max)
        if 30 <= rsi <= 45:
            score += 1.5  # Good entry zone (not extreme)
        elif 45 < rsi <= 55:
            score += 1.0  # Neutral, acceptable
        elif 25 <= rsi < 30:
            score += 1.0  # Oversold, good if trend ok
        elif rsi < 25:
            score += 0.5  # Very oversold, could be falling knife
        elif rsi > 70:
            score -= 1.0  # Overbought, wait

        # MACD momentum (1 point max)
        if macd_hist > 0:
            score += 1.0  # Positive momentum
        elif macd_hist > -0.5:
            score += 0.5  # Turning positive
        # Negative MACD doesn't subtract, just less attractive

        # ADX trend strength (1 point max)
        if 20 <= adx <= 35:
            score += 1.0  # Good trend, not extreme
        elif adx > 35:
            score += 0.5  # Strong trend, but may be late
        # Low ADX just means no clear trend

        # Volume trend (1 point max)
        if vol_trend == "ACCUMULATING":
            score += 1.0
        elif vol_trend == "DISTRIBUTING":
            score -= 0.5

        # Divergence (1.5 points max)
        if divergence == "STRONG_BULLISH":
            score += 1.5
        elif divergence == "BULLISH":
            score += 1.0
        elif divergence == "STRONG_BEARISH":
            score -= 1.0
        elif divergence == "BEARISH":
            score -= 0.5

        # Clamp to 1-10
        return max(1.0, min(10.0, score))

    def _calculate_long_term_score(
        self, rsi: float, macd_hist: float, price_vs_sma200: float,
        cross_status: str, adx: float, obv_trend: str,
        position_52w: float, trend: str
    ) -> float:
        """Calculate long-term health score (1-10)."""
        score = 5.0

        # Trend status (2 points max)
        if trend == "STRONG_UPTREND":
            score += 2.0
        elif trend == "UPTREND":
            score += 1.5
        elif trend == "SIDEWAYS":
            score += 0.0
        elif trend == "DOWNTREND":
            score -= 1.0
        elif trend == "STRONG_DOWNTREND":
            score -= 2.0

        # MA cross status (1.5 points max)
        if cross_status == "GOLDEN_CROSS":
            score += 1.5
        elif cross_status == "BULLISH":
            score += 1.0
        elif cross_status == "DEATH_CROSS":
            score -= 1.5
        elif cross_status == "BEARISH":
            score -= 1.0

        # Price vs SMA200 (1 point max)
        if price_vs_sma200 > 0:
            score += min(1.0, price_vs_sma200 / 10)  # Up to +1 for 10%+ above
        else:
            score += max(-1.0, price_vs_sma200 / 20)  # Down to -1 for 20%+ below

        # ADX (0.5 points max)
        if adx > 25:
            score += 0.5  # Strong trend

        # OBV (1 point max)
        if obv_trend == "ACCUMULATING":
            score += 1.0
        elif obv_trend == "DISTRIBUTING":
            score -= 0.5

        # 52-week position (1 point max)
        if position_52w > 70:
            score += 0.5  # Near highs, strong
        elif position_52w < 30:
            score -= 0.5  # Near lows, weak

        # RSI health (1 point max)
        if 40 <= rsi <= 60:
            score += 0.5  # Healthy range
        elif rsi > 70:
            score -= 0.5  # Overbought

        return max(1.0, min(10.0, score))

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """Safely convert value to float."""
        if pd.isna(value):
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure for insufficient data."""
        return {
            'Price': 0.0,
            'Change%': '+0.00%',
            # Short-term
            'ST_RSI_7': 50.0,
            'ST_Stoch_K': 50.0,
            'ST_MACD_Hist': 0.0,
            'ST_Price_vs_EMA10': '+0.00%',
            'ST_Vol_Ratio_5d': '1.0x',
            # Mid-term
            'MT_RSI_14': 50.0,
            'MT_MACD_Hist': 0.0,
            'MT_Price_vs_SMA50': '+0.00%',
            'MT_ADX': 20.0,
            'MT_Divergence': 'NONE',
            'MT_Vol_Trend_20d': 'NEUTRAL',
            'MT_Reversal_Score': 5.0,
            'MT_Entry_Score': 5.0,
            'MT_Conviction': 'NONE',
            # Long-term
            'LT_RSI_21': 50.0,
            'LT_MACD_Hist': 0.0,
            'LT_Price_vs_SMA200': '+0.00%',
            'LT_SMA50_vs_SMA200': 'NEUTRAL',
            'LT_ADX_21': 20.0,
            'LT_OBV_Trend_50d': 'NEUTRAL',
            'LT_52W_Position': '50%',
            'LT_Trend': 'UNDEFINED',
            'LT_Months_in_Trend': '< 1 month',
            'LT_Score': 5.0,
        }
