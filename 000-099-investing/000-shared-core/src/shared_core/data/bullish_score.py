"""
Bullish score calculation.

Computes a 1-10 bullish score based on trend, momentum, and volume indicators.
"""

import pandas as pd
from typing import Dict, Tuple

from ..scoring.weights import BULLISH_WEIGHTS
from ..scoring.models import BullishScore


def calculate_bullish_score(df: pd.DataFrame) -> Tuple[float, Dict[str, float]]:
    """
    Compute 1-10 bullish score based on the latest row.

    Weights:
    - TREND DIRECTION (25%): Price vs SMA50/SMA200
    - MA STACK (20%): 20>50>200=10, Mixed=5, Bearish=2
    - MACD HISTOGRAM (15%): Positive+expanding=10, Negative=2
    - RSI POSITION (15%): 50-70=10, 30-50=6, extremes=4
    - OBV TREND (15%): UP=10, SIDEWAYS=5, DOWN=2
    - ADX STRENGTH (10%): >25=10, 20-25=7, <20=4

    Args:
        df: DataFrame with calculated indicators

    Returns:
        Tuple of (score, breakdown_dict)

    Example:
        >>> score, breakdown = calculate_bullish_score(df)
        >>> print(f"Score: {score}, Trend: {breakdown['trend']}")
    """
    if df is None or len(df) < 50:
        return 0.0, {}

    curr = df.iloc[-1]
    prev = df.iloc[-2]

    score = 0.0
    breakdown: Dict[str, float] = {}

    # 1. Trend Direction (25%)
    trend_score = 2.0
    sma50 = curr.get('SMA_50', 0) or 0
    sma200 = curr.get('SMA_200', 0) or 0

    if curr['close'] > sma50 and sma50 > sma200:
        trend_score = 10.0  # Strong Up
    elif curr['close'] > sma200:
        trend_score = 8.0   # Up
    elif curr['close'] > sma50:
        trend_score = 5.0   # Sideways/Recovering

    score += trend_score * BULLISH_WEIGHTS['trend']
    breakdown['trend'] = trend_score

    # 2. MA Stack (20%)
    ma_score = 2.0
    sma20 = curr.get('SMA_20', 0) or 0

    if sma20 > sma50 and sma50 > sma200:
        ma_score = 10.0
    elif sma20 > sma50 or sma50 > sma200:
        ma_score = 5.0

    score += ma_score * BULLISH_WEIGHTS['ma_stack']
    breakdown['ma_stack'] = ma_score

    # 3. MACD Histogram (15%)
    macd_score = 2.0
    curr_hist = curr.get('MACD_HIST', 0) or 0
    prev_hist = prev.get('MACD_HIST', 0) or 0

    if curr_hist > 0:
        if curr_hist > prev_hist:
            macd_score = 10.0  # Positive and expanding
        else:
            macd_score = 8.0   # Positive but narrowing
    else:
        if curr_hist > prev_hist:
            macd_score = 5.0   # Negative but improving

    score += macd_score * BULLISH_WEIGHTS['macd']
    breakdown['macd'] = macd_score

    # 4. RSI Position (15%)
    rsi_score = 4.0
    rsi = curr.get('RSI', 50) or 50

    if 50 <= rsi <= 70:
        rsi_score = 10.0
    elif 30 <= rsi < 50:
        rsi_score = 6.0
    elif rsi > 70:
        rsi_score = 7.0
    elif rsi < 30:
        rsi_score = 2.0

    score += rsi_score * BULLISH_WEIGHTS['rsi']
    breakdown['rsi'] = rsi_score

    # 5. OBV Trend (15%)
    obv_score = 5.0
    if len(df) >= 20 and 'OBV' in df.columns:
        obv_slope = df['OBV'].iloc[-5:].is_monotonic_increasing
        if obv_slope:
            obv_score = 10.0
        elif df['OBV'].iloc[-1] < df['OBV'].iloc[-20]:
            obv_score = 2.0

    score += obv_score * BULLISH_WEIGHTS['obv']
    breakdown['obv'] = obv_score

    # 6. ADX Strength (10%)
    adx_score = 4.0
    adx = curr.get('ADX', 0) or 0
    if adx > 25:
        adx_score = 10.0
    elif 20 <= adx <= 25:
        adx_score = 7.0

    score += adx_score * BULLISH_WEIGHTS['adx']
    breakdown['adx'] = adx_score

    return round(score, 1), breakdown


def calculate_bullish_score_detailed(df: pd.DataFrame) -> BullishScore:
    """
    Calculate bullish score with structured return type.

    Args:
        df: DataFrame with calculated indicators

    Returns:
        BullishScore object with final_score and components
    """
    score, breakdown = calculate_bullish_score(df)
    return BullishScore(final_score=score, components=breakdown)

