"""
Component scoring functions for technical analysis.

Each function takes raw indicator values and returns a score (typically 1-10).
These are building blocks for composite scoring systems.
"""

import pandas as pd
from typing import Optional

from .models import DivergenceType, DivergenceResult


# =============================================================================
# RSI SCORING
# =============================================================================

def score_rsi(rsi: float, direction: str = "up") -> float:
    """
    Score RSI value for reversal potential.

    Args:
        rsi: RSI value (0-100)
        direction: "up" for upside reversal (oversold is good),
                   "down" for downside reversal (overbought is good)

    Returns:
        Score from 1.0 to 10.0
    """
    if pd.isna(rsi):
        return 5.0

    if direction == "up":
        # Upside reversal: lower RSI = higher score
        if rsi < 30:
            return 10.0
        elif rsi < 40:
            return 7.0
        elif rsi < 50:
            return 5.0
        else:
            return 2.0
    else:
        # Downside reversal: higher RSI = higher score
        if rsi > 70:
            return 10.0
        elif rsi > 60:
            return 7.0
        elif rsi > 50:
            return 5.0
        else:
            return 2.0


def score_rsi_oversold(rsi: float) -> float:
    """
    Score RSI for oversold condition detection — TIGHTENED.

    Lower RSI indicates more oversold condition, resulting in higher score.
    Removed loose thresholds (35, 40, 50) that diluted signal quality.

    Args:
        rsi: RSI value (0-100)

    Returns:
        Score from 1.0 to 10.0
    """
    if pd.isna(rsi):
        return 0.0

    # Tightened thresholds - only truly oversold gets high scores
    thresholds = [
        (15, 10.0),  # Extreme oversold
        (20, 9.0),   # Very oversold
        (25, 7.0),   # Oversold (tightened from 8.0)
        (30, 5.0),   # Approaching oversold (tightened from 6.0)
    ]

    for threshold, score in thresholds:
        if rsi < threshold:
            return score
    return 1.0  # Not oversold


# =============================================================================
# STOCHASTIC SCORING
# =============================================================================

def score_stochastic(
    k: float,
    d: float,
    prev_k: Optional[float],
    direction: str = "up",
) -> float:
    """
    Score Stochastic oscillator with crossover detection.

    Args:
        k: Current %K value (0-100)
        d: Current %D value (0-100)
        prev_k: Previous %K value (for crossover detection)
        direction: "up" for upside reversal, "down" for downside reversal

    Returns:
        Score from 1.0 to 10.0
    """
    if pd.isna(k) or pd.isna(d):
        return 5.0

    if direction == "up":
        bullish_cross = (
            prev_k is not None
            and not pd.isna(prev_k)
            and prev_k < d
            and k > d
        )
        if k < 20 and bullish_cross:
            return 10.0
        elif k < 20:
            return 7.0
        elif k < 30:
            return 5.0
        else:
            return 2.0
    else:
        bearish_cross = (
            prev_k is not None
            and not pd.isna(prev_k)
            and prev_k > d
            and k < d
        )
        if k > 80 and bearish_cross:
            return 10.0
        elif k > 80:
            return 7.0
        elif k > 70:
            return 5.0
        else:
            return 2.0


def score_stochastic_oversold(stoch_k: float) -> float:
    """
    Score Stochastic %K for oversold condition — TIGHTENED.

    Lower %K indicates more oversold condition.
    Removed loose threshold (30) that diluted signal quality.

    Args:
        stoch_k: Stochastic %K value (0-100)

    Returns:
        Score from 1.0 to 10.0
    """
    if pd.isna(stoch_k):
        return 0.0

    # Tightened thresholds - standard oversold is < 20
    thresholds = [
        (5, 10.0),   # Extreme oversold
        (10, 9.0),   # Very oversold
        (15, 7.0),   # Oversold
        (20, 5.0),   # Approaching oversold
    ]

    for threshold, score in thresholds:
        if stoch_k < threshold:
            return score
    return 1.0  # Not oversold


# =============================================================================
# MACD SCORING
# =============================================================================

def score_macd_histogram(
    hist: float,
    prev_hist: Optional[float],
    direction: str = "up",
) -> float:
    """
    Score MACD histogram for momentum.

    Args:
        hist: Current MACD histogram value
        prev_hist: Previous MACD histogram value
        direction: "up" for upside reversal, "down" for downside reversal

    Returns:
        Score from 1.0 to 10.0
    """
    if pd.isna(hist):
        return 5.0

    if direction == "up":
        # Upside: positive or improving histogram is good
        if prev_hist is not None and not pd.isna(prev_hist) and prev_hist < 0 and hist > 0:
            return 10.0  # Flip from negative to positive
        elif hist < 0 and prev_hist is not None and not pd.isna(prev_hist) and hist > prev_hist:
            return 5.0  # Narrowing negative
        elif hist < 0:
            return 2.0  # Widening negative
        else:
            return 5.0
    else:
        # Downside: negative or worsening histogram signals reversal
        if prev_hist is not None and not pd.isna(prev_hist) and prev_hist > 0 and hist < 0:
            return 10.0  # Flip from positive to negative
        elif hist > 0 and prev_hist is not None and not pd.isna(prev_hist) and hist < prev_hist:
            return 5.0  # Narrowing positive
        elif hist > 0:
            return 2.0  # Widening positive
        else:
            return 5.0


# =============================================================================
# PRICE VS SMA SCORING
# =============================================================================

def score_price_vs_sma200(
    close: float,
    sma200: float,
    prev_close: Optional[float],
    prev_sma200: Optional[float],
    direction: str = "up",
) -> float:
    """
    Score price position relative to 200-day SMA.

    Args:
        close: Current closing price
        sma200: Current 200-day SMA
        prev_close: Previous closing price
        prev_sma200: Previous 200-day SMA
        direction: "up" for upside reversal, "down" for downside reversal

    Returns:
        Score from 1.0 to 10.0
    """
    if pd.isna(sma200) or sma200 == 0:
        return 5.0

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
            return 10.0
        elif close > sma200:
            return 7.0
        elif pct_diff >= -3:
            return 5.0
        else:
            return 2.0
    else:
        crossed_below = (
            prev_close is not None
            and not pd.isna(prev_close)
            and prev_sma200 is not None
            and not pd.isna(prev_sma200)
            and prev_close > prev_sma200
            and close < sma200
        )
        if crossed_below:
            return 10.0
        elif pct_diff > 20:
            return 7.0  # Extended above
        elif pct_diff > 10:
            return 5.0
        else:
            return 2.0


# =============================================================================
# VOLUME SCORING
# =============================================================================

def score_volume_spike(volume_ratio: float) -> float:
    """
    Score volume relative to average.

    Args:
        volume_ratio: Current volume / average volume

    Returns:
        Score from 1.0 to 10.0
    """
    if volume_ratio >= 2.0:
        return 10.0
    elif volume_ratio >= 1.5:
        return 5.0
    else:
        return 2.0


def get_volume_ratio(df: pd.DataFrame, period: int = 20) -> float:
    """
    Calculate current volume / average volume ratio.

    Args:
        df: DataFrame with 'volume' column
        period: Lookback period for average

    Returns:
        Volume ratio (>1 = above average)
    """
    if 'volume' not in df.columns:
        return 1.0

    current_volume = df['volume'].iloc[-1]
    avg_volume = df['volume'].rolling(window=period).mean().iloc[-1]

    if pd.isna(avg_volume) or avg_volume == 0:
        return 1.0

    return current_volume / avg_volume


def get_volume_multiplier(df: pd.DataFrame, threshold: float = 1.2) -> float:
    """
    Soft volume gate: returns multiplier for score adjustment.

    - Volume >= 2.0x avg: 1.1x bonus
    - Volume >= 1.2x avg: 1.0x (neutral)
    - Volume >= 0.8x avg: 0.9x mild penalty
    - Volume < 0.8x avg: 0.75x penalty (low conviction)

    Args:
        df: DataFrame with 'volume' column
        threshold: Minimum ratio for neutral score

    Returns:
        Multiplier (0.75-1.1)
    """
    ratio = get_volume_ratio(df)

    if ratio >= 2.0:
        return 1.1
    elif ratio >= threshold:
        return 1.0
    elif ratio >= 0.8:
        return 0.9
    else:
        return 0.75


# =============================================================================
# WILLIAMS %R SCORING
# =============================================================================

def score_williams_r(williams_r: float, direction: str = "up") -> float:
    """
    Score Williams %R value.

    Williams %R ranges from -100 to 0.
    Below -80 = oversold, above -20 = overbought.

    Args:
        williams_r: Williams %R value (-100 to 0)
        direction: "up" for upside reversal, "down" for downside reversal

    Returns:
        Score from 1.0 to 10.0
    """
    if pd.isna(williams_r):
        return 5.0

    if direction == "up":
        # Upside: lower (more negative) is more oversold
        if williams_r < -80:
            return 10.0
        elif williams_r < -50:
            return 5.0
        else:
            return 2.0
    else:
        # Downside: higher (less negative) is more overbought
        if williams_r > -20:
            return 10.0
        elif williams_r > -50:
            return 5.0
        else:
            return 2.0


def score_williams_r_oversold(williams_r: float) -> float:
    """
    Score Williams %R for oversold condition.

    Args:
        williams_r: Williams %R value (-100 to 0)

    Returns:
        Score from 1.0 to 10.0
    """
    if pd.isna(williams_r):
        return 0.0

    thresholds = [
        (-95, 10.0),
        (-90, 8.0),
        (-85, 6.0),
        (-80, 4.0),
        (-70, 2.0),
    ]

    for threshold, score in thresholds:
        if williams_r < threshold:
            return score
    return 1.0


# =============================================================================
# DIVERGENCE SCORING
# =============================================================================

def score_divergence(
    divergence: DivergenceResult,
    expected_type: DivergenceType,
) -> float:
    """
    Score divergence alignment with expected direction.

    Args:
        divergence: Detected divergence result
        expected_type: Expected divergence type (BULLISH or BEARISH)

    Returns:
        Score from 1.0 to 10.0
    """
    if divergence.type == expected_type:
        base_score = min(10.0, 7.0 + (divergence.strength / 10.0))
        return base_score
    return 2.0


# =============================================================================
# CONSECUTIVE DAYS SCORING
# =============================================================================

def score_consecutive_days(df: pd.DataFrame, direction: str = "red") -> float:
    """
    Score based on consecutive red/green days.

    Args:
        df: DataFrame with 'close' column
        direction: "red" (down) or "green" (up)

    Returns:
        Score from 1.0 to 10.0
    """
    if df is None or len(df) < 5:
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
        else:
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


def score_consecutive_red(df: pd.DataFrame) -> float:
    """
    Score based on consecutive down days for oversold detection — TIGHTENED.

    Removed loose thresholds (2-3 days) that are common market noise.

    Args:
        df: DataFrame with 'close' column

    Returns:
        Score from 1.0 to 10.0
    """
    if df is None or len(df) < 2:
        return 0.0

    count = 0
    closes = df["close"].values

    for i in range(len(closes) - 1, 0, -1):
        if closes[i] < closes[i - 1]:
            count += 1
        else:
            break

    # Tightened thresholds - 3 days is noise, need 5+ for signal
    thresholds = [
        (8, 10.0),   # Extreme selloff
        (7, 9.0),    # Very extended
        (6, 7.0),    # Extended
        (5, 5.0),    # Notable
    ]

    for threshold, score in thresholds:
        if count >= threshold:
            return score
    return 1.0  # Less than 5 days = noise


# =============================================================================
# BOLLINGER BAND SCORING
# =============================================================================

def score_bollinger_position(
    close: float,
    bb_lower: float,
    bb_middle: float,
) -> float:
    """
    Score price position relative to Bollinger Bands.

    Price below lower band indicates potential oversold condition.

    Args:
        close: Current closing price
        bb_lower: Lower Bollinger Band value
        bb_middle: Middle Bollinger Band (SMA20)

    Returns:
        Score from 1.0 to 10.0
    """
    if pd.isna(close) or pd.isna(bb_lower) or pd.isna(bb_middle) or bb_middle == 0:
        return 0.0

    band_width = bb_middle - bb_lower
    if band_width <= 0:
        return 1.0

    if close < bb_lower:
        # Below lower band — very oversold
        distance_below = (bb_lower - close) / band_width
        if distance_below > 0.5:
            return 10.0
        elif distance_below > 0.25:
            return 9.0
        return 8.0

    # Above lower band — check proximity
    distance_above = (close - bb_lower) / band_width
    thresholds = [
        (0.2, 6.0),
        (0.4, 4.0),
        (0.6, 2.0),
    ]

    for threshold, score in thresholds:
        if distance_above < threshold:
            return score
    return 1.0


# =============================================================================
# SMA DISTANCE SCORING
# =============================================================================

def score_sma200_distance(close: float, sma200: float) -> float:
    """
    Score how far price is below SMA200.

    Deeper below the 200-day moving average indicates more oversold.

    Args:
        close: Current closing price
        sma200: 200-day simple moving average

    Returns:
        Score from 1.0 to 10.0
    """
    if pd.isna(close) or pd.isna(sma200) or sma200 == 0:
        return 0.0

    pct_below = ((sma200 - close) / sma200) * 100

    thresholds = [
        (30, 10.0),
        (20, 9.0),
        (15, 7.0),
        (10, 5.0),
        (5, 3.0),
        (0, 2.0),
    ]

    for threshold, score in thresholds:
        if pct_below > threshold:
            return score
    return 1.0  # Above SMA200


# =============================================================================
# ADX MULTIPLIER
# =============================================================================

def get_adx_multiplier(adx_value: float, signal_type: str = "reversal") -> float:
    """
    ADX-based regime modifier.

    For REVERSAL signals (mean reversion):
        - ADX < 20: Weak trend, mean reversion favored → 1.1x boost
        - ADX 20-30: Moderate trend → 1.0x (neutral)
        - ADX > 30: Strong trend, fighting momentum → 0.85x penalty

    Args:
        adx_value: Current ADX value
        signal_type: "reversal" or "trend"

    Returns:
        Multiplier (0.85-1.1)
    """
    if pd.isna(adx_value):
        return 1.0

    if signal_type == "reversal":
        if adx_value < 20:
            return 1.1
        elif adx_value <= 30:
            return 1.0
        else:
            return 0.85

    return 1.0

