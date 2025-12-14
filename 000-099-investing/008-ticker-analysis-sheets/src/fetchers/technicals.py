import requests
import pandas as pd
import datetime as dt
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.utils.logging import setup_logger
from src.analysis.technical import TechnicalCalculator

logger = setup_logger(__name__)

class TwelveDataFetcher:
    """Fetch OHLCV data from Twelve Data and calculate all indicators."""
    
    def __init__(self, api_key: str, output_size: int = 365):
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com"
        self.output_size = output_size
        self.calc = TechnicalCalculator()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(requests.exceptions.RequestException)
    )
    def _fetch_data(self, ticker: str) -> Dict[str, Any]:
        """Fetch raw data with retry."""
        url = f"{self.base_url}/time_series"
        params = {
            'symbol': ticker,
            'interval': '1day',
            'outputsize': self.output_size,
            'apikey': self.api_key
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def fetch_and_calculate(self, ticker: str) -> Dict[str, Any]:
        """Fetch data and calculate all indicators. Returns dict for sheet row."""
        logger.info(f"📊 Fetching {ticker} from Twelve Data...")
        
        try:
            data = self._fetch_data(ticker)
            
            # Check for API-level errors
            if 'code' in data and data['code'] != 200:
                error_msg = data.get('message', 'Unknown API error')
                logger.error(f"Twelve Data error for {ticker}: {error_msg}")
                return {'Ticker': ticker, 'Status': f"ERROR: {error_msg}"}
            
            if 'values' not in data or not data['values']:
                logger.warning(f"No data returned for {ticker}")
                return {'Ticker': ticker, 'Status': "ERROR: No data returned"}
            
            # Convert to DataFrame
            df = pd.DataFrame(data['values'])
            df['datetime'] = pd.to_datetime(df['datetime'])
            for col in ['open', 'high', 'low', 'close']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0).astype(int)
            df = df.sort_values('datetime').reset_index(drop=True)
            df = df.dropna(subset=['close'])
            
            if len(df) < 50:
                logger.warning(f"Insufficient data for {ticker}: {len(df)} bars")
                return {'Ticker': ticker, 'Status': f"ERROR: Only {len(df)} bars"}
            
            # Current values
            current_price = float(df['close'].iloc[-1])
            previous_close = float(df['close'].iloc[-2]) if len(df) > 1 else current_price
            change_pct = ((current_price - previous_close) / previous_close) * 100 if previous_close > 0 else 0
            
            # Calculate indicators
            rsi_series = self.calc.rsi(df['close'])
            macd_line, signal_line, histogram = self.calc.macd(df['close'])
            bb_upper, bb_middle, bb_lower = self.calc.bollinger_bands(df['close'])
            stoch_k, stoch_d = self.calc.stochastic(df)
            atr_series = self.calc.atr(df)
            obv_series = self.calc.obv(df)
            
            # OBV trend
            obv_sma = obv_series.rolling(20).mean()
            if obv_series.iloc[-1] > obv_sma.iloc[-1] * 1.02:
                obv_trend = 'UP'
            elif obv_series.iloc[-1] < obv_sma.iloc[-1] * 0.98:
                obv_trend = 'DOWN'
            else:
                obv_trend = 'SIDEWAYS'
            
            # Trend classification
            sma_20 = float(self.calc.sma(df['close'], 20).iloc[-1])
            sma_50 = float(self.calc.sma(df['close'], 50).iloc[-1])
            sma_200 = float(self.calc.sma(df['close'], min(200, len(df))).iloc[-1])
            
            macd_hist = float(histogram.iloc[-1])
            if current_price > sma_200 * 1.10 and macd_hist > 0 and sma_20 > sma_50 > sma_200:
                trend = 'STRONG_UPTREND'
            elif current_price > sma_200 and sma_20 > sma_50:
                trend = 'UPTREND'
            elif current_price < sma_200 * 0.90 and macd_hist < 0 and sma_20 < sma_50 < sma_200:
                trend = 'STRONG_DOWNTREND'
            elif current_price < sma_200 and sma_20 < sma_50:
                trend = 'DOWNTREND'
            else:
                trend = 'SIDEWAYS'
            
            # Divergence detection
            price_trend = df['close'].tail(20).diff().sum()
            rsi_trend = rsi_series.tail(20).diff().sum()
            rsi_current = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50.0
            
            if price_trend < 0 and rsi_trend > 0 and rsi_current < 40:
                divergence = 'BULLISH'
            elif price_trend > 0 and rsi_trend < 0 and rsi_current > 60:
                divergence = 'BEARISH'
            else:
                divergence = 'NONE'
            
            # Volatility regime
            atr_90 = atr_series.tail(min(90, len(df)))
            atr_current = float(atr_series.iloc[-1])
            atr_min, atr_max = atr_90.min(), atr_90.max()
            if atr_max > atr_min:
                atr_pct = (atr_current - atr_min) / (atr_max - atr_min)
            else:
                atr_pct = 0.5
            
            if atr_pct < 0.25:
                volatility = 'LOW'
            elif atr_pct < 0.5:
                volatility = 'NORMAL'
            elif atr_pct < 0.75:
                volatility = 'HIGH'
            else:
                volatility = 'EXTREME'
            
            # Relative volume
            avg_volume = df['volume'].tail(20).mean()
            current_volume = df['volume'].iloc[-1]
            rel_volume = f"{current_volume / avg_volume:.1f}x" if avg_volume > 0 else "N/A"
            
            # VWAP & ADX
            vwap = self.calc.vwap(df, period=20)
            adx = self.calc.adx(df)
            
            result = {
                'Ticker': ticker,
                'Price': round(current_price, 2),
                'Change%': f"{change_pct:+.2f}%",
                'RSI': round(rsi_current, 1),
                'MACD': round(float(macd_line.iloc[-1]), 3),
                'MACD_Signal': round(float(signal_line.iloc[-1]), 3),
                'MACD_Hist': round(macd_hist, 3),
                'ADX': round(adx, 1),
                'Trend': trend,
                'SMA_20': round(sma_20, 2),
                'SMA_50': round(sma_50, 2),
                'SMA_200': round(sma_200, 2),
                'BB_Upper': round(float(bb_upper.iloc[-1]), 2),
                'BB_Lower': round(float(bb_lower.iloc[-1]), 2),
                'ATR': round(atr_current, 2),
                'Stoch_K': round(float(stoch_k.iloc[-1]), 1),
                'Stoch_D': round(float(stoch_d.iloc[-1]), 1),
                'VWAP': round(vwap, 2),
                'OBV_Trend': obv_trend,
                'Volatility': volatility,
                'Divergence': divergence,
                'Volume_Rel': rel_volume,
                '52W_High': round(float(df['high'].max()), 2),
                '52W_Low': round(float(df['low'].min()), 2),
                'Status': 'OK',
                'Updated': dt.datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            
            logger.info(f"✅ {ticker}: ${current_price:.2f}, RSI={rsi_current:.1f}, Trend={trend}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing technicals for {ticker}: {e}")
            return {'Ticker': ticker, 'Status': f"ERROR: {str(e)[:50]}"}
