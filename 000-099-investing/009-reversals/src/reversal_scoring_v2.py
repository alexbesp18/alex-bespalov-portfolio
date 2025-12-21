"""
Reversal Scoring v2 — Enhanced Signal Logic
============================================
Integrations:
1. Volume gate (soft: reduces score if <1.2x, doesn't zero it)
2. ADX regime multiplier (gentler: 0.85x instead of 0.8x)
3. Williams %R in scoring weights
4. Enhanced swing-based divergence detection

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


@dataclass
class DivergenceResult:
    type: DivergenceType
    strength: float  # Magnitude of RSI/OBV divergence
    description: str


@dataclass
class ReversalScore:
    raw_score: float          # Before ADX multiplier
    final_score: float        # After ADX multiplier
    volume_multiplier: float  # Soft volume gate multiplier
    adx_multiplier: float
    components: Dict[str, float]
    divergence: DivergenceResult


# =============================================================================
# VOLUME GATE (SOFT)
# =============================================================================

def get_volume_multiplier(df: pd.DataFrame, threshold: float = 1.2) -> float:
    """
    Soft volume gate: Returns multiplier instead of hard pass/fail.
    
    - Volume >= 2.0x avg: 1.1x bonus
    - Volume >= 1.2x avg: 1.0x (neutral)
    - Volume >= 0.8x avg: 0.9x mild penalty
    - Volume < 0.8x avg: 0.75x penalty (low conviction)
    """
    if 'volume' not in df.columns:
        return 1.0
    
    current_volume = df['volume'].iloc[-1]
    avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
    
    if pd.isna(avg_volume) or avg_volume == 0:
        return 1.0
    
    ratio = current_volume / avg_volume
    
    if ratio >= 2.0:
        return 1.1  # High volume confirmation
    elif ratio >= threshold:
        return 1.0  # Normal
    elif ratio >= 0.8:
        return 0.9  # Slightly low
    else:
        return 0.75  # Very low volume = reduced conviction


def get_volume_ratio(df: pd.DataFrame) -> float:
    """Returns current volume / 20-day average volume."""
    if 'volume' not in df.columns:
        return 1.0
    
    current_volume = df['volume'].iloc[-1]
    avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
    
    if pd.isna(avg_volume) or avg_volume == 0:
        return 1.0
    
    return current_volume / avg_volume


# =============================================================================
# ADX REGIME MULTIPLIER (GENTLER)
# =============================================================================

def get_adx_multiplier(adx_value: float, signal_type: str = "reversal") -> float:
    """
    ADX-based regime modifier (gentler version).
    
    For REVERSAL signals (mean reversion):
        - ADX < 20: Weak trend, mean reversion favored → 1.1x boost
        - ADX 20-30: Moderate trend → 1.0x (neutral)
        - ADX > 30: Strong trend, fighting momentum → 0.85x penalty (was 0.8x)
    """
    if pd.isna(adx_value):
        return 1.0
    
    if signal_type == "reversal":
        if adx_value < 20:
            return 1.1  # Weak trend = mean reversion friendly
        elif adx_value <= 30:
            return 1.0  # Moderate trend = neutral
        else:
            return 0.85  # Strong trend = reversal is fighting momentum (gentler)
    
    return 1.0


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
    lookback: int = 14,
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


def detect_combined_divergence(df: pd.DataFrame, lookback: int = 14) -> DivergenceResult:
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
# COMPONENT SCORING FUNCTIONS
# =============================================================================

def score_rsi(rsi: float, direction: str = "up") -> float:
    """RSI component scoring."""
    if pd.isna(rsi):
        return 5.0
    
    if direction == "up":
        if rsi < 30:
            return 10.0
        elif rsi < 40:
            return 7.0
        elif rsi < 50:
            return 5.0
        else:
            return 2.0
    else:  # downside
        if rsi > 70:
            return 10.0
        elif rsi > 60:
            return 7.0
        elif rsi > 50:
            return 5.0
        else:
            return 2.0


def score_stochastic(k: float, d: float, prev_k: float, direction: str = "up") -> float:
    """Stochastic component with crossover detection."""
    if pd.isna(k) or pd.isna(d):
        return 5.0
    
    if direction == "up":
        bullish_cross = prev_k is not None and not pd.isna(prev_k) and prev_k < d and k > d
        if k < 20 and bullish_cross:
            return 10.0
        elif k < 20:
            return 7.0
        elif k < 30:
            return 5.0
        else:
            return 2.0
    else:  # downside
        bearish_cross = prev_k is not None and not pd.isna(prev_k) and prev_k > d and k < d
        if k > 80 and bearish_cross:
            return 10.0
        elif k > 80:
            return 7.0
        elif k > 70:
            return 5.0
        else:
            return 2.0


def score_macd_histogram(hist: float, prev_hist: float, direction: str = "up") -> float:
    """MACD histogram component."""
    if pd.isna(hist):
        return 5.0
    
    if direction == "up":
        if prev_hist is not None and not pd.isna(prev_hist) and prev_hist < 0 and hist > 0:
            return 10.0  # Negative to positive flip
        elif hist < 0 and prev_hist is not None and not pd.isna(prev_hist) and hist > prev_hist:
            return 5.0  # Narrowing negative
        elif hist < 0:
            return 2.0  # Widening negative
        else:
            return 5.0
    else:  # downside
        if prev_hist is not None and not pd.isna(prev_hist) and prev_hist > 0 and hist < 0:
            return 10.0  # Positive to negative flip
        elif hist > 0 and prev_hist is not None and not pd.isna(prev_hist) and hist < prev_hist:
            return 5.0  # Narrowing positive
        elif hist > 0:
            return 2.0  # Widening positive
        else:
            return 5.0


def score_price_vs_sma200(close: float, sma200: float, prev_close: float, prev_sma200: float, direction: str = "up") -> float:
    """Price vs SMA200 component."""
    if pd.isna(sma200) or sma200 == 0:
        return 5.0
    
    pct_diff = ((close - sma200) / sma200) * 100
    
    if direction == "up":
        crossed_above = prev_close is not None and not pd.isna(prev_close) and prev_close < prev_sma200 and close > sma200
        if crossed_above:
            return 10.0
        elif close > sma200:
            return 7.0
        elif pct_diff >= -3:
            return 5.0
        else:
            return 2.0
    else:  # downside
        crossed_below = prev_close is not None and not pd.isna(prev_close) and prev_close > prev_sma200 and close < sma200
        if crossed_below:
            return 10.0
        elif pct_diff > 20:
            return 7.0  # Extended above
        elif pct_diff > 10:
            return 5.0
        else:
            return 2.0


def score_volume_spike(volume_ratio: float) -> float:
    """Volume spike component (separate from gate)."""
    if volume_ratio >= 2.0:
        return 10.0
    elif volume_ratio >= 1.5:
        return 5.0
    else:
        return 2.0


def score_williams_r(williams_r: float, direction: str = "up") -> float:
    """Williams %R component."""
    if pd.isna(williams_r):
        return 5.0
    
    if direction == "up":
        if williams_r < -80:
            return 10.0
        elif williams_r < -50:
            return 5.0
        else:
            return 2.0
    else:  # downside
        if williams_r > -20:
            return 10.0
        elif williams_r > -50:
            return 5.0
        else:
            return 2.0


def score_divergence(divergence: DivergenceResult, expected_type: DivergenceType) -> float:
    """Divergence component scoring."""
    if divergence.type == expected_type:
        base_score = min(10.0, 7.0 + (divergence.strength / 10.0))
        return base_score
    return 2.0


def score_consecutive_days(df: pd.DataFrame, direction: str = "red") -> float:
    """Count consecutive red/green days using close vs prev close."""
    if len(df) < 5:
        return 2.0
    
    count = 0
    closes = df['close'].values
    
    for i in range(-1, -min(10, len(df)), -1):
        prev_close = closes[i - 1] if abs(i - 1) <= len(df) else None
        if prev_close is None:
            break
        
        if direction == "red":
            if closes[i] < prev_close:
                count += 1
            else:
                break
        else:  # green
            if closes[i] > prev_close:
                count += 1
            else:
                break
    
    if count >= 5:
        return 10.0
    elif count >= 3:
        return 5.0
    else:
        return 2.0


# =============================================================================
# WEIGHTS V2
# =============================================================================

WEIGHTS_V2 = {
    'rsi': 0.20,
    'stochastic': 0.15,
    'macd_hist': 0.15,
    'price_sma200': 0.15,
    'volume': 0.10,
    'divergence': 0.15,
    'consecutive': 0.05,
    'williams_r': 0.05,
}


# =============================================================================
# MAIN SCORING FUNCTIONS
# =============================================================================

def calculate_upside_reversal_score_v2(df: pd.DataFrame) -> ReversalScore:
    """
    Calculate upside reversal score with v2 enhancements.
    """
    if df is None or len(df) < 50:
        return ReversalScore(
            raw_score=0.0, final_score=0.0, volume_multiplier=1.0,
            adx_multiplier=1.0, components={},
            divergence=DivergenceResult(DivergenceType.NONE, 0.0, "Insufficient data")
        )
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Divergence
    divergence = detect_combined_divergence(df, lookback=14)
    
    # Volume ratio
    volume_ratio = get_volume_ratio(df)
    
    # Score components
    components = {
        'rsi': score_rsi(current.get('RSI'), "up"),
        'stochastic': score_stochastic(
            current.get('STOCH_K'), current.get('STOCH_D'),
            prev.get('STOCH_K'), "up"
        ),
        'macd_hist': score_macd_histogram(
            current.get('MACD_HIST'), prev.get('MACD_HIST'), "up"
        ),
        'price_sma200': score_price_vs_sma200(
            current['close'], current.get('SMA_200'),
            prev['close'], prev.get('SMA_200'), "up"
        ),
        'volume': score_volume_spike(volume_ratio),
        'divergence': score_divergence(divergence, DivergenceType.BULLISH),
        'consecutive': score_consecutive_days(df, "red"),
        'williams_r': score_williams_r(current.get('WILLIAMS_R'), "up"),
    }
    
    # Weighted raw score
    raw_score = sum(components[k] * WEIGHTS_V2[k] for k in components)
    
    # Multipliers
    volume_mult = get_volume_multiplier(df)
    adx_mult = get_adx_multiplier(current.get('ADX'), "reversal")
    
    final_score = min(10.0, raw_score * volume_mult * adx_mult)
    
    return ReversalScore(
        raw_score=round(raw_score, 2),
        final_score=round(final_score, 2),
        volume_multiplier=volume_mult,
        adx_multiplier=adx_mult,
        components={k: round(v, 1) for k, v in components.items()},
        divergence=divergence
    )


def calculate_downside_reversal_score_v2(df: pd.DataFrame) -> ReversalScore:
    """
    Calculate downside reversal score with v2 enhancements.
    """
    if df is None or len(df) < 50:
        return ReversalScore(
            raw_score=0.0, final_score=0.0, volume_multiplier=1.0,
            adx_multiplier=1.0, components={},
            divergence=DivergenceResult(DivergenceType.NONE, 0.0, "Insufficient data")
        )
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    
    divergence = detect_combined_divergence(df, lookback=14)
    volume_ratio = get_volume_ratio(df)
    
    components = {
        'rsi': score_rsi(current.get('RSI'), "down"),
        'stochastic': score_stochastic(
            current.get('STOCH_K'), current.get('STOCH_D'),
            prev.get('STOCH_K'), "down"
        ),
        'macd_hist': score_macd_histogram(
            current.get('MACD_HIST'), prev.get('MACD_HIST'), "down"
        ),
        'price_sma200': score_price_vs_sma200(
            current['close'], current.get('SMA_200'),
            prev['close'], prev.get('SMA_200'), "down"
        ),
        'volume': score_volume_spike(volume_ratio),
        'divergence': score_divergence(divergence, DivergenceType.BEARISH),
        'consecutive': score_consecutive_days(df, "green"),
        'williams_r': score_williams_r(current.get('WILLIAMS_R'), "down"),
    }
    
    raw_score = sum(components[k] * WEIGHTS_V2[k] for k in components)
    
    volume_mult = get_volume_multiplier(df)
    adx_mult = get_adx_multiplier(current.get('ADX'), "reversal")
    
    final_score = min(10.0, raw_score * volume_mult * adx_mult)
    
    return ReversalScore(
        raw_score=round(raw_score, 2),
        final_score=round(final_score, 2),
        volume_multiplier=volume_mult,
        adx_multiplier=adx_mult,
        components={k: round(v, 1) for k, v in components.items()},
        divergence=divergence
    )


def format_score_report(score: ReversalScore, ticker: str, direction: str) -> str:
    """Generate human-readable score breakdown."""
    emoji = "🟢 UPSIDE" if direction == "up" else "🔴 DOWNSIDE"
    lines = [
        f"{emoji} REVERSAL — {ticker}",
        f"{'=' * 50}",
        f"Final Score: {score.final_score}/10",
        f"Raw: {score.raw_score} × Vol({score.volume_multiplier}) × ADX({score.adx_multiplier})",
        "",
        "Components:",
    ]
    
    for component, value in score.components.items():
        weight = WEIGHTS_V2.get(component, 0) * 100
        lines.append(f"  {component:15} {value:4.1f}/10  ({weight:.0f}%)")
    
    if score.divergence.type != DivergenceType.NONE:
        lines.append("")
        lines.append(f"Divergence: {score.divergence.description}")
    
    return "\n".join(lines)
