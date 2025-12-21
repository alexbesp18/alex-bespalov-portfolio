"""
Reversal Calculator - Computes upside and downside reversal scores.

Mid-term reversal detection for portfolio management.
Uses v2 scoring with volume gate, ADX regime, and enhanced divergence.
"""

import pandas as pd
from .calculator import TechnicalCalculator
from .reversal_scoring_v2 import (
    calculate_upside_reversal_score_v2,
    calculate_downside_reversal_score_v2,
    detect_combined_divergence,
    DivergenceType,
    format_score_report,
)


class ReversalCalculator:
    """
    Computes Upside and Downside Reversal Scores (1-10) based on technical indicators.
    Uses v2 scoring with volume gate, ADX regime multiplier, and enhanced divergence.
    """
    
    def __init__(self):
        self.calc = TechnicalCalculator()
    
    def calculate_upside_reversal_score(self, df: pd.DataFrame) -> tuple:
        """
        Computes 1-10 upside reversal score (potential bottom/bounce).
        
        V2 Enhancements:
        - Soft volume gate (multiplier, not hard cutoff)
        - ADX regime multiplier (boost in weak trends)
        - Williams %R included at 5% weight
        - Enhanced swing-based divergence detection
        
        Returns: (score, breakdown_dict)
        """
        result = calculate_upside_reversal_score_v2(df)
        
        # Convert ReversalScore dataclass to legacy tuple format
        breakdown = {
            **result.components,
            'volume_multiplier': result.volume_multiplier,
            'adx_multiplier': result.adx_multiplier,
            'divergence_type': result.divergence.description if result.divergence else 'None',
            'raw_score': result.raw_score,
        }
        
        return result.final_score, breakdown
    
    def calculate_downside_reversal_score(self, df: pd.DataFrame) -> tuple:
        """
        Computes 1-10 downside reversal score (potential top/pullback).
        
        V2 Enhancements:
        - Soft volume gate (multiplier, not hard cutoff)
        - ADX regime multiplier (boost in weak trends)
        - Williams %R included at 5% weight
        - Enhanced swing-based divergence detection
        
        Returns: (score, breakdown_dict)
        """
        result = calculate_downside_reversal_score_v2(df)
        
        # Convert ReversalScore dataclass to legacy tuple format
        breakdown = {
            **result.components,
            'volume_multiplier': result.volume_multiplier,
            'adx_multiplier': result.adx_multiplier,
            'divergence_type': result.divergence.description if result.divergence else 'None',
            'raw_score': result.raw_score,
        }
        
        return result.final_score, breakdown
    
    def detect_reversal_triggers(self, df: pd.DataFrame) -> dict:
        """
        Detects specific reversal trigger conditions.
        
        Returns dict with trigger IDs that are active.
        """
        if df is None or len(df) < 50:
            return {'upside': [], 'downside': []}
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        upside_triggers = []
        downside_triggers = []
        
        # Get key values
        price = curr['close']
        prev_price = prev['close']
        sma50 = curr.get('SMA_50', 0) or 0
        sma200 = curr.get('SMA_200', 0) or 0
        prev_sma50 = prev.get('SMA_50', 0) or 0
        prev_sma200 = prev.get('SMA_200', 0) or 0
        rsi = curr.get('RSI', 50) or 50
        prev_rsi = prev.get('RSI', 50) or 50
        macd_hist = curr.get('MACD_HIST', 0) or 0
        prev_macd_hist = prev.get('MACD_HIST', 0) or 0
        stoch_k = curr.get('STOCH_K', 50) or 50
        stoch_d = curr.get('STOCH_D', 50) or 50
        prev_stoch_k = prev.get('STOCH_K', 50) or 50
        prev_stoch_d = prev.get('STOCH_D', 50) or 50
        
        # === UPSIDE REVERSAL TRIGGERS ===
        
        # REV-UP-01: Golden Cross (50 > 200)
        if prev_sma50 <= prev_sma200 and sma50 > sma200:
            upside_triggers.append({'id': 'REV-UP-01', 'name': 'Golden Cross', 'priority': 'HIGH'})
        
        # REV-UP-02: Price crosses ABOVE 200 SMA
        if prev_price < prev_sma200 and price > sma200:
            upside_triggers.append({'id': 'REV-UP-02', 'name': 'Price > 200 SMA', 'priority': 'HIGH'})
        
        # REV-UP-03: RSI crosses above 30 from below
        if prev_rsi < 30 and rsi >= 30:
            upside_triggers.append({'id': 'REV-UP-03', 'name': 'RSI bounce from oversold', 'priority': 'MEDIUM'})
        
        # REV-UP-04: MACD histogram flips positive
        if prev_macd_hist < 0 and macd_hist >= 0:
            upside_triggers.append({'id': 'REV-UP-04', 'name': 'MACD histogram flip +', 'priority': 'MEDIUM'})
        
        # REV-UP-05: Stochastic bullish cross while <20
        if stoch_k < 20 and prev_stoch_k < prev_stoch_d and stoch_k > stoch_d:
            upside_triggers.append({'id': 'REV-UP-05', 'name': 'Stoch bullish cross <20', 'priority': 'MEDIUM'})
        
        # REV-UP-06: Bullish divergence
        rsi_div = self.calc.detect_rsi_divergence(df)
        obv_div = self.calc.detect_obv_divergence(df)
        if rsi_div == 'bullish':
            upside_triggers.append({'id': 'REV-UP-06a', 'name': 'Bullish RSI divergence', 'priority': 'HIGH'})
        if obv_div == 'bullish':
            upside_triggers.append({'id': 'REV-UP-06b', 'name': 'Bullish OBV divergence', 'priority': 'HIGH'})
        
        # === DOWNSIDE REVERSAL TRIGGERS ===
        
        # REV-DN-01: Death Cross (50 < 200)
        if prev_sma50 >= prev_sma200 and sma50 < sma200:
            downside_triggers.append({'id': 'REV-DN-01', 'name': 'Death Cross', 'priority': 'HIGH'})
        
        # REV-DN-02: Price crosses BELOW 200 SMA
        if prev_price > prev_sma200 and price < sma200:
            downside_triggers.append({'id': 'REV-DN-02', 'name': 'Price < 200 SMA', 'priority': 'HIGH'})
        
        # REV-DN-03: RSI crosses below 70 from above
        if prev_rsi > 70 and rsi <= 70:
            downside_triggers.append({'id': 'REV-DN-03', 'name': 'RSI drop from overbought', 'priority': 'MEDIUM'})
        
        # REV-DN-04: MACD histogram flips negative
        if prev_macd_hist > 0 and macd_hist <= 0:
            downside_triggers.append({'id': 'REV-DN-04', 'name': 'MACD histogram flip -', 'priority': 'MEDIUM'})
        
        # REV-DN-05: Stochastic bearish cross while >80
        if stoch_k > 80 and prev_stoch_k > prev_stoch_d and stoch_k < stoch_d:
            downside_triggers.append({'id': 'REV-DN-05', 'name': 'Stoch bearish cross >80', 'priority': 'MEDIUM'})
        
        # REV-DN-06: Bearish divergence
        if rsi_div == 'bearish':
            downside_triggers.append({'id': 'REV-DN-06a', 'name': 'Bearish RSI divergence', 'priority': 'HIGH'})
        if obv_div == 'bearish':
            downside_triggers.append({'id': 'REV-DN-06b', 'name': 'Bearish OBV divergence', 'priority': 'HIGH'})
        
        return {
            'upside': upside_triggers,
            'downside': downside_triggers
        }
    
    def get_full_reversal_analysis(self, df: pd.DataFrame, symbol: str = '') -> dict:
        """
        Returns complete reversal analysis for a ticker.
        """
        upside_score, upside_breakdown = self.calculate_upside_reversal_score(df)
        downside_score, downside_breakdown = self.calculate_downside_reversal_score(df)
        triggers = self.detect_reversal_triggers(df)
        
        # Determine primary signal
        if upside_score >= 7 and len(triggers['upside']) > 0:
            signal = 'UPSIDE_REVERSAL'
        elif downside_score >= 7 and len(triggers['downside']) > 0:
            signal = 'DOWNSIDE_REVERSAL'
        elif upside_score >= 6:
            signal = 'UPSIDE_WATCH'
        elif downside_score >= 6:
            signal = 'DOWNSIDE_WATCH'
        else:
            signal = 'NEUTRAL'
        
        return {
            'symbol': symbol,
            'price': df.iloc[-1]['close'] if df is not None and len(df) > 0 else 0,
            'signal': signal,
            'upside_reversal_score': upside_score,
            'upside_breakdown': upside_breakdown,
            'downside_reversal_score': downside_score,
            'downside_breakdown': downside_breakdown,
            'upside_triggers': triggers['upside'],
            'downside_triggers': triggers['downside'],
            'rsi': df.iloc[-1].get('RSI', 0) if df is not None and len(df) > 0 else 0,
            'williams_r': df.iloc[-1].get('WILLIAMS_R', 0) if df is not None and len(df) > 0 else 0,
        }
