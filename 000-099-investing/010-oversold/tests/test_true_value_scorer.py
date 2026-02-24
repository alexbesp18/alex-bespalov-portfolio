"""Tests for TrueValueScorer — gate filter, components, and tier assignment."""

import pytest

from src.true_value_scorer import TrueValueScorer
from src.true_value_models import Tier, assign_tier, TrueValueResult


@pytest.fixture
def scorer():
    return TrueValueScorer()


# ---------------------------------------------------------------
# Gate filter
# ---------------------------------------------------------------

class TestGate:
    def test_amd_passes(self, scorer):
        """AMD: RSI 26.6, LT 7.7, SMA BULLISH, OBV ACCUMULATING → PASS."""
        passes, _ = scorer._passes_gate(26.6, 7.7, "BULLISH", "ACCUMULATING", "UPTREND")
        assert passes is True

    def test_gety_fails(self, scorer):
        """GETY: RSI 15.2, LT 1.0, BEARISH, DISTRIBUTING → FAIL (no structure)."""
        passes, _ = scorer._passes_gate(
            15.2, 1.0, "BEARISH", "DISTRIBUTING", "STRONG_DOWNTREND"
        )
        assert passes is False

    def test_terminal_decline_blocked(self, scorer):
        """Terminal decline gate blocks even if structure would otherwise pass."""
        # LT_Score 7.0 would pass Gate 2, but terminal combo blocks at Gate 3
        passes, reason = scorer._passes_gate(
            25.0, 7.0, "BEARISH", "DISTRIBUTING", "STRONG_DOWNTREND"
        )
        assert passes is False
        assert "terminal" in reason

    def test_visa_fails_no_structure(self, scorer):
        """V: RSI 26.5, LT 2.0, SMA BEARISH, OBV NEUTRAL → FAIL (no structure)."""
        passes, reason = scorer._passes_gate(26.5, 2.0, "BEARISH", "NEUTRAL", "DOWNTREND")
        assert passes is False
        assert "no structure" in reason

    def test_rsi_too_high(self, scorer):
        """RSI >= 35 always fails gate 1."""
        passes, reason = scorer._passes_gate(35.0, 9.0, "BULLISH", "ACCUMULATING", "UPTREND")
        assert passes is False
        assert "RSI" in reason

    def test_rsi_boundary_passes(self, scorer):
        """RSI just below 35 with good structure passes."""
        passes, _ = scorer._passes_gate(34.9, 7.0, "BULLISH", "NEUTRAL", "UPTREND")
        assert passes is True

    def test_path_lt_score_7(self, scorer):
        """LT Score >= 7.0 alone is enough for structural integrity."""
        passes, _ = scorer._passes_gate(25.0, 7.0, "BEARISH", "NEUTRAL", "SIDEWAYS")
        assert passes is True

    def test_path_sma_bullish_obv_accum(self, scorer):
        """SMA BULLISH + OBV ACCUMULATING is enough regardless of LT Score."""
        passes, _ = scorer._passes_gate(25.0, 2.0, "BULLISH", "ACCUMULATING", "SIDEWAYS")
        assert passes is True

    def test_path_obv_accum_lt4(self, scorer):
        """OBV ACCUMULATING + LT >= 4.0 passes."""
        passes, _ = scorer._passes_gate(25.0, 4.0, "BEARISH", "ACCUMULATING", "SIDEWAYS")
        assert passes is True

    def test_path_obv_accum_lt_below4_fails(self, scorer):
        """OBV ACCUMULATING but LT < 4.0 without other paths fails."""
        passes, _ = scorer._passes_gate(25.0, 3.9, "BEARISH", "ACCUMULATING", "SIDEWAYS")
        assert passes is False


# ---------------------------------------------------------------
# Component scoring
# ---------------------------------------------------------------

class TestOversoldScore:
    def test_deeply_oversold(self, scorer):
        """Very low RSI across timeframes scores high."""
        score = scorer._oversold_score(15.0, 20.0, -20.0)
        assert score >= 7.0

    def test_barely_oversold(self, scorer):
        """RSI near 35 boundary scores low."""
        score = scorer._oversold_score(34.0, 45.0, 5.0)
        assert score < 2.0

    def test_mid_range(self, scorer):
        """Moderate oversold levels."""
        score = scorer._oversold_score(25.0, 35.0, -5.0)
        assert 2.0 < score < 6.0


class TestStructureScore:
    def test_strong_structure(self, scorer):
        """High LT score + BULLISH SMA + uptrend."""
        score = scorer._structure_score(9.0, "BULLISH", "STRONG_UPTREND", 40.0)
        assert score >= 7.0

    def test_weak_structure(self, scorer):
        """Low LT score + DEATH_CROSS + downtrend."""
        score = scorer._structure_score(2.0, "DEATH_CROSS", "STRONG_DOWNTREND", 10.0)
        assert score < 2.0


class TestAccumulationScore:
    def test_accumulating(self, scorer):
        assert scorer._accumulation_score("ACCUMULATING") == 9.0

    def test_neutral(self, scorer):
        assert scorer._accumulation_score("NEUTRAL") == 5.0

    def test_distributing(self, scorer):
        assert scorer._accumulation_score("DISTRIBUTING") == 1.5


class TestReversalScore:
    def test_strong_bullish_divergence(self, scorer):
        score = scorer._reversal_score("STRONG_BULLISH", 8.0, 7.0)
        assert score >= 7.0

    def test_no_signals(self, scorer):
        score = scorer._reversal_score("NONE", 4.0, 4.0)
        assert score < 4.0


# ---------------------------------------------------------------
# Tier assignment
# ---------------------------------------------------------------

class TestTierAssignment:
    def test_structural_buy(self):
        assert assign_tier(7.0) == Tier.STRUCTURAL_BUY
        assert assign_tier(9.5) == Tier.STRUCTURAL_BUY

    def test_watchlist_entry(self):
        assert assign_tier(5.5) == Tier.WATCHLIST_ENTRY
        assert assign_tier(6.9) == Tier.WATCHLIST_ENTRY

    def test_reversal_speculative(self):
        assert assign_tier(4.0) == Tier.REVERSAL_SPECULATIVE
        assert assign_tier(5.4) == Tier.REVERSAL_SPECULATIVE


# ---------------------------------------------------------------
# Dedup
# ---------------------------------------------------------------

class TestDedup:
    def test_googl_goog(self, scorer):
        """GOOGL should be deduped in favor of GOOG."""
        results = [
            TrueValueResult(
                ticker="GOOG", price=150.0, true_value_score=7.0,
                tier=Tier.STRUCTURAL_BUY, oversold_component=5.0,
                structure_component=6.0, accumulation_component=9.0,
                reversal_component=4.0, mt_rsi=28.0, lt_score=7.5,
                sma_alignment="BULLISH", obv_trend="ACCUMULATING",
                pct_1m=-5.0, pct_1y=10.0,
            ),
            TrueValueResult(
                ticker="GOOGL", price=149.0, true_value_score=6.8,
                tier=Tier.WATCHLIST_ENTRY, oversold_component=5.0,
                structure_component=5.5, accumulation_component=9.0,
                reversal_component=4.0, mt_rsi=28.5, lt_score=7.3,
                sma_alignment="BULLISH", obv_trend="ACCUMULATING",
                pct_1m=-5.2, pct_1y=9.5,
            ),
        ]
        deduped = scorer._dedup(results)
        assert len(deduped) == 1
        assert deduped[0].ticker == "GOOG"

    def test_no_dedup_for_unrelated(self, scorer):
        """Unrelated tickers should not be deduped."""
        results = [
            TrueValueResult(
                ticker="AMD", price=100.0, true_value_score=7.5,
                tier=Tier.STRUCTURAL_BUY, oversold_component=6.0,
                structure_component=7.0, accumulation_component=9.0,
                reversal_component=5.0, mt_rsi=26.0, lt_score=7.7,
                sma_alignment="BULLISH", obv_trend="ACCUMULATING",
                pct_1m=-8.0, pct_1y=15.0,
            ),
            TrueValueResult(
                ticker="GOOG", price=150.0, true_value_score=7.0,
                tier=Tier.STRUCTURAL_BUY, oversold_component=5.0,
                structure_component=6.0, accumulation_component=9.0,
                reversal_component=4.0, mt_rsi=28.0, lt_score=7.5,
                sma_alignment="BULLISH", obv_trend="ACCUMULATING",
                pct_1m=-5.0, pct_1y=10.0,
            ),
        ]
        deduped = scorer._dedup(results)
        assert len(deduped) == 2


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------

class TestHelpers:
    def test_parse_pct_positive(self, scorer):
        assert scorer._parse_pct("+6.56%") == 6.56

    def test_parse_pct_negative(self, scorer):
        assert scorer._parse_pct("-3.25%") == -3.25

    def test_parse_pct_no_sign(self, scorer):
        assert scorer._parse_pct("67%") == 67.0

    def test_parse_pct_invalid(self, scorer):
        assert scorer._parse_pct("N/A") == 0.0

    def test_parse_pct_none(self, scorer):
        assert scorer._parse_pct(None) == 0.0
