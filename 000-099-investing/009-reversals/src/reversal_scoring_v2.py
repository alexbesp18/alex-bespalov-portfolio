"""
Reversal Scoring v3 — Tightened Mid/Long-Term Signal Logic
===========================================================
Focus: Mid-term (weeks) and Long-term (months) reversals only.
Removed short-term noise (stochastic, consecutive days, Williams %R).

Key Changes from v2:
1. Harsher volume gate (0.5x penalty for low volume)
2. Harsher ADX penalty (0.5x for ADX > 40)
3. Tightened RSI thresholds (< 25 for max score)
4. Added Price vs SMA50 (mid-term trend)
5. Added MACD line crossover (mid-term momentum)
6. Removed: Stochastic, Consecutive days, Williams %R (too short-term)
7. Added conviction levels (HIGH/MEDIUM/LOW)

Drop-in replacement for existing scoring functions.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class DivergenceType(Enum):
    NONE = "none"
    BULLISH = "bullish"
    BEARISH = "bearish"


class ConvictionLevel(Enum):
    HIGH = "HIGH"       # Score >= 8.0, volume >= 1.2x, ADX < 35 → BUY NOW
    MEDIUM = "MEDIUM"   # Score >= 7.0, volume >= 1.0x → Developing
    LOW = "LOW"         # Score >= 6.0 → Not actionable
    NONE = "NONE"       # Below thresholds


@dataclass
class DivergenceResult:
    type: DivergenceType
    strength: float  # Magnitude of RSI/OBV divergence
    description: str


@dataclass
class ReversalScore:
    raw_score: float          # Before multipliers
    final_score: float        # After multipliers
    volume_multiplier: float  # Volume gate multiplier
    volume_ratio: float       # Actual volume ratio for conviction check
    adx_multiplier: float
    adx_value: float          # Actual ADX for conviction check
    components: Dict[str, float]
    divergence: DivergenceResult
    conviction: ConvictionLevel  # NEW: conviction level


# =============================================================================
# VOLUME GATE (HARSH)
# =============================================================================

def get_volume_multiplier(df: pd.DataFrame) -> Tuple[float, float]:
    """
    Harsh volume gate: Returns (multiplier, ratio).

    - Volume >= 2.0x avg: 1.2x bonus (strong confirmation)
    - Volume >= 1.5x avg: 1.1x bonus (good volume)
    - Volume >= 1.0x avg: 1.0x (neutral)
    - Volume >= 0.8x avg: 0.7x penalty (weak)
    - Volume < 0.8x avg: 0.5x penalty (no conviction - halve score)
    """
    if 'volume' not in df.columns:
        return 1.0, 1.0

    current_volume = df['volume'].iloc[-1]
    avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]

    # Handle missing volume data - default to neutral
    if pd.isna(current_volume) or pd.isna(avg_volume) or avg_volume == 0:
        return 1.0, 1.0

    ratio = current_volume / avg_volume

    if ratio >= 2.0:
        return 1.2, ratio  # Strong confirmation
    elif ratio >= 1.5:
        return 1.1, ratio  # Good volume
    elif ratio >= 1.0:
        return 1.0, ratio  # Neutral
    elif ratio >= 0.8:
        return 0.7, ratio  # Weak - significant penalty
    else:
        return 0.5, ratio  # No conviction - halve the score


def get_volume_ratio(df: pd.DataFrame) -> float:
    """Returns current volume / 20-day average volume."""
    if 'volume' not in df.columns:
        return 1.0

    current_volume = df['volume'].iloc[-1]
    avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]

    # Handle missing volume data - default to neutral
    if pd.isna(current_volume) or pd.isna(avg_volume) or avg_volume == 0:
        return 1.0

    return current_volume / avg_volume


# =============================================================================
# ADX REGIME MULTIPLIER (HARSH)
# =============================================================================

def get_adx_multiplier(adx_value: float) -> Tuple[float, float]:
    """
    Harsh ADX-based regime modifier. Returns (multiplier, adx_value).

    For REVERSAL signals (mean reversion):
        - ADX < 20: Weak trend, mean reversion favored → 1.15x boost
        - ADX 20-30: Moderate trend → 1.0x (neutral)
        - ADX 30-40: Strong trend → 0.7x penalty (30%)
        - ADX > 40: Very strong trend → 0.5x penalty (50% - fighting freight train)
    """
    if pd.isna(adx_value):
        return 1.0, 25.0  # Default to neutral ADX

    if adx_value < 20:
        return 1.15, adx_value  # Range-bound = mean reversion boost
    elif adx_value <= 30:
        return 1.0, adx_value   # Moderate trend = neutral
    elif adx_value <= 40:
        return 0.7, adx_value   # Strong trend = 30% penalty
    else:
        return 0.5, adx_value   # Very strong trend = 50% penalty


# =============================================================================
# ENHANCED DIVERGENCE DETECTION
# =============================================================================

def find_swing_lows(series: pd.Series) -> pd.Series:
    """Find local minima (swing lows) in a price series."""
    swing_lows = series[(series.shift(1) > series) & (series.shift(-1) > series)]
    return swing_lows


def find_swing_highs(series: pd.Series) -> pd.Series:
    """Find local maxima (swing highs) in a price series."""
    swing_highs = series[(series.shift(1) < series) & (series.shift(-1) < series)]
    return swing_highs


def detect_divergence_enhanced(
    df: pd.DataFrame,
    lookback: int = 20,  # Increased from 14 for mid-term
    indicator: str = "RSI"
) -> DivergenceResult:
    """
    Enhanced divergence detection using actual swing points.

    Bullish divergence: Price makes lower low, indicator makes higher low
    Bearish divergence: Price makes higher high, indicator makes lower high
    """
    if len(df) < lookback:
        return DivergenceResult(DivergenceType.NONE, 0.0, "Insufficient data")

    window = df.iloc[-lookback:]
    prices = window['close']

    ind_col = 'RSI' if indicator == "RSI" else ('OBV' if indicator == "OBV" else indicator)

    if ind_col not in window.columns:
        return DivergenceResult(DivergenceType.NONE, 0.0, f"{indicator} not available")

    ind_series = window[ind_col]

    # Find swing lows for bullish divergence
    price_lows = find_swing_lows(prices)

    if len(price_lows) >= 2:
        p1_idx, p2_idx = price_lows.index[-2], price_lows.index[-1]
        p1, p2 = price_lows.iloc[-2], price_lows.iloc[-1]

        r1 = ind_series.loc[p1_idx] if p1_idx in ind_series.index else None
        r2 = ind_series.loc[p2_idx] if p2_idx in ind_series.index else None

        if r1 is not None and r2 is not None:
            if p2 < p1 and r2 > r1:
                strength = abs(r2 - r1)
                pct_price_drop = ((p1 - p2) / p1) * 100 if p1 != 0 else 0
                return DivergenceResult(
                    DivergenceType.BULLISH,
                    strength,
                    f"Bullish: Price -{pct_price_drop:.1f}%, {indicator} +{strength:.1f}"
                )

    # Find swing highs for bearish divergence
    price_highs = find_swing_highs(prices)

    if len(price_highs) >= 2:
        p1_idx, p2_idx = price_highs.index[-2], price_highs.index[-1]
        p1, p2 = price_highs.iloc[-2], price_highs.iloc[-1]

        r1 = ind_series.loc[p1_idx] if p1_idx in ind_series.index else None
        r2 = ind_series.loc[p2_idx] if p2_idx in ind_series.index else None

        if r1 is not None and r2 is not None:
            if p2 > p1 and r2 < r1:
                strength = abs(r1 - r2)
                pct_price_rise = ((p2 - p1) / p1) * 100 if p1 != 0 else 0
                return DivergenceResult(
                    DivergenceType.BEARISH,
                    strength,
                    f"Bearish: Price +{pct_price_rise:.1f}%, {indicator} -{strength:.1f}"
                )

    return DivergenceResult(DivergenceType.NONE, 0.0, "No divergence detected")


def detect_combined_divergence(df: pd.DataFrame, lookback: int = 20) -> DivergenceResult:
    """
    Check both RSI and OBV for divergence.
    Returns stronger signal if both agree (1.5x confluence bonus).
    """
    rsi_div = detect_divergence_enhanced(df, lookback, "RSI")
    obv_div = detect_divergence_enhanced(df, lookback, "OBV")

    # Both bullish - confluence bonus
    if rsi_div.type == DivergenceType.BULLISH and obv_div.type == DivergenceType.BULLISH:
        combined_strength = (rsi_div.strength + obv_div.strength) / 2
        return DivergenceResult(
            DivergenceType.BULLISH,
            combined_strength * 1.5,
            "STRONG Bullish (RSI + OBV confirmed)"
        )

    # Both bearish - confluence bonus
    if rsi_div.type == DivergenceType.BEARISH and obv_div.type == DivergenceType.BEARISH:
        combined_strength = (rsi_div.strength + obv_div.strength) / 2
        return DivergenceResult(
            DivergenceType.BEARISH,
            combined_strength * 1.5,
            "STRONG Bearish (RSI + OBV confirmed)"
        )

    # Single signal
    if rsi_div.type != DivergenceType.NONE:
        return rsi_div
    if obv_div.type != DivergenceType.NONE:
        return obv_div

    return DivergenceResult(DivergenceType.NONE, 0.0, "No divergence")


# =============================================================================
# COMPONENT SCORING FUNCTIONS (TIGHTENED)
# =============================================================================

def score_rsi(rsi: float, direction: str = "up") -> float:
    """
    RSI component scoring — TIGHTENED thresholds.

    Upside: Only truly oversold gets high scores.
    < 25 → 10 (extreme oversold)
    < 30 → 7  (oversold)
    < 35 → 4  (approaching oversold)
    else → 1  (not oversold - near zero contribution)
    """
    if pd.isna(rsi):
        return 1.0  # Unknown = no contribution

    if direction == "up":
        if rsi < 25:
            return 10.0  # Extreme oversold
        elif rsi < 30:
            return 7.0   # Oversold
        elif rsi < 35:
            return 4.0   # Approaching
        else:
            return 1.0   # Not oversold
    else:  # downside
        if rsi > 75:
            return 10.0  # Extreme overbought
        elif rsi > 70:
            return 7.0   # Overbought
        elif rsi > 65:
            return 4.0   # Approaching
        else:
            return 1.0   # Not overbought


def score_macd_crossover(
    macd_line: float,
    signal_line: float,
    prev_macd: float,
    prev_signal: float,
    direction: str = "up"
) -> float:
    """
    MACD line crossover scoring — mid-term momentum shift.

    Bullish crossover: MACD crosses above signal line
    Bearish crossover: MACD crosses below signal line
    """
    if pd.isna(macd_line) or pd.isna(signal_line):
        return 1.0

    if direction == "up":
        # Bullish crossover
        if prev_macd is not None and not pd.isna(prev_macd) and not pd.isna(prev_signal):
            if prev_macd < prev_signal and macd_line > signal_line:
                return 10.0  # Fresh bullish crossover

        # Already above signal (bullish)
        if macd_line > signal_line:
            return 6.0

        # Below signal but narrowing
        if macd_line < signal_line and prev_macd is not None:
            if not pd.isna(prev_macd) and (macd_line - signal_line) > (prev_macd - prev_signal):
                return 4.0

        return 1.0  # Bearish MACD
    else:  # downside
        # Bearish crossover
        if prev_macd is not None and not pd.isna(prev_macd) and not pd.isna(prev_signal):
            if prev_macd > prev_signal and macd_line < signal_line:
                return 10.0  # Fresh bearish crossover

        # Already below signal (bearish)
        if macd_line < signal_line:
            return 6.0

        return 1.0


def score_macd_histogram(hist: float, prev_hist: float, direction: str = "up") -> float:
    """MACD histogram component — momentum direction."""
    if pd.isna(hist):
        return 1.0

    if direction == "up":
        if prev_hist is not None and not pd.isna(prev_hist) and prev_hist < 0 and hist > 0:
            return 10.0  # Negative to positive flip
        elif hist < 0 and prev_hist is not None and not pd.isna(prev_hist) and hist > prev_hist:
            return 5.0   # Narrowing negative
        elif hist > 0:
            return 6.0   # Positive histogram
        else:
            return 1.0   # Widening negative
    else:  # downside
        if prev_hist is not None and not pd.isna(prev_hist) and prev_hist > 0 and hist < 0:
            return 10.0  # Positive to negative flip
        elif hist > 0 and prev_hist is not None and not pd.isna(prev_hist) and hist < prev_hist:
            return 5.0   # Narrowing positive
        elif hist < 0:
            return 6.0   # Negative histogram
        else:
            return 1.0   # Widening positive


def score_price_vs_sma50(
    close: float,
    sma50: float,
    prev_close: float,
    prev_sma50: float,
    direction: str = "up"
) -> float:
    """
    Price vs SMA50 — mid-term trend indicator.
    """
    if pd.isna(sma50) or sma50 == 0:
        return 1.0

    pct_diff = ((close - sma50) / sma50) * 100

    if direction == "up":
        # Crossed above SMA50 (bullish)
        crossed_above = (
            prev_close is not None
            and not pd.isna(prev_close)
            and prev_sma50 is not None
            and not pd.isna(prev_sma50)
            and prev_close < prev_sma50
            and close > sma50
        )
        if crossed_above:
            return 10.0  # Bullish cross
        elif close > sma50:
            return 7.0   # Above SMA50
        elif pct_diff >= -3:
            return 4.0   # Within 3% below
        else:
            return 1.0   # Well below
    else:  # downside
        crossed_below = (
            prev_close is not None
            and not pd.isna(prev_close)
            and prev_sma50 is not None
            and not pd.isna(prev_sma50)
            and prev_close > prev_sma50
            and close < sma50
        )
        if crossed_below:
            return 10.0
        elif pct_diff > 15:
            return 7.0   # Extended above
        elif pct_diff > 5:
            return 4.0
        else:
            return 1.0


def score_price_vs_sma200(
    close: float,
    sma200: float,
    prev_close: float,
    prev_sma200: float,
    direction: str = "up"
) -> float:
    """
    Price vs SMA200 — long-term trend indicator.
    """
    if pd.isna(sma200) or sma200 == 0:
        return 1.0

    pct_diff = ((close - sma200) / sma200) * 100

    if direction == "up":
        crossed_above = (
            prev_close is not None
            and not pd.isna(prev_close)
            and prev_sma200 is not None
            and not pd.isna(prev_sma200)
            and prev_close < prev_sma200
            and close > sma200
        )
        if crossed_above:
            return 10.0  # Major bullish event
        elif close > sma200:
            return 7.0   # Above long-term trend
        elif pct_diff >= -5:
            return 4.0   # Within 5% below
        else:
            return 1.0   # Well below
    else:  # downside
        crossed_below = (
            prev_close is not None
            and not pd.isna(prev_close)
            and prev_sma200 is not None
            and not pd.isna(prev_sma200)
            and prev_close > prev_sma200
            and close < sma200
        )
        if crossed_below:
            return 10.0  # Major bearish event
        elif pct_diff > 20:
            return 7.0   # Extended above
        elif pct_diff > 10:
            return 4.0
        else:
            return 1.0


def score_volume_spike(volume_ratio: float) -> float:
    """
    Volume spike component — TIGHTENED.
    Requires higher volume for good scores.
    """
    if volume_ratio >= 2.0:
        return 10.0  # Strong volume confirmation
    elif volume_ratio >= 1.5:
        return 7.0   # Good volume
    elif volume_ratio >= 1.2:
        return 5.0   # Above average
    elif volume_ratio >= 1.0:
        return 3.0   # Average
    else:
        return 1.0   # Below average


def score_divergence(divergence: DivergenceResult, expected_type: DivergenceType) -> float:
    """Divergence component scoring."""
    if divergence.type == expected_type:
        base_score = min(10.0, 7.0 + (divergence.strength / 10.0))
        return base_score
    return 1.0  # No divergence = minimal contribution


# =============================================================================
# WEIGHTS V3 — MID/LONG TERM FOCUS
# =============================================================================

WEIGHTS_V3 = {
    'rsi': 0.15,           # Momentum context
    'macd_crossover': 0.15, # Mid-term momentum shift
    'macd_hist': 0.10,     # Momentum direction
    'price_sma50': 0.15,   # Mid-term trend
    'price_sma200': 0.20,  # Long-term trend (the big one)
    'volume': 0.15,        # Confirmation (critical)
    'divergence': 0.10,    # Quality signal when present
}

# Keep old weights for backward compatibility
WEIGHTS_V2 = WEIGHTS_V3


# =============================================================================
# CONVICTION LEVEL CLASSIFICATION
# =============================================================================

def classify_conviction(
    final_score: float,
    volume_ratio: float,
    adx_value: float
) -> ConvictionLevel:
    """
    Classify conviction level for actionability.

    HIGH: Score >= 8.0 AND volume >= 1.2x AND ADX < 35 → BUY NOW
    MEDIUM: Score >= 7.0 AND volume >= 1.0x → Developing, watch closely
    LOW: Score >= 6.0 → Not actionable
    NONE: Below thresholds
    """
    if final_score >= 8.0 and volume_ratio >= 1.2 and adx_value < 35:
        return ConvictionLevel.HIGH
    elif final_score >= 7.0 and volume_ratio >= 1.0:
        return ConvictionLevel.MEDIUM
    elif final_score >= 6.0:
        return ConvictionLevel.LOW
    return ConvictionLevel.NONE


# =============================================================================
# MAIN SCORING FUNCTIONS
# =============================================================================

def calculate_upside_reversal_score_v2(df: pd.DataFrame) -> ReversalScore:
    """
    Calculate upside reversal score with v3 enhancements.
    (Function name kept for backward compatibility)
    """
    if df is None or len(df) < 50:
        return ReversalScore(
            raw_score=0.0, final_score=0.0, volume_multiplier=1.0,
            volume_ratio=1.0, adx_multiplier=1.0, adx_value=25.0,
            components={}, conviction=ConvictionLevel.NONE,
            divergence=DivergenceResult(DivergenceType.NONE, 0.0, "Insufficient data")
        )

    current = df.iloc[-1]
    prev = df.iloc[-2]

    # Divergence (with extended lookback for mid-term)
    divergence = detect_combined_divergence(df, lookback=20)

    # Volume ratio
    volume_mult, volume_ratio = get_volume_multiplier(df)

    # ADX
    adx_mult, adx_value = get_adx_multiplier(current.get('ADX'))

    # Score components (mid/long term focus)
    components = {
        'rsi': score_rsi(current.get('RSI'), "up"),
        'macd_crossover': score_macd_crossover(
            current.get('MACD'), current.get('MACD_SIGNAL'),
            prev.get('MACD'), prev.get('MACD_SIGNAL'), "up"
        ),
        'macd_hist': score_macd_histogram(
            current.get('MACD_HIST'), prev.get('MACD_HIST'), "up"
        ),
        'price_sma50': score_price_vs_sma50(
            current['close'], current.get('SMA_50'),
            prev['close'], prev.get('SMA_50'), "up"
        ),
        'price_sma200': score_price_vs_sma200(
            current['close'], current.get('SMA_200'),
            prev['close'], prev.get('SMA_200'), "up"
        ),
        'volume': score_volume_spike(volume_ratio),
        'divergence': score_divergence(divergence, DivergenceType.BULLISH),
    }

    # Weighted raw score
    raw_score = sum(components[k] * WEIGHTS_V3[k] for k in components)

    # Apply multipliers
    final_score = min(10.0, raw_score * volume_mult * adx_mult)

    # Classify conviction
    conviction = classify_conviction(final_score, volume_ratio, adx_value)

    return ReversalScore(
        raw_score=round(raw_score, 2),
        final_score=round(final_score, 2),
        volume_multiplier=volume_mult,
        volume_ratio=round(volume_ratio, 2),
        adx_multiplier=adx_mult,
        adx_value=round(adx_value, 1),
        components={k: round(v, 1) for k, v in components.items()},
        divergence=divergence,
        conviction=conviction
    )


def calculate_downside_reversal_score_v2(df: pd.DataFrame) -> ReversalScore:
    """
    Calculate downside reversal score with v3 enhancements.
    (Function name kept for backward compatibility)
    """
    if df is None or len(df) < 50:
        return ReversalScore(
            raw_score=0.0, final_score=0.0, volume_multiplier=1.0,
            volume_ratio=1.0, adx_multiplier=1.0, adx_value=25.0,
            components={}, conviction=ConvictionLevel.NONE,
            divergence=DivergenceResult(DivergenceType.NONE, 0.0, "Insufficient data")
        )

    current = df.iloc[-1]
    prev = df.iloc[-2]

    divergence = detect_combined_divergence(df, lookback=20)
    volume_mult, volume_ratio = get_volume_multiplier(df)
    adx_mult, adx_value = get_adx_multiplier(current.get('ADX'))

    components = {
        'rsi': score_rsi(current.get('RSI'), "down"),
        'macd_crossover': score_macd_crossover(
            current.get('MACD'), current.get('MACD_SIGNAL'),
            prev.get('MACD'), prev.get('MACD_SIGNAL'), "down"
        ),
        'macd_hist': score_macd_histogram(
            current.get('MACD_HIST'), prev.get('MACD_HIST'), "down"
        ),
        'price_sma50': score_price_vs_sma50(
            current['close'], current.get('SMA_50'),
            prev['close'], prev.get('SMA_50'), "down"
        ),
        'price_sma200': score_price_vs_sma200(
            current['close'], current.get('SMA_200'),
            prev['close'], prev.get('SMA_200'), "down"
        ),
        'volume': score_volume_spike(volume_ratio),
        'divergence': score_divergence(divergence, DivergenceType.BEARISH),
    }

    raw_score = sum(components[k] * WEIGHTS_V3[k] for k in components)
    final_score = min(10.0, raw_score * volume_mult * adx_mult)
    conviction = classify_conviction(final_score, volume_ratio, adx_value)

    return ReversalScore(
        raw_score=round(raw_score, 2),
        final_score=round(final_score, 2),
        volume_multiplier=volume_mult,
        volume_ratio=round(volume_ratio, 2),
        adx_multiplier=adx_mult,
        adx_value=round(adx_value, 1),
        components={k: round(v, 1) for k, v in components.items()},
        divergence=divergence,
        conviction=conviction
    )


def format_score_report(score: ReversalScore, ticker: str, direction: str) -> str:
    """Generate human-readable score breakdown."""
    emoji = "🟢 UPSIDE" if direction == "up" else "🔴 DOWNSIDE"
    conviction_emoji = {
        ConvictionLevel.HIGH: "🔥 HIGH",
        ConvictionLevel.MEDIUM: "⚡ MEDIUM",
        ConvictionLevel.LOW: "💤 LOW",
        ConvictionLevel.NONE: "❌ NONE",
    }

    lines = [
        f"{emoji} REVERSAL — {ticker}",
        f"{'=' * 50}",
        f"Final Score: {score.final_score}/10",
        f"Conviction: {conviction_emoji.get(score.conviction, '?')}",
        f"Raw: {score.raw_score} × Vol({score.volume_multiplier}) × ADX({score.adx_multiplier})",
        f"Volume: {score.volume_ratio}x avg | ADX: {score.adx_value}",
        "",
        "Components:",
    ]

    for component, value in score.components.items():
        weight = WEIGHTS_V3.get(component, 0) * 100
        lines.append(f"  {component:15} {value:4.1f}/10  ({weight:.0f}%)")

    if score.divergence.type != DivergenceType.NONE:
        lines.append("")
        lines.append(f"Divergence: {score.divergence.description}")

    return "\n".join(lines)
