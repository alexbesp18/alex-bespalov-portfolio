"""True Value Scorer — gate filter + weighted scoring engine.

Filters out falling knives by requiring structural integrity,
then scores remaining names on 4 weighted components.

Score = oversold(30%) + structure(35%) + accumulation(20%) + reversal(15%)
"""

import logging
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd

from shared_core.scoring.multi_horizon import MultiHorizonCalculator
from .calculator import TechnicalCalculator
from .true_value_models import TrueValueResult, Tier, assign_tier

logger = logging.getLogger(__name__)

# Dedup pairs — keep the more liquid symbol
DEDUP_PAIRS = {
    "GOOGL": "GOOG",
    "BRK.A": "BRK.B",
    "FOX": "FOXA",
}


class TrueValueScorer:
    """Gate filter + 4-component weighted scoring engine."""

    def __init__(self) -> None:
        self.calculator = TechnicalCalculator()
        self.mh_calculator = MultiHorizonCalculator()

    def score_batch(
        self, raw_data: Dict[str, Any], tickers: List[str]
    ) -> List[TrueValueResult]:
        """Score all tickers through gate filter and weighted components.

        Args:
            raw_data: Dict mapping ticker -> raw time series data from fetcher.
            tickers: List of ticker symbols to process.

        Returns:
            Sorted list of TrueValueResult (highest score first), capped at 15.
        """
        results: List[TrueValueResult] = []

        for ticker in tickers:
            data_ts = raw_data.get(ticker)
            if not data_ts:
                continue

            df = self.calculator.process_data(data_ts)
            if df is None or df.empty or len(df) < 50:
                continue

            mh = self.mh_calculator.calculate_all(df)

            mt_rsi = mh.get("MT_RSI_14", 50.0)
            lt_score = mh.get("LT_Score", 5.0)
            sma = mh.get("LT_SMA50_vs_SMA200", "NEUTRAL")
            obv = mh.get("LT_OBV_Trend_50d", "NEUTRAL")
            lt_trend = mh.get("LT_Trend", "UNDEFINED")

            passes, reason = self._passes_gate(mt_rsi, lt_score, sma, obv, lt_trend)
            if not passes:
                logger.debug(f"{ticker}: gate fail — {reason}")
                continue

            # Extract additional fields
            lt_rsi = mh.get("LT_RSI_21", 50.0)
            price_vs_sma200_str = mh.get("LT_Price_vs_SMA200", "+0.00%")
            price_vs_sma200 = self._parse_pct(price_vs_sma200_str)
            w52_str = mh.get("LT_52W_Position", "50%")
            w52_position = self._parse_pct(w52_str)
            divergence = mh.get("MT_Divergence", "NONE")
            mt_reversal = mh.get("MT_Reversal_Score", 5.0)
            mt_entry = mh.get("MT_Entry_Score", 5.0)

            # Score components (0-10 each)
            oversold = self._oversold_score(mt_rsi, lt_rsi, price_vs_sma200)
            structure = self._structure_score(lt_score, sma, lt_trend, w52_position)
            accumulation = self._accumulation_score(obv)
            reversal = self._reversal_score(divergence, mt_reversal, mt_entry)

            # Weighted composite
            tv_score = (
                oversold * 0.30
                + structure * 0.35
                + accumulation * 0.20
                + reversal * 0.15
            )
            tv_score = round(max(1.0, min(10.0, tv_score)), 1)

            # Price movements
            movements = self._calculate_price_movements(df)

            results.append(
                TrueValueResult(
                    ticker=ticker,
                    price=round(float(df.iloc[-1]["close"]), 2),
                    true_value_score=tv_score,
                    tier=assign_tier(tv_score),
                    oversold_component=round(oversold, 1),
                    structure_component=round(structure, 1),
                    accumulation_component=round(accumulation, 1),
                    reversal_component=round(reversal, 1),
                    mt_rsi=round(mt_rsi, 1),
                    lt_score=round(lt_score, 1),
                    sma_alignment=sma,
                    obv_trend=obv,
                    pct_1m=movements.get("pct_1m", 0.0),
                    pct_1y=movements.get("pct_1y", 0.0),
                )
            )

        results = self._dedup(results)
        results.sort(key=lambda r: r.true_value_score, reverse=True)
        return results[:15]

    # ------------------------------------------------------------------
    # Gate filter
    # ------------------------------------------------------------------

    @staticmethod
    def _passes_gate(
        mt_rsi: float,
        lt_score: float,
        sma: str,
        obv: str,
        lt_trend: str,
    ) -> Tuple[bool, str]:
        """Apply 3-stage gate filter.

        Returns:
            (passes, rejection_reason)
        """
        # Gate 1: Must be oversold
        if mt_rsi >= 35:
            return False, f"MT_RSI {mt_rsi:.1f} >= 35"

        # Gate 2: Must have structural integrity (at least ONE path)
        has_structure = any([
            sma == "BULLISH" and lt_score >= 5.0,
            obv == "ACCUMULATING" and lt_score >= 4.0,
            lt_score >= 7.0,
            sma == "BULLISH" and obv == "ACCUMULATING",
        ])
        if not has_structure:
            return False, f"no structure path (LT {lt_score}, SMA {sma}, OBV {obv})"

        # Gate 3: NOT in terminal decline
        if (
            lt_trend == "STRONG_DOWNTREND"
            and sma == "BEARISH"
            and obv == "DISTRIBUTING"
        ):
            return False, "terminal decline"

        return True, ""

    # ------------------------------------------------------------------
    # Component scoring functions (each returns 0-10)
    # ------------------------------------------------------------------

    @staticmethod
    def _oversold_score(mt_rsi: float, lt_rsi: float, price_vs_sma200: float) -> float:
        """How deeply oversold across timeframes.

        - MT RSI contribution (0-5): lower RSI = higher score
        - LT RSI contribution (0-3): lower long-term RSI adds conviction
        - Price vs SMA200 (0-2): further below = more oversold
        """
        # MT RSI: 0 -> 5, 35 -> 0 (linear)
        mt_part = max(0.0, min(5.0, (35 - mt_rsi) / 7.0))

        # LT RSI: below 40 starts scoring, max at 20
        if lt_rsi <= 20:
            lt_part = 3.0
        elif lt_rsi <= 40:
            lt_part = 3.0 * (40 - lt_rsi) / 20.0
        else:
            lt_part = 0.0

        # Price vs SMA200: negative = below SMA200
        if price_vs_sma200 <= -15:
            sma_part = 2.0
        elif price_vs_sma200 <= 0:
            sma_part = 2.0 * abs(price_vs_sma200) / 15.0
        else:
            sma_part = 0.0

        return mt_part + lt_part + sma_part

    @staticmethod
    def _structure_score(
        lt_score: float, sma: str, lt_trend: str, w52_position: float
    ) -> float:
        """Long-term structural integrity.

        - LT Score contribution (0-4): direct mapping
        - SMA alignment (0-3): BULLISH/GOLDEN best
        - Trend bonus (0-2): uptrend gets points
        - 52W position (0-1): mid-range is best for entry
        """
        # LT Score: map 1-10 -> 0-4
        lt_part = max(0.0, min(4.0, (lt_score - 1.0) * 4.0 / 9.0))

        # SMA alignment
        sma_scores = {
            "GOLDEN_CROSS": 3.0,
            "BULLISH": 2.5,
            "NEUTRAL": 1.0,
            "BEARISH": 0.5,
            "DEATH_CROSS": 0.0,
        }
        sma_part = sma_scores.get(sma, 1.0)

        # Trend
        trend_scores = {
            "STRONG_UPTREND": 2.0,
            "UPTREND": 1.5,
            "SIDEWAYS": 0.5,
            "DOWNTREND": 0.0,
            "STRONG_DOWNTREND": 0.0,
            "UNDEFINED": 0.5,
        }
        trend_part = trend_scores.get(lt_trend, 0.5)

        # 52W position: 20-60% is ideal entry zone (not too high, not cratering)
        if 20 <= w52_position <= 60:
            w52_part = 1.0
        elif w52_position < 20:
            w52_part = 0.3
        else:
            w52_part = 0.5

        return lt_part + sma_part + trend_part + w52_part

    @staticmethod
    def _accumulation_score(obv_trend: str) -> float:
        """Institutional accumulation signal.

        Simple mapping — OBV trend is the primary signal.
        Returns 0-10.
        """
        scores = {
            "ACCUMULATING": 9.0,
            "NEUTRAL": 5.0,
            "DISTRIBUTING": 1.5,
        }
        return scores.get(obv_trend, 5.0)

    @staticmethod
    def _reversal_score(
        divergence: str, mt_reversal: float, mt_entry: float
    ) -> float:
        """Near-term reversal probability.

        - Divergence (0-4): bullish divergence is a strong reversal signal
        - MT Reversal Score (0-3): mapped from 1-10
        - MT Entry Score (0-3): mapped from 1-10
        """
        div_scores = {
            "STRONG_BULLISH": 4.0,
            "BULLISH": 3.0,
            "NONE": 1.0,
            "BEARISH": 0.5,
            "STRONG_BEARISH": 0.0,
        }
        div_part = div_scores.get(divergence, 1.0)

        # Map 1-10 -> 0-3
        rev_part = max(0.0, min(3.0, (mt_reversal - 1.0) * 3.0 / 9.0))
        entry_part = max(0.0, min(3.0, (mt_entry - 1.0) * 3.0 / 9.0))

        return div_part + rev_part + entry_part

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_pct(val: str) -> float:
        """Parse percentage strings like '+6.56%' or '67%' to float."""
        try:
            return float(str(val).replace("%", "").replace("+", ""))
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _calculate_price_movements(df: pd.DataFrame) -> Dict[str, float]:
        """Calculate 1M and 1Y price changes from OHLCV DataFrame."""
        close = df["close"]
        current = float(close.iloc[-1])
        result: Dict[str, float] = {}

        # 1 month (~21 trading days)
        if len(close) >= 21:
            prev = float(close.iloc[-21])
            result["pct_1m"] = round((current - prev) / prev * 100, 1) if prev else 0.0
        else:
            result["pct_1m"] = 0.0

        # 1 year (~252 trading days)
        if len(close) >= 252:
            prev = float(close.iloc[-252])
            result["pct_1y"] = round((current - prev) / prev * 100, 1) if prev else 0.0
        else:
            result["pct_1y"] = 0.0

        return result

    @staticmethod
    def _dedup(results: List[TrueValueResult]) -> List[TrueValueResult]:
        """Remove duplicate share classes, keeping the higher-scored one."""
        seen: Dict[str, TrueValueResult] = {}
        for r in results:
            # Check if this ticker is the less-liquid version
            preferred = DEDUP_PAIRS.get(r.ticker)
            key = preferred or r.ticker

            if key in seen:
                if r.true_value_score > seen[key].true_value_score:
                    seen[key] = r
            else:
                seen[key] = r

        return list(seen.values())
