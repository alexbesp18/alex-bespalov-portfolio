"""
compute_flags.py — Computes state flags and event flags for each ticker.

State Flags (true/false today):
- above_SMA200, below_SMA200, above_SMA50
- new_20day_high, volume_above_1.5x_avg

Event Flags (true only on day of transition):
- crosses_above_SMA200, crosses_below_SMA200
- rsi_crosses_above_30, rsi_crosses_above_60

Continuous Values:
- rsi, score, close, sma50, sma200
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def compute_sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period).mean()


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def compute_score(df: pd.DataFrame) -> tuple:
    """
    Compute bullish score (0-10) based on technical indicators.
    Simplified scoring logic based on trend, RSI, MACD, volume, and momentum.

    Returns:
        tuple: (score, components_dict) where components breaks down each factor
    """
    if len(df) < 50:
        return 0.0, {}

    curr = df.iloc[-1]
    prev = df.iloc[-2]

    components = {}

    # Trend: Price vs SMAs (30%)
    if curr['close'] > curr.get('sma50', 0) and curr.get('sma50', 0) > curr.get('sma200', 0):
        components['trend'] = 3.0
    elif curr['close'] > curr.get('sma200', 0):
        components['trend'] = 2.0
    elif curr['close'] > curr.get('sma50', 0):
        components['trend'] = 1.0
    else:
        components['trend'] = 0.0

    # RSI (25%)
    rsi = curr.get('rsi', 50)
    if 50 <= rsi <= 70:
        components['rsi'] = 2.5
    elif 40 <= rsi < 50:
        components['rsi'] = 1.5
    elif rsi > 70:
        components['rsi'] = 1.0
    else:
        components['rsi'] = 0.0

    # MACD direction (20%)
    components['macd'] = 0.0
    if 'macd_hist' in curr and 'macd_hist' in prev:
        if curr['macd_hist'] > 0:
            components['macd'] = 2.0 if curr['macd_hist'] > prev['macd_hist'] else 1.5
        elif curr['macd_hist'] > prev['macd_hist']:
            components['macd'] = 1.0

    # Volume trend (15%)
    if curr.get('volume_ratio', 1) > 1.2:
        components['volume'] = 1.5
    elif curr.get('volume_ratio', 1) > 0.8:
        components['volume'] = 0.75
    else:
        components['volume'] = 0.0

    # Price momentum (10%)
    components['momentum'] = 0.0
    if len(df) >= 5:
        pct_5d = (curr['close'] - df.iloc[-5]['close']) / df.iloc[-5]['close'] * 100
        if pct_5d > 3:
            components['momentum'] = 1.0
        elif pct_5d > 0:
            components['momentum'] = 0.5

    score = sum(components.values())
    return round(min(10, score), 1), components


def process_ticker_data(raw_data: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """
    Process raw Twelve Data response into DataFrame with indicators.
    """
    if not raw_data or "values" not in raw_data:
        return None
    
    df = pd.DataFrame(raw_data["values"])
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.set_index('datetime').sort_index()
    
    # Convert numeric columns
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna(subset=['close'])
    
    if len(df) < 20:
        return None
    
    # Compute indicators
    df['sma200'] = compute_sma(df['close'], 200)
    df['sma50'] = compute_sma(df['close'], 50)
    df['sma20'] = compute_sma(df['close'], 20)
    df['rsi'] = compute_rsi(df['close'], 14)
    
    # Volume average
    df['avg_volume_20d'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['avg_volume_20d']
    
    # 20-day high
    df['high_20d'] = df['high'].rolling(20).max()
    
    # MACD
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    return df


def compute_flags(df: pd.DataFrame, previous_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Compute all flags for a ticker based on current data and previous state.
    
    Args:
        df: DataFrame with OHLCV and indicators
        previous_state: Previous day's flags (for event detection)
    
    Returns:
        Dict with all flags and values
    """
    if df is None or len(df) < 2:
        return {}
    
    curr = df.iloc[-1]
    close = curr['close']
    sma200 = curr.get('sma200') or 0
    sma50 = curr.get('sma50') or 0
    rsi = curr.get('rsi') or 50
    high_20d = curr.get('high_20d') or close
    volume = curr.get('volume') or 0
    avg_volume = curr.get('avg_volume_20d') or volume
    
    # Compute score and components
    score, components = compute_score(df)

    # State flags - convert numpy types to native Python types for JSON
    flags = {
        'above_SMA200': bool(close > sma200) if sma200 else False,
        'below_SMA200': bool(close < sma200) if sma200 else False,
        'above_SMA50': bool(close > sma50) if sma50 else False,
        'new_20day_high': bool(close >= high_20d),
        'volume_above_1.5x_avg': bool(volume > 1.5 * avg_volume) if avg_volume else False,

        # Continuous values
        'rsi': float(round(rsi, 1)) if pd.notna(rsi) else 50.0,
        'score': float(score),
        'close': float(round(close, 2)),
        'sma50': float(round(sma50, 2)) if sma50 else None,
        'sma200': float(round(sma200, 2)) if sma200 else None,

        # Score component breakdown for historical analysis
        'score_components': components,
    }
    
    # Event flags (require previous state)
    if previous_state:
        prev_above_sma200 = previous_state.get('above_SMA200', False)
        prev_below_sma200 = previous_state.get('below_SMA200', False)
        prev_rsi = previous_state.get('rsi', 50)
        
        flags['crosses_above_SMA200'] = bool(flags['above_SMA200'] and prev_below_sma200)
        flags['crosses_below_SMA200'] = bool(flags['below_SMA200'] and prev_above_sma200)
        flags['rsi_crosses_above_30'] = bool(rsi > 30 and prev_rsi <= 30)
        flags['rsi_crosses_above_60'] = bool(rsi > 60 and prev_rsi <= 60)
    else:
        # First run: no events
        flags['crosses_above_SMA200'] = False
        flags['crosses_below_SMA200'] = False
        flags['rsi_crosses_above_30'] = False
        flags['rsi_crosses_above_60'] = False
    
    return flags


if __name__ == "__main__":
    # Test
    print("compute_flags module loaded successfully")
