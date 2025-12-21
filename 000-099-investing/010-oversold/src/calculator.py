"""
Technical indicator calculations for oversold screener.

Extends shared_core.TechnicalCalculator with oversold-specific scoring methods.
"""

import pandas as pd
import numpy as np

# Import base calculator from shared_core
from shared_core import TechnicalCalculator as BaseCalculator


class TechnicalCalculator(BaseCalculator):
    """
    Extended TechnicalCalculator with oversold-specific scoring methods.
    
    Inherits all base methods from shared_core.TechnicalCalculator:
    - sma, ema, rsi, macd, bollinger_bands, atr, stochastic, adx, obv
    - williams_r, roc
    - classify_trend, classify_volatility
    - detect_divergence, detect_rsi_divergence, detect_obv_divergence
    - count_consecutive_direction, calculate_support_resistance
    """
    
    def __init__(self):
        pass
    
    @staticmethod
    def bollinger_bands_with_width(close: pd.Series, period: int = 20, std_dev: int = 2) -> tuple:
        """Returns (upper_band, middle_band, lower_band, bandwidth)"""
        middle = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        bandwidth = ((upper - lower) / middle) * 100
        return upper, middle, lower, bandwidth

    def process_data(self, time_series_data):
        """
        Takes raw Twelve Data time series (list of dicts) and returns a DataFrame
        with calculated indicators.
        """
        if "values" not in time_series_data or not time_series_data["values"]:
            return None
        
        df = pd.DataFrame(time_series_data["values"])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.set_index('datetime').sort_index()
        
        # Convert numeric columns
        cols = ['open', 'high', 'low', 'close', 'volume']
        for col in cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Drop rows with missing core data
        df = df.dropna(subset=['close'])
        
        # Calculate Indicators using inherited static methods
        # Trend
        df['SMA_20'] = self.sma(df['close'], 20)
        df['SMA_50'] = self.sma(df['close'], 50)
        df['SMA_200'] = self.sma(df['close'], 200)
        
        # Momentum
        df['RSI'] = self.rsi(df['close'], 14)
        
        macd_line, signal_line, hist = self.macd(df['close'])
        df['MACD'] = macd_line
        df['MACD_SIGNAL'] = signal_line
        df['MACD_HIST'] = hist
        
        # ADX - use adx_series for full series
        df['ADX'] = self.adx_series(df)
        
        # OBV
        df['OBV'] = self.obv(df)
        
        # Stochastics
        stoch_k, stoch_d = self.stochastic(df)
        df['STOCH_K'] = stoch_k
        df['STOCH_D'] = stoch_d
        
        # Bollinger Bands with bandwidth
        bb_upper, bb_middle, bb_lower, bb_width = self.bollinger_bands_with_width(df['close'])
        df['BB_UPPER'] = bb_upper
        df['BB_MIDDLE'] = bb_middle
        df['BB_LOWER'] = bb_lower
        df['BB_WIDTH'] = bb_width
        
        # ATR
        df['ATR'] = self.atr(df)
        
        # Williams %R
        df['WILLIAMS_R'] = self.williams_r(df)
        
        # Rate of Change
        df['ROC'] = self.roc(df['close'])
        
        return df

    def calculate_bullish_score(self, df):
        """
        Computes 1-10 bullish score based on the latest row.
        
        Weights:
        TREND DIRECTION     25%   SMA20 > SMA50 mostly
        MA STACK            20%   20>50>200=10, Mixed=5, Bearish=2
        MACD HISTOGRAM      15%   Positive+expanding=10, Negative=2
        RSI POSITION        15%   50-70=10, 30-50=6, extremes=4
        OBV TREND           15%   UP=10, SIDEWAYS=5, DOWN=2
        ADX STRENGTH        10%   >25=10, 20-25=7, <20=4
        """
        if df is None or len(df) < 50:
            return 0, {}
            
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        score = 0
        breakdown = {}
        
        # 1. Trend Direction (25%)
        trend_score = 2
        sma50 = curr.get('SMA_50', 0) or 0
        sma200 = curr.get('SMA_200', 0) or 0
        
        if curr['close'] > sma50 and sma50 > sma200:
            trend_score = 10  # Strong Up
        elif curr['close'] > sma200:
            trend_score = 8  # Up
        elif curr['close'] > sma50:
            trend_score = 5  # Sideways/Recovering
        
        score += trend_score * 0.25
        breakdown['trend'] = trend_score

        # 2. MA Stack (20%)
        ma_score = 2
        sma20 = curr.get('SMA_20', 0) or 0
        
        if sma20 > sma50 and sma50 > sma200:
            ma_score = 10
        elif sma20 > sma50 or sma50 > sma200:
            ma_score = 5
        
        score += ma_score * 0.20
        breakdown['ma_stack'] = ma_score

        # 3. MACD Histogram (15%)
        macd_score = 2
        curr_hist = curr.get('MACD_HIST', 0) or 0
        prev_hist = prev.get('MACD_HIST', 0) or 0
        
        if curr_hist > 0:
            if curr_hist > prev_hist:
                macd_score = 10  # Positive and expanding
            else:
                macd_score = 8  # Positive but narrowing
        else:
            if curr_hist > prev_hist:
                macd_score = 5  # Negative but improving
        
        score += macd_score * 0.15
        breakdown['macd'] = macd_score

        # 4. RSI Position (15%)
        rsi_score = 4
        rsi = curr.get('RSI', 50) or 50
        
        if 50 <= rsi <= 70:
            rsi_score = 10
        elif 30 <= rsi < 50:
            rsi_score = 6
        elif rsi > 70:
            rsi_score = 7 
        elif rsi < 30:
            rsi_score = 2 
        
        score += rsi_score * 0.15
        breakdown['rsi'] = rsi_score
        
        # 5. OBV Trend (15%)
        obv_score = 5
        if len(df) >= 20:
            obv_slope = df['OBV'].iloc[-5:].is_monotonic_increasing
            if obv_slope:
                obv_score = 10
            elif df['OBV'].iloc[-1] < df['OBV'].iloc[-20]: 
                obv_score = 2
            
        score += obv_score * 0.15
        breakdown['obv'] = obv_score
        
        # 6. ADX Strength (10%)
        adx_score = 4
        adx = curr.get('ADX', 0) or 0
        if adx > 25:
            adx_score = 10
        elif 20 <= adx <= 25:
            adx_score = 7
            
        score += adx_score * 0.10
        breakdown['adx'] = adx_score
        
        return round(score, 1), breakdown

    def calculate_matrix(self, df) -> dict:
        """
        Generates a dictionary of binary flags for matrix/dashboard output.
        
        Categories:
        - Price Correction from 52W High: -5%, -10%, -15%, -20%, -30%, -40%, -50%
        - Price vs MAs: >SMA5, >SMA14, >SMA50, >SMA200
        - MA Crosses Today: Golden (50>200), Death (50<200)
        - RSI Levels: >85, >70, <30, <15
        
        Returns: Dict with binary (0/1) values for each flag.
        """
        if df is None or len(df) < 2:
            return {}
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        price = curr['close']
        
        # Calculate 52-week high (approx 252 trading days, use available data)
        high_52w = df['high'].max()
        
        # Calculate SMAs that might not be in process_data
        if 'SMA_5' not in df.columns:
            df['SMA_5'] = self.sma(df['close'], 5)
        if 'SMA_14' not in df.columns:
            df['SMA_14'] = self.sma(df['close'], 14)
        
        curr = df.iloc[-1]  # Refresh after adding columns
        prev = df.iloc[-2]
        
        matrix = {}
        
        # --- Price Correction from 52W High ---
        pct_from_high = (high_52w - price) / high_52w * 100 if high_52w > 0 else 0
        matrix['corr_5pct'] = 1 if pct_from_high >= 5 else 0
        matrix['corr_10pct'] = 1 if pct_from_high >= 10 else 0
        matrix['corr_15pct'] = 1 if pct_from_high >= 15 else 0
        matrix['corr_20pct'] = 1 if pct_from_high >= 20 else 0
        matrix['corr_30pct'] = 1 if pct_from_high >= 30 else 0
        matrix['corr_40pct'] = 1 if pct_from_high >= 40 else 0
        matrix['corr_50pct'] = 1 if pct_from_high >= 50 else 0
        
        # --- Price vs MAs ---
        matrix['above_SMA5'] = 1 if price > (curr.get('SMA_5') or 0) else 0
        matrix['above_SMA14'] = 1 if price > (curr.get('SMA_14') or 0) else 0
        matrix['above_SMA50'] = 1 if price > (curr.get('SMA_50') or 0) else 0
        matrix['above_SMA200'] = 1 if price > (curr.get('SMA_200') or 0) else 0
        
        # --- MA Crosses Today ---
        sma50_curr = curr.get('SMA_50') or 0
        sma50_prev = prev.get('SMA_50') or 0
        sma200_curr = curr.get('SMA_200') or 0
        sma200_prev = prev.get('SMA_200') or 0
        
        matrix['golden_cross'] = 1 if (sma50_prev <= sma200_prev and sma50_curr > sma200_curr) else 0
        matrix['death_cross'] = 1 if (sma50_prev >= sma200_prev and sma50_curr < sma200_curr) else 0
        
        # --- RSI Levels ---
        rsi = curr.get('RSI') or 50
        matrix['rsi_above_85'] = 1 if rsi > 85 else 0
        matrix['rsi_above_70'] = 1 if rsi > 70 else 0
        matrix['rsi_below_30'] = 1 if rsi < 30 else 0
        matrix['rsi_below_15'] = 1 if rsi < 15 else 0
        
        # --- Additional useful metrics (not binary) ---
        matrix['_price'] = round(price, 2)
        matrix['_high_52w'] = round(high_52w, 2)
        matrix['_pct_from_high'] = round(pct_from_high, 1)
        matrix['_rsi'] = round(rsi, 1)
        
        return matrix
