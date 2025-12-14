import pandas as pd
import numpy as np

class TechnicalCalculator:
    def __init__(self):
        pass

    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        return data.rolling(window=period).mean()

    @staticmethod
    def rsi(close_prices: pd.Series, period: int = 14) -> pd.Series:
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def macd(close_prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        ema_fast = close_prices.ewm(span=fast, adjust=False).mean()
        ema_slow = close_prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
        high, low, close = df['high'], df['low'], df['close']
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        return adx

    @staticmethod
    def obv(df: pd.DataFrame) -> pd.Series:
        return (df['volume'] * np.where(df['close'].diff() > 0, 1, -1)).cumsum()

    @staticmethod
    def stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> tuple:
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        k = 100 * ((df['close'] - low_min) / (high_max - low_min))
        d = k.rolling(window=d_period).mean()
        return k, d

    def process_data(self, time_series_data):
        """
        Takes raw Twelve Data time series (list of dicts) and returns a DataFrame
        with calculated indicators using manual methods (no pandas_ta).
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
        
        # Calculate Indicators using static methods
        # Trend
        df['SMA_20'] = self.sma(df['close'], 20)
        df['SMA_50'] = self.sma(df['close'], 50)
        df['SMA_200'] = self.sma(df['close'], 200)
        
        # Momentum
        df['RSI'] = self.rsi(df['close'], 14)
        
        macd_line, signal_line, hist = self.macd(df['close'])
        # df['MACD'] = macd_line         # Not strictly needed for score but good for debug
        # df['MACD_SIGNAL'] = signal_line # Not strictly needed for score
        df['MACD_HIST'] = hist
        
        # ADX
        # 008 returns a float (only last value) in some contexts, but here we want the series
        # Modified 008 logic slightly to return Series for the whole DF
        df['ADX'] = self.adx(df)
        
        # OBV
        df['OBV'] = self.obv(df)
        
        # Stochastics
        stoch_k, stoch_d = self.stochastic(df)
        df['STOCH_K'] = stoch_k
        df['STOCH_D'] = stoch_d
        
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
        if df is None or len(df) < 50: # Reduced requirements from 200 to 50 to avoid strict failures on limited data
            return 0, {}
            
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        score = 0
        breakdown = {}
        
        # 1. Trend Direction (25%)
        trend_score = 2
        # Handle cases where SMA might be NaN if not enough history
        sma50 = curr.get('SMA_50', 0) or 0
        sma200 = curr.get('SMA_200', 0) or 0
        
        if curr['close'] > sma50 and sma50 > sma200:
            trend_score = 10 # Strong Up
        elif curr['close'] > sma200:
            trend_score = 8 # Up
        elif curr['close'] > sma50:
            trend_score = 5 # Sideways/Recovering
        
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
                macd_score = 10 # Positive and expanding
            else:
                macd_score = 8 # Positive but narrowing
        else:
             if curr_hist > prev_hist:
                 macd_score = 5 # Negative but improving
        
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
        # Simple slope check over last 5 days
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
        # Golden Cross: SMA50 crosses above SMA200
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

