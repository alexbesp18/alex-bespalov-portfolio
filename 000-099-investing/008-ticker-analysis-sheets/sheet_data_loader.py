#!/usr/bin/env python3
"""
Sheet Data Loader - Pre-fetch Technical Data + Transcripts for Hype Scorer
===========================================================================
Reads tickers from Google Sheet, fetches technical data (Twelve Data) and
earnings transcripts (defeatbeta), summarizes with Grok, writes back to helper tabs.

Usage:
  python sheet_data_loader.py
  python sheet_data_loader.py --config custom_config.json
  python sheet_data_loader.py --verbose --dry-run

Requirements:
  pip install gspread google-auth pandas numpy requests defeatbeta-api duckdb
"""

import argparse
import json
import time
import sys
import datetime as dt
from pathlib import Path
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor

import requests
import pandas as pd
import numpy as np

# Google Sheets
import gspread
from google.oauth2.service_account import Credentials

# defeatbeta (optional)
DEFEATBETA_AVAILABLE = True
try:
    from defeatbeta_api.data.ticker import Ticker
except ImportError:
    DEFEATBETA_AVAILABLE = False
    print("⚠️  defeatbeta-api not installed. Transcripts will be skipped.")
    print("   Install with: pip install defeatbeta-api duckdb")


# ============================================================================
# TECHNICAL CALCULATOR (from consolidated_stock_analyzer_v4.py)
# ============================================================================

class TechnicalCalculator:
    """Calculate all technical indicators from raw OHLCV data"""
    
    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        return data.rolling(window=period).mean()
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        return data.ewm(span=period, adjust=False).mean()
    
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
    def bollinger_bands(close_prices: pd.Series, period: int = 20, num_std: float = 2.0) -> tuple:
        sma = close_prices.rolling(window=period).mean()
        std = close_prices.rolling(window=period).std()
        upper = sma + (std * num_std)
        lower = sma - (std * num_std)
        return upper, sma, lower
    
    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        high, low, close = df['high'], df['low'], df['close']
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    @staticmethod
    def stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> tuple:
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        k = 100 * ((df['close'] - low_min) / (high_max - low_min))
        d = k.rolling(window=d_period).mean()
        return k, d
    
    @staticmethod
    def adx(df: pd.DataFrame, period: int = 14) -> float:
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
        return float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else 20.0
    
    @staticmethod
    def obv(df: pd.DataFrame) -> pd.Series:
        return (df['volume'] * np.where(df['close'].diff() > 0, 1, -1)).cumsum()
    
    @staticmethod
    def vwap(df: pd.DataFrame, period: int = 20) -> float:
        recent_df = df.tail(period)
        total_volume = recent_df['volume'].sum()
        if total_volume > 0:
            return float((recent_df['close'] * recent_df['volume']).sum() / total_volume)
        return float(df['close'].iloc[-1])


# ============================================================================
# TWELVE DATA FETCHER
# ============================================================================

class TwelveDataFetcher:
    """Fetch OHLCV data from Twelve Data and calculate all indicators (1 credit/stock)"""
    
    def __init__(self, api_key: str, output_size: int = 365, verbose: bool = False):
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com"
        self.output_size = output_size
        self.calc = TechnicalCalculator()
        self.verbose = verbose
    
    def fetch_and_calculate(self, ticker: str) -> Optional[Dict]:
        """Fetch data and calculate all indicators. Returns dict for sheet row."""
        if self.verbose:
            print(f"    📊 Fetching {ticker} from Twelve Data...")
        
        try:
            url = f"{self.base_url}/time_series"
            params = {
                'symbol': ticker,
                'interval': '1day',
                'outputsize': self.output_size,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            # Check for errors
            if 'code' in data and data['code'] != 200:
                error_msg = data.get('message', 'Unknown API error')
                if self.verbose:
                    print(f"    ❌ API error: {error_msg}")
                return {'Ticker': ticker, 'Status': f"ERROR: {error_msg}"}
            
            if 'values' not in data or not data['values']:
                if self.verbose:
                    print(f"    ❌ No data returned")
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
                if self.verbose:
                    print(f"    ❌ Insufficient data: {len(df)} bars")
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
            
            # Moving averages
            sma_20 = float(self.calc.sma(df['close'], 20).iloc[-1])
            sma_50 = float(self.calc.sma(df['close'], 50).iloc[-1])
            sma_200 = float(self.calc.sma(df['close'], min(200, len(df))).iloc[-1])
            
            # Trend classification
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
            
            # 52-week high/low
            high_52w = float(df['high'].max())
            low_52w = float(df['low'].min())
            
            # VWAP
            vwap = self.calc.vwap(df, period=20)
            
            # ADX
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
                '52W_High': round(high_52w, 2),
                '52W_Low': round(low_52w, 2),
                'Status': 'OK',
                'Updated': dt.datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            
            if self.verbose:
                print(f"    ✅ {ticker}: ${current_price:.2f}, RSI={rsi_current:.1f}, Trend={trend}")
            
            return result
            
        except requests.exceptions.Timeout:
            return {'Ticker': ticker, 'Status': "ERROR: Request timeout"}
        except Exception as e:
            return {'Ticker': ticker, 'Status': f"ERROR: {str(e)[:50]}"}


# ============================================================================
# DEFEATBETA TRANSCRIPT FETCHER
# ============================================================================

class TranscriptFetcher:
    """Fetch earnings transcripts from defeatbeta-api"""
    
    def __init__(self, min_chars: int = 600, earliest_year_offset: int = 1, verbose: bool = False):
        self.min_chars = min_chars
        self.earliest_year = dt.date.today().year - earliest_year_offset
        self.verbose = verbose
    
    def fetch_latest(self, ticker: str) -> Optional[Dict]:
        """Fetch the latest transcript for a ticker. Returns dict with text and metadata."""
        if not DEFEATBETA_AVAILABLE:
            return {'Ticker': ticker, 'Status': "ERROR: defeatbeta not installed"}
        
        if self.verbose:
            print(f"    📝 Fetching transcript for {ticker}...")
        
        try:
            tkr = Ticker(ticker)
            tr = tkr.earning_call_transcripts()
            df_list = tr.get_transcripts_list()
            
            try:
                df = pd.DataFrame(df_list)
            except Exception:
                df = df_list if isinstance(df_list, pd.DataFrame) else pd.DataFrame(df_list)
            
            if df.empty:
                if self.verbose:
                    print(f"    ⚠️  No transcripts found")
                return {'Ticker': ticker, 'Status': 'NO_DATA', 'Period': 'N/A'}
            
            # Filter by year
            if 'fiscal_year' in df.columns:
                df = df[df['fiscal_year'].astype(int) >= self.earliest_year]
            
            if df.empty:
                if self.verbose:
                    print(f"    ⚠️  No recent transcripts (>= {self.earliest_year})")
                return {'Ticker': ticker, 'Status': 'NO_DATA', 'Period': 'N/A'}
            
            # Sort by date
            sort_cols = [c for c in ['report_date', 'fiscal_year', 'fiscal_quarter'] if c in df.columns]
            if sort_cols:
                df = df.sort_values(sort_cols, ascending=[False] * len(sort_cols))
            
            # Get the latest transcript
            row = df.iloc[0]
            y = int(row.get('fiscal_year', 0))
            q = int(row.get('fiscal_quarter', 0))
            report_date = str(row.get('report_date', 'N/A'))
            period = f"{y}Q{q}"
            
            # Fetch full transcript
            tx = tr.get_transcript(y, q)
            
            # Extract text
            try:
                tdf = pd.DataFrame(tx)
            except Exception:
                tdf = tx if isinstance(tx, pd.DataFrame) else pd.DataFrame(tx)
            
            if not tdf.empty and 'content' in tdf.columns:
                text = "\n".join(str(x) for x in tdf['content'].tolist())
            elif isinstance(tx, dict):
                text = self._normalize_text(tx)
            elif isinstance(tx, list):
                text = self._normalize_text(tx)
            else:
                text = ""
            
            text = (text or "").strip()
            char_count = len(text)
            
            if char_count < self.min_chars:
                if self.verbose:
                    print(f"    ⚠️  Transcript too short: {char_count} chars")
                return {
                    'Ticker': ticker,
                    'Period': period,
                    'Earnings_Date': report_date,
                    'Char_Count': char_count,
                    'Status': f'NO_DATA (only {char_count} chars)',
                    'Full_Text': ''
                }
            
            if self.verbose:
                print(f"    ✅ {ticker} {period}: {char_count:,} chars")
            
            return {
                'Ticker': ticker,
                'Period': period,
                'Earnings_Date': report_date,
                'Char_Count': char_count,
                'Status': 'OK',
                'Full_Text': text
            }
            
        except Exception as e:
            if self.verbose:
                print(f"    ❌ Error: {e}")
            return {'Ticker': ticker, 'Status': f"ERROR: {str(e)[:50]}"}
    

    
    def _normalize_text(self, obj: Any) -> str:
        """Convert various transcript formats to plain text."""
        if obj is None:
            return ""
        if isinstance(obj, str):
            return obj
        if isinstance(obj, list):
            parts = []
            for item in obj:
                if isinstance(item, dict):
                    speaker = item.get('speaker') or item.get('name', '')
                    content = item.get('text') or item.get('content', '')
                    parts.append(f"{speaker}: {content}" if speaker else str(content))
                else:
                    parts.append(str(item))
            return "\n".join(parts)
        if isinstance(obj, dict):
            for k in ('transcript', 'prepared_remarks', 'q_and_a', 'content', 'text'):
                if k in obj:
                    return self._normalize_text(obj[k])
            try:
                return json.dumps(obj, ensure_ascii=False, indent=2)
            except Exception:
                return str(obj)
        return str(obj)


# ============================================================================
# GROK SUMMARIZER
# ============================================================================

class GrokSummarizer:
    """Use Grok 4.1 to summarize earnings transcripts"""
    
    def __init__(self, api_key: str, model: str = 'grok-4-1-fast-reasoning', 
                 max_tokens: int = 400, verbose: bool = False):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.base_url = 'https://api.x.ai/v1/chat/completions'
        self.verbose = verbose
    
    def summarize(self, ticker: str, period: str, text: str) -> Dict:
        """Summarize a transcript. Returns dict with Key_Metrics, Guidance, Tone, Summary."""
        if not text or len(text) < 500:
            return {
                'Key_Metrics': 'N/A',
                'Guidance': 'N/A',
                'Tone': 'N/A',
                'Summary': 'Transcript too short to summarize'
            }
        
        if self.verbose:
            print(f"    🤖 Summarizing {ticker} {period} with Grok...")
        
        # Truncate text to avoid token limits (roughly 4 chars per token)
        max_chars = 30000  # ~7500 tokens of input
        truncated_text = text[:max_chars] if len(text) > max_chars else text
        
        prompt = f"""Analyze this earnings call transcript for {ticker} ({period}).

TRANSCRIPT (may be truncated):
{truncated_text}

Provide a structured summary with exactly these 4 fields:

KEY_METRICS: Extract revenue and EPS vs expectations. Use format like "Rev: $X.XB (+X% YoY, beat by X%), EPS: $X.XX (beat/miss by $X.XX)". If exact numbers unclear, use directional language like "beat expectations" or "missed estimates".

GUIDANCE: Summarize forward guidance. Did they raise, maintain, or lower? Include any specific targets mentioned.

TONE: One word only: Bullish, Cautious, Neutral, or Bearish. Base this on management's language and outlook.

SUMMARY: 2-3 sentences capturing the most important themes, risks, or opportunities mentioned.

OUTPUT FORMAT (use exactly this format):
KEY_METRICS: [your metrics here]
GUIDANCE: [your guidance here]
TONE: [one word]
SUMMARY: [your summary here]

Do not include any other text or explanation."""

        try:
            response = requests.post(
                self.base_url,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': self.model,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'temperature': 0.2,
                    'max_tokens': self.max_tokens,
                    'search': False  # No web search needed for summarization
                },
                timeout=60
            )
            
            if response.status_code == 429:
                if self.verbose:
                    print(f"    ⚠️  Rate limited, skipping summary")
                return self._empty_summary("Rate limited")
            
            if response.status_code != 200:
                if self.verbose:
                    print(f"    ❌ API error: {response.status_code}")
                return self._empty_summary(f"API error {response.status_code}")
            
            data = response.json()
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            if not content:
                return self._empty_summary("Empty response")
            
            # Parse the response
            result = self._parse_summary(content)
            
            if self.verbose:
                print(f"    ✅ Summary complete: Tone={result['Tone']}")
            
            return result
            
        except requests.exceptions.Timeout:
            return self._empty_summary("Request timeout")
        except Exception as e:
            if self.verbose:
                print(f"    ❌ Error: {e}")
            return self._empty_summary(str(e)[:30])
    
    def analyze_technicals(self, ticker: str, tech_data: Dict) -> Dict:
        """Analyze technical indicators and return a bullish score (1-10)."""
        if self.verbose:
            print(f"    🤖 Analyzing technicals for {ticker} with Grok...")
            
        # Format technicals for the prompt
        tech_str = "\n".join([f"{k}: {v}" for k, v in tech_data.items() if k not in ('Ticker', 'Status', 'Updated')])
        
        prompt = f"""Analyze the technical indicators for {ticker} and provide a "Bullish Score" from 1 to 10.

TECHNICAL INDICATORS:
{tech_str}

SCORING GUIDE:
1-3: Bearish (Downtrend, negative momentum, breakdown)
4-6: Neutral (Sideways, mixed signals, consolidation)
7-10: Bullish (Uptrend, positive momentum, breakout)

OUTPUT FORMAT (JSON only):
{{
  "Bullish_Score": <int 1-10>,
  "Bullish_Reason": "<one short sentence explaining why>"
}}"""

        try:
            response = requests.post(
                self.base_url,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': self.model,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'temperature': 0.2,
                    'max_tokens': 100,
                    'response_format': {'type': 'json_object'}
                },
                timeout=30
            )
            
            if response.status_code != 200:
                if self.verbose:
                    print(f"    ❌ API error: {response.status_code}")
                return {'Bullish_Score': '', 'Bullish_Reason': f"API Error {response.status_code}"}
            
            data = response.json()
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            try:
                result = json.loads(content)
                return {
                    'Bullish_Score': result.get('Bullish_Score', ''),
                    'Bullish_Reason': result.get('Bullish_Reason', '')
                }
            except json.JSONDecodeError:
                return {'Bullish_Score': '', 'Bullish_Reason': "Failed to parse JSON"}
                
        except Exception as e:
            if self.verbose:
                print(f"    ❌ Error: {e}")
            return {'Bullish_Score': '', 'Bullish_Reason': str(e)[:30]}

    def _parse_summary(self, content: str) -> Dict:
        """Parse Grok's response into structured fields."""
        result = {
            'Key_Metrics': 'N/A',
            'Guidance': 'N/A',
            'Tone': 'Neutral',
            'Summary': 'N/A'
        }
        
        lines = content.strip().split('\n')
        current_field = None
        current_value = []
        
        for line in lines:
            line = line.strip()
            if line.upper().startswith('KEY_METRICS:'):
                if current_field:
                    result[current_field] = ' '.join(current_value).strip()
                current_field = 'Key_Metrics'
                current_value = [line.split(':', 1)[1].strip() if ':' in line else '']
            elif line.upper().startswith('GUIDANCE:'):
                if current_field:
                    result[current_field] = ' '.join(current_value).strip()
                current_field = 'Guidance'
                current_value = [line.split(':', 1)[1].strip() if ':' in line else '']
            elif line.upper().startswith('TONE:'):
                if current_field:
                    result[current_field] = ' '.join(current_value).strip()
                current_field = 'Tone'
                tone_val = line.split(':', 1)[1].strip() if ':' in line else 'Neutral'
                current_value = [tone_val.split()[0] if tone_val else 'Neutral']  # First word only
            elif line.upper().startswith('SUMMARY:'):
                if current_field:
                    result[current_field] = ' '.join(current_value).strip()
                current_field = 'Summary'
                current_value = [line.split(':', 1)[1].strip() if ':' in line else '']
            elif current_field and line:
                current_value.append(line)
        
        # Don't forget the last field
        if current_field:
            result[current_field] = ' '.join(current_value).strip()
        
        # Truncate long values for sheet
        for key in result:
            if len(result[key]) > 500:
                result[key] = result[key][:497] + '...'
        
        return result
    
    def _empty_summary(self, reason: str) -> Dict:
        return {
            'Key_Metrics': 'N/A',
            'Guidance': 'N/A',
            'Tone': 'N/A',
            'Summary': f'Summary unavailable: {reason}'
        }


# ============================================================================
# GOOGLE SHEETS MANAGER
# ============================================================================

class SheetManager:
    """Manage Google Sheets read/write operations"""
    
    def __init__(self, credentials_file: str, spreadsheet_name: str, verbose: bool = False):
        self.verbose = verbose
        
        if verbose:
            print(f"📊 Connecting to Google Sheets...")
        
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
        self.gc = gspread.authorize(creds)
        
        try:
            self.spreadsheet = self.gc.open(spreadsheet_name)
            if verbose:
                print(f"   ✅ Connected to: {spreadsheet_name}")
        except gspread.SpreadsheetNotFound:
            raise ValueError(f"Spreadsheet '{spreadsheet_name}' not found. "
                           "Make sure you shared it with the service account.")
    
    def get_tickers(self, tab_name: str, column: str = 'A', start_row: int = 2) -> List[str]:
        """Read tickers from specified tab and column."""
        try:
            sheet = self.spreadsheet.worksheet(tab_name)
        except gspread.WorksheetNotFound:
            raise ValueError(f"Tab '{tab_name}' not found in spreadsheet")
        
        # Get all values in the column
        col_idx = ord(column.upper()) - ord('A') + 1
        values = sheet.col_values(col_idx)
        
        # Filter: skip header rows, remove empty, uppercase
        tickers = []
        for i, val in enumerate(values):
            if i < start_row - 1:  # Skip header rows
                continue
            val = str(val).strip().upper()
            if val and val not in ('TICKER', 'SYMBOL', ''):
                tickers.append(val)
        
        return tickers
    
    def get_existing_tickers(self, tab_name: str, column: str = 'A', start_row: int = 2) -> List[str]:
        """Read tickers from specified tab to see what's already there."""
        try:
            return self.get_tickers(tab_name, column, start_row)
        except (ValueError, gspread.WorksheetNotFound):
            return []
    
    def write_tech_data(self, tab_name: str, data: List[Dict], append: bool = False):
        """Write technical data to specified tab."""
        if not data:
            return
        
        # Get or create sheet
        try:
            sheet = self.spreadsheet.worksheet(tab_name)
        except gspread.WorksheetNotFound:
            sheet = self.spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=30)
            append = False  # New sheet, can't append
        
        # Define column order
        columns = [
            'Ticker', 'Bullish_Score', 'Price', 'Change%', 'RSI', 'MACD', 'MACD_Signal', 'MACD_Hist',
            'ADX', 'Trend', 'SMA_20', 'SMA_50', 'SMA_200', 'BB_Upper', 'BB_Lower',
            'ATR', 'Stoch_K', 'Stoch_D', 'VWAP', 'OBV_Trend', 'Volatility',
            'Divergence', 'Volume_Rel', '52W_High', '52W_Low', 'Status', 'Updated', 'Bullish_Reason'
        ]
        
        # Build rows
        rows = []
        if not append:
            rows.append(columns)  # Header only if not appending
            
        for d in data:
            row = [d.get(col, '') for col in columns]
            rows.append(row)
        
        # Write
        if append:
            sheet.append_rows(rows)
            if self.verbose:
                print(f"   ✅ Appended {len(data)} rows to {tab_name}")
        else:
            sheet.clear()
            sheet.update(rows, 'A1')
            if self.verbose:
                print(f"   ✅ Wrote {len(data)} rows to {tab_name}")
    
    def write_transcripts(self, tab_name: str, data: List[Dict], append: bool = False):
        """Write transcript data to specified tab."""
        if not data:
            return
        
        # Get or create sheet
        try:
            sheet = self.spreadsheet.worksheet(tab_name)
        except gspread.WorksheetNotFound:
            sheet = self.spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=15)
            append = False
        
        # Define column order
        columns = [
            'Ticker', 'Period', 'Earnings_Date', 'Char_Count', 
            'Key_Metrics', 'Guidance', 'Tone', 'Summary', 'Status', 'Updated', 'Days_Since_Earnings'
        ]
        
        # Build rows
        rows = []
        if not append:
            rows.append(columns)
            
        for d in data:
            row = [d.get(col, '') for col in columns]
            rows.append(row)
        
        # Write
        if append:
            sheet.append_rows(rows)
            if self.verbose:
                print(f"   ✅ Appended {len(data)} rows to {tab_name}")
        else:
            sheet.clear()
            sheet.update(rows, 'A1')
            if self.verbose:
                print(f"   ✅ Wrote {len(data)} rows to {tab_name}")
        
        # Apply conditional formatting to Days_Since_Earnings (Column K)
        self.apply_formatting(tab_name)

    def apply_formatting(self, tab_name: str):
        """Apply conditional formatting to Days_Since_Earnings column."""
        try:
            sheet = self.spreadsheet.worksheet(tab_name)
            
            # Column K is index 10 (0-based)
            # Rules: > 90 (Yellow), > 180 (Red)
            
            # Clear existing rules (this might clear all filters, which is fine)
            sheet.clear_basic_filter()
            
            requests = [
                {
                    "addConditionalFormatRule": {
                        "rule": {
                            "ranges": [{"sheetId": sheet.id, "startColumnIndex": 10, "endColumnIndex": 11, "startRowIndex": 1}],
                            "booleanRule": {
                                "condition": {"type": "NUMBER_GREATER", "values": [{"userEnteredValue": "180"}]},
                                "format": {"backgroundColor": {"red": 1, "green": 0.8, "blue": 0.8}, "textFormat": {"foregroundColor": {"red": 0, "green": 0, "blue": 0}}}
                            }
                        },
                        "index": 0
                    }
                },
                {
                    "addConditionalFormatRule": {
                        "rule": {
                            "ranges": [{"sheetId": sheet.id, "startColumnIndex": 10, "endColumnIndex": 11, "startRowIndex": 1}],
                            "booleanRule": {
                                "condition": {"type": "NUMBER_GREATER", "values": [{"userEnteredValue": "90"}]},
                                "format": {"backgroundColor": {"red": 1, "green": 1, "blue": 0.8}, "textFormat": {"foregroundColor": {"red": 0, "green": 0, "blue": 0}}}
                            }
                        },
                        "index": 1
                    }
                }
            ]
            
            # Execute batch update
            self.spreadsheet.batch_update({"requests": requests})
            if self.verbose:
                print(f"   🎨 Applied conditional formatting to {tab_name}")
                
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️  Could not apply formatting: {e}")


# ============================================================================
# MAIN LOADER CLASS
# ============================================================================

class SheetDataLoader:
    """Main orchestrator for loading data into Google Sheets"""
    
    def __init__(self, config_path: str, verbose: bool = False, dry_run: bool = False, limit: int = 0, batch_size: int = 0, clean: bool = False):
        self.verbose = verbose
        self.dry_run = dry_run
        self.limit = limit
        self.batch_size = batch_size
        self.clean = clean
        
        # Load config
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        gs_config = self.config['google_sheets']
        td_config = self.config['twelve_data']
        grok_config = self.config['grok']
        db_config = self.config.get('defeatbeta', {})
        
        # Initialize components
        self.sheet_manager = SheetManager(
            credentials_file=gs_config['credentials_file'],
            spreadsheet_name=gs_config['spreadsheet_name'],
            verbose=verbose
        )
        
        self.twelve_data = TwelveDataFetcher(
            api_key=td_config['api_key'],
            output_size=td_config.get('output_size', 365),
            verbose=verbose
        )
        
        self.transcript_fetcher = TranscriptFetcher(
            min_chars=db_config.get('min_chars', 600),
            earliest_year_offset=db_config.get('earliest_year_offset', 1),
            verbose=verbose
        )
        
        self.summarizer = GrokSummarizer(
            api_key=grok_config['api_key'],
            model=grok_config.get('model', 'grok-4-1-fast-reasoning'),
            max_tokens=grok_config.get('max_summary_tokens', 400),
            verbose=verbose
        ) if grok_config.get('summarization_enabled', True) else None
        
        # Config values
        self.main_tab = gs_config['main_tab']
        self.ticker_column = gs_config.get('ticker_column', 'A')
        self.start_row = gs_config.get('start_row', 2)
        self.tech_data_tab = gs_config['tech_data_tab']
        self.transcripts_tab = gs_config['transcripts_tab']
        self.rate_limit_sleep = td_config.get('rate_limit_sleep', 0.5)
    
    def run(self):
        """Main execution flow."""
        print("\n" + "=" * 60)
        print("SHEET DATA LOADER")
        print("=" * 60)
        
        # Get tickers
        print(f"\n📋 Reading tickers from '{self.main_tab}' tab, column {self.ticker_column}...")
        tickers = self.sheet_manager.get_tickers(
            self.main_tab, self.ticker_column, self.start_row
        )
        
        if not tickers:
            print("❌ No tickers found!")
            return
        
        print(f"   Found {len(tickers)} tickers: {', '.join(tickers[:10])}{'...' if len(tickers) > 10 else ''}")
        
        # Check for existing tickers if batching or just to be smart
        existing_tickers = []
        if not self.dry_run and not self.clean:
            print(f"   🔍 Checking for already processed tickers in '{self.tech_data_tab}'...")
            existing_tickers = self.sheet_manager.get_existing_tickers(self.tech_data_tab)
            if existing_tickers:
                print(f"   found {len(existing_tickers)} existing tickers.")
        elif self.clean:
            print(f"   🧹 CLEAN RUN: Ignoring existing data, will overwrite.")
        
        # Filter out existing
        tickers_to_process = [t for t in tickers if t not in existing_tickers]
        
        if len(tickers_to_process) < len(tickers):
            print(f"   ℹ️  Skipping {len(tickers) - len(tickers_to_process)} already processed tickers.")
        
        if not tickers_to_process:
            print("✅ All tickers already processed! Nothing to do.")
            return

        # Apply limit (on remaining tickers)
        if self.limit > 0:
            tickers_to_process = tickers_to_process[:self.limit]
            print(f"   ⚠️  LIMITING run to {self.limit} tickers")
            
        # Apply batch size
        if self.batch_size > 0:
            if len(tickers_to_process) > self.batch_size:
                tickers_to_process = tickers_to_process[:self.batch_size]
                print(f"   📦 BATCH MODE: Processing next {self.batch_size} tickers")
        
        print(f"   🚀 Starting run for {len(tickers_to_process)} tickers: {', '.join(tickers_to_process[:5])}...")
        
        # Fetch technical data
        print(f"\n📊 FETCHING TECHNICAL DATA (Twelve Data)")
        print("-" * 40)
        tech_results = []
        
        for i, ticker in enumerate(tickers_to_process):
            print(f"[{i+1}/{len(tickers_to_process)}] {ticker}")
            result = self.twelve_data.fetch_and_calculate(ticker)
            if result:
                # Analyze technicals with Grok
                if self.summarizer:
                    ai_analysis = self.summarizer.analyze_technicals(ticker, result)
                    result.update(ai_analysis)
                
                tech_results.append(result)
            
            # Rate limiting
            if i < len(tickers_to_process) - 1:
                time.sleep(self.rate_limit_sleep)
        
        # Fetch transcripts
        print(f"\n📝 FETCHING TRANSCRIPTS (defeatbeta)")
        print("-" * 40)
        transcript_results = []
        
        for i, ticker in enumerate(tickers_to_process):
            print(f"[{i+1}/{len(tickers_to_process)}] {ticker}")
            result = self.transcript_fetcher.fetch_latest(ticker)
            
            if result and result.get('Status') == 'OK' and result.get('Full_Text'):
                # Summarize with Grok
                if self.summarizer:
                    summary = self.summarizer.summarize(
                        ticker, 
                        result.get('Period', 'N/A'),
                        result.get('Full_Text', '')
                    )
                    result.update(summary)
                
                # Remove full text (too long for sheet)
                result.pop('Full_Text', None)
            
            # Calculate Days Since Earnings
            if result and result.get('Earnings_Date') and result.get('Earnings_Date') != 'N/A':
                try:
                    earnings_date = dt.datetime.strptime(result['Earnings_Date'], '%Y-%m-%d').date()
                    days_since = (dt.date.today() - earnings_date).days
                    result['Days_Since_Earnings'] = days_since
                except Exception:
                    result['Days_Since_Earnings'] = 'N/A'
            else:
                if result:
                    result['Days_Since_Earnings'] = 'N/A'
            
            if result:
                result['Updated'] = dt.datetime.now().strftime('%Y-%m-%d %H:%M')
                transcript_results.append(result)
            
            time.sleep(0.5)  # Be nice to defeatbeta
        
        # Write to sheets
        if not self.dry_run:
            print(f"\n💾 WRITING TO GOOGLE SHEETS")
            print("-" * 40)
            
            # Determine if we should append (if we found existing tickers, we append)
            # Or if we are in batch mode, we generally append unless it's the very first run
            # Safest logic: if existing_tickers is not empty, we append. 
            # If existing_tickers is empty, we overwrite (start fresh).
            should_append = len(existing_tickers) > 0
            
            self.sheet_manager.write_tech_data(self.tech_data_tab, tech_results, append=should_append)
            self.sheet_manager.write_transcripts(self.transcripts_tab, transcript_results, append=should_append)
        
        # Summary
        print(f"\n" + "=" * 60)
        print("COMPLETE")
        print("=" * 60)
        
        tech_ok = sum(1 for r in tech_results if r.get('Status') == 'OK')
        trans_ok = sum(1 for r in transcript_results if r.get('Status') == 'OK')
        
        print(f"Technical data: {tech_ok}/{len(tickers_to_process)} successful")
        print(f"Transcripts:    {trans_ok}/{len(tickers_to_process)} successful")
        
        if self.dry_run:
            print("\n⚠️  DRY RUN - No data was written to sheets")
        else:
            print(f"\n✅ Data written to tabs: '{self.tech_data_tab}' and '{self.transcripts_tab}'")
            print(f"   Now run the Hype Scorer in Google Sheets!")


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Pre-fetch technical data and transcripts for Google Sheets Hype Scorer'
    )
    parser.add_argument(
        '--config', '-c',
        default='sheet_loader_config.json',
        help='Path to configuration file (default: sheet_loader_config.json)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print detailed progress information'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Fetch data but do not write to sheets'
    )
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=0,
        help='Limit the number of tickers to process (0 = all)'
    )
    
    parser.add_argument(
        '--batch-size', '-b',
        type=int,
        default=0,
        help='Batch size: process N tickers then stop (resumes from last run)'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Start fresh: ignore existing data and overwrite sheets'
    )
    
    args = parser.parse_args()
    
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        print(f"   Create it using the template in SETUP_GUIDE.md")
        sys.exit(1)
    
    try:
        loader = SheetDataLoader(
            config_path=str(config_path),
            verbose=args.verbose,
            dry_run=args.dry_run,
            limit=args.limit,
            batch_size=args.batch_size,
            clean=args.clean
        )
        loader.run()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
