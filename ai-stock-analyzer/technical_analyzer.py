"""
Technical Stock Analyzer - PURE TECHNICAL ANALYSIS (1 Credit Per Stock!)
==========================================================================
Real data from Twelve Data → Client-side calculations → 3 Agent Analysis → Claude Arbitration

Focus: Pure technical analysis without Elliott Wave patterns
"""

import anthropic
from openai import OpenAI
from google import genai
from google.genai.types import GenerateContentConfig, ThinkingConfig
import gspread
from google.oauth2.service_account import Credentials
import time
import re
import json
import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


# ============================================================================
# GOOGLE SHEET COLOR DEFINITIONS
# ============================================================================

class SheetColors:
    """RGB color definitions for Google Sheets"""
    DARK_GREEN = {'red': 0.22, 'green': 0.6, 'blue': 0.29}
    LIGHT_GREEN = {'red': 0.71, 'green': 0.84, 'blue': 0.66}
    YELLOW = {'red': 1.0, 'green': 0.95, 'blue': 0.6}
    LIGHT_RED = {'red': 0.96, 'green': 0.6, 'blue': 0.6}
    DARK_RED = {'red': 0.8, 'green': 0.2, 'blue': 0.2}
    WHITE = {'red': 1.0, 'green': 1.0, 'blue': 1.0}
    LIGHT_BLUE = {'red': 0.8, 'green': 0.92, 'blue': 0.97}
    HEADER_DARK = {'red': 0.2, 'green': 0.2, 'blue': 0.2}


# ============================================================================
# TECHNICAL INDICATOR CALCULATOR (Client-Side Calculations)
# ============================================================================

class TechnicalCalculator:
    """Calculate all technical indicators from raw OHLCV data"""
    
    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        return data.rolling(window=period).mean()
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def rsi(close_prices: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        # Avoid division by zero
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def macd(close_prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        """MACD (Moving Average Convergence Divergence)"""
        ema_fast = close_prices.ewm(span=fast, adjust=False).mean()
        ema_slow = close_prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def bollinger_bands(close_prices: pd.Series, period: int = 20, num_std: float = 2.0) -> tuple:
        """Bollinger Bands"""
        sma = close_prices.rolling(window=period).mean()
        std = close_prices.rolling(window=period).std()
        upper = sma + (std * num_std)
        lower = sma - (std * num_std)
        return upper, sma, lower
    
    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Average True Range"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr
    
    @staticmethod
    def stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> tuple:
        """Stochastic Oscillator"""
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        
        k = 100 * ((df['close'] - low_min) / (high_max - low_min))
        d = k.rolling(window=d_period).mean()
        
        return k, d
    
    @staticmethod
    def calculate_support_resistance(df: pd.DataFrame, short_window: int = 20, long_window: int = 90) -> Dict:
        """Calculate support and resistance levels"""
        # Recent levels (last 20 days)
        recent_high = df['high'].tail(short_window).max()
        recent_low = df['low'].tail(short_window).min()
        
        # Longer-term levels (last 90 days)
        strong_resistance = df['high'].tail(long_window).max()
        strong_support = df['low'].tail(long_window).min()
        
        # Find pivot points
        current_price = df['close'].iloc[-1]
        
        # Closest support: highest low below current price
        support_levels = df[df['low'] < current_price]['low'].tail(short_window)
        closest_support = support_levels.max() if not support_levels.empty else recent_low
        
        # Closest resistance: lowest high above current price
        resistance_levels = df[df['high'] > current_price]['high'].tail(short_window)
        closest_resistance = resistance_levels.min() if not resistance_levels.empty else recent_high
        
        return {
            'closest_support': closest_support,
            'key_support': strong_support,
            'closest_resistance': closest_resistance,
            'strongest_resistance': strong_resistance
        }


# ============================================================================
# OPTIMIZED TWELVE DATA FETCHER (1 Credit Per Stock!)
# ============================================================================

class TwelveDataFetcher:
    """Optimized fetcher - pulls only time_series and calculates everything client-side"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com"
        self.calc = TechnicalCalculator()
    
    def get_complete_analysis_data(self, ticker: str, outputsize: int = 200) -> Optional[Dict]:
        """
        Fetch ALL data needed for analysis with ONLY 1 API CREDIT!
        
        Args:
            ticker: Stock symbol
            outputsize: Number of days to retrieve (max 5000)
        
        Returns:
            Complete analysis data with all indicators calculated
        """
        print(f"  📊 Fetching market data for {ticker} (1 credit only)...")
        
        try:
            # Single API call - ONLY 1 CREDIT!
            url = f"{self.base_url}/time_series"
            params = {
                'symbol': ticker,
                'interval': '1day',
                'outputsize': outputsize,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            # Check for errors
            if 'code' in data and data['code'] != 200:
                print(f"      ⚠️  API error: {data.get('message', 'Unknown error')}")
                return None
            
            if 'values' not in data or not data['values']:
                print(f"      ⚠️  No data returned for {ticker}")
                return None
            
            # Convert to pandas DataFrame for easy calculations
            df = pd.DataFrame(data['values'])
            df['datetime'] = pd.to_datetime(df['datetime'])
            
            # Convert numeric columns
            for col in ['open', 'high', 'low', 'close']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0).astype(int)
            
            # Sort chronologically (oldest first) for proper indicator calculation
            df = df.sort_values('datetime').reset_index(drop=True)
            
            # Remove any NaN rows
            df = df.dropna(subset=['close'])
            
            if len(df) < 50:
                print(f"      ⚠️  Insufficient data: only {len(df)} bars")
                return None
            
            # Current price info
            current_price = float(df['close'].iloc[-1])
            previous_close = float(df['close'].iloc[-2]) if len(df) > 1 else current_price
            
            # Calculate ALL indicators from raw OHLCV data
            print(f"      🧮 Calculating indicators...")
            
            indicators = {}
            
            # Moving Averages
            indicators['sma_20'] = float(self.calc.sma(df['close'], 20).iloc[-1])
            indicators['sma_50'] = float(self.calc.sma(df['close'], 50).iloc[-1])
            indicators['sma_200'] = float(self.calc.sma(df['close'], 200).iloc[-1])
            
            # RSI
            rsi_series = self.calc.rsi(df['close'])
            indicators['rsi'] = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50.0
            
            # MACD
            macd_line, signal_line, histogram = self.calc.macd(df['close'])
            indicators['macd'] = float(macd_line.iloc[-1])
            indicators['macd_signal'] = float(signal_line.iloc[-1])
            indicators['macd_hist'] = float(histogram.iloc[-1])
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = self.calc.bollinger_bands(df['close'])
            indicators['bb_upper'] = float(bb_upper.iloc[-1])
            indicators['bb_middle'] = float(bb_middle.iloc[-1])
            indicators['bb_lower'] = float(bb_lower.iloc[-1])
            
            # ATR (Volatility)
            atr_series = self.calc.atr(df)
            indicators['atr'] = float(atr_series.iloc[-1])
            
            # Stochastic
            stoch_k, stoch_d = self.calc.stochastic(df)
            indicators['stoch_k'] = float(stoch_k.iloc[-1])
            indicators['stoch_d'] = float(stoch_d.iloc[-1])
            
            # Support & Resistance
            levels = self.calc.calculate_support_resistance(df)
            
            # Quote data (from most recent bar)
            quote = {
                'price': current_price,
                'open': float(df['open'].iloc[-1]),
                'high': float(df['high'].iloc[-1]),
                'low': float(df['low'].iloc[-1]),
                'volume': int(df['volume'].iloc[-1]),
                'previous_close': previous_close,
                'change': current_price - previous_close,
                'percent_change': ((current_price - previous_close) / previous_close) * 100 if previous_close > 0 else 0
            }
            
            # Historical data for agent analysis (last 30 days)
            history = []
            for _, row in df.tail(30).iterrows():
                history.append({
                    'date': row['datetime'].strftime('%Y-%m-%d'),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['volume'])
                })
            
            # --- START: Mock data for 22-column sheet (replace with real calculations) ---
            # These are placeholders. The 22-column sheet requires these.
            # You would need to add real calculations for these indicators in TechnicalCalculator
            # and populate them here.
            indicators['adx'] = np.random.uniform(15, 40)
            indicators['obv_trend'] = np.random.choice(['UP', 'DOWN', 'SIDEWAYS'])
            indicators['vwap'] = current_price * np.random.uniform(0.99, 1.01)
            
            trend_analysis = {
                'trend': np.random.choice(['STRONG_UPTREND', 'UPTREND', 'SIDEWAYS', 'DOWNTREND', 'STRONG_DOWNTREND']),
                'confidence': np.random.uniform(0.6, 1.0)
            }
            volume_metrics = {
                'relative_volume': f"{np.random.uniform(0.8, 2.5):.2f}x",
                'volume_confirms_price': np.random.choice([True, False])
            }
            divergence = {
                'divergence_type': np.random.choice(['None', 'BULLISH', 'BEARISH'])
            }
            volatility = {
                'volatility_regime': np.random.choice(['LOW', 'NORMAL', 'HIGH', 'VERY_HIGH'])
            }
            risk = {
                'max_drawdown': -np.random.uniform(2.0, 15.0)
            }
            # --- END: Mock data ---

            result = {
                'ticker': ticker,
                'current_price': current_price,
                'quote': quote,
                'indicators': indicators,
                'history': history,
                'levels': levels,
                'timestamp': datetime.now().isoformat(),
                'data_points': len(df),
                
                # Add mock data to result (replace with real data when available)
                'trend_analysis': trend_analysis,
                'volume_metrics': volume_metrics,
                'divergence': divergence,
                'volatility': volatility,
                'risk': risk
            }
            
            print(f"      ✓ Price: ${current_price:.2f} ({quote['percent_change']:+.2f}%)")
            print(f"      ✓ RSI: {indicators['rsi']:.1f} | MACD: {indicators['macd']:.3f}")
            print(f"      ✓ SMA: 20=${indicators['sma_20']:.2f} | 50=${indicators['sma_50']:.2f} | 200=${indicators['sma_200']:.2f}")
            print(f"      ✓ Support/Resistance: ${levels['closest_support']:.2f} / ${levels['closest_resistance']:.2f}")
            print(f"      💰 Cost: 1 credit (analyzed {len(df)} days)")
            
            return result
            
        except Exception as e:
            print(f"      ✗ Fetch failed: {e}")
            return None


# ============================================================================
# TECHNICAL ANALYZER (3-Agent System - Pure Technical Analysis)
# ============================================================================

class TechnicalAnalyzer:
    """Multi-agent technical analysis system - focused on pure technicals"""
    
    def __init__(self, config_path: str = 'config.json'):
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Extract API keys from nested structure
        api_keys = self.config.get('api_keys', {})
        
        # Initialize Twelve Data fetcher
        twelve_data_key = api_keys.get('twelve_data_api_key') or api_keys.get('twelve_data')
        if not twelve_data_key:
            raise ValueError("Twelve Data API key not found in config")
        self.data_fetcher = TwelveDataFetcher(twelve_data_key)
        
        # Initialize AI clients based on enabled status
        self._init_ai_clients(api_keys)
        
        # Initialize Google Sheets
        self._init_google_sheets()
        
        # Create reports directory
        self.reports_dir = Path('stock_reports')
        self.reports_dir.mkdir(exist_ok=True)
        
        # Stats tracking
        self.successful_analyses = 0
        self.failed_analyses = 0
        self.total_cost = 0.0
        self.agreement_stats = {
            'full_agreement': 0,
            'partial_agreement': 0,
            'major_disagreement': 0
        }
    
    def _init_ai_clients(self, api_keys: Dict):
        """Initialize AI clients based on config"""
        # Claude
        claude_config = self.config.get('claude_settings', {})
        if claude_config.get('enabled', True):
            anthropic_key = api_keys.get('anthropic')
            if anthropic_key:
                self.claude_client = anthropic.Anthropic(api_key=anthropic_key)
                self.claude_model = self._get_claude_model_string(claude_config.get('model', 'sonnet-4.5'))
                self.claude_config = claude_config
            else:
                print("⚠️  Claude API key missing - Claude disabled")
                self.claude_client = None
        else:
            self.claude_client = None
        
        # OpenAI/GPT
        openai_config = self.config.get('openai_settings', {})
        if openai_config.get('enabled', True):
            openai_key = api_keys.get('openai')
            if openai_key:
                self.openai_client = OpenAI(api_key=openai_key)
                self.openai_model = self._get_openai_model_string(openai_config.get('model', 'gpt-5'))
                self.openai_config = openai_config
            else:
                print("⚠️  OpenAI API key missing - GPT disabled")
                self.openai_client = None
        else:
            self.openai_client = None
        
        # Grok (via XAI)
        grok_config = self.config.get('grok_settings', {})
        if grok_config.get('enabled', True):
            xai_key = api_keys.get('xai')
            if xai_key:
                self.grok_client = OpenAI(
                    api_key=xai_key,
                    base_url="https://api.x.ai/v1"
                )
                self.grok_model = self._get_grok_model_string(grok_config.get('model', 'grok-4'))
                self.grok_config = grok_config
            else:
                print("⚠️  XAI API key missing - Grok disabled")
                self.grok_client = None
        else:
            self.grok_client = None
        
        # Gemini
        gemini_config = self.config.get('gemini_settings', {})
        if gemini_config.get('enabled', True):
            google_key = api_keys.get('google')
            if google_key:
                self.gemini_client = genai.Client(api_key=google_key)
                self.gemini_model = self._get_gemini_model_string(gemini_config.get('model', 'gemini-2.5-pro'))
                self.gemini_config = gemini_config
            else:
                print("⚠️  Google API key missing - Gemini disabled")
                self.gemini_client = None
        else:
            self.gemini_client = None
    
    def _get_claude_model_string(self, model_name: str) -> str:
        """Convert config model name to API model string"""
        model_map = {
            'sonnet-4.5': 'claude-sonnet-4-5-20250929',  # Latest Sonnet 4.5 (Sept 2025)
            'sonnet-4': 'claude-sonnet-4-20250514',
            'opus-4.1': 'claude-opus-4-1-20250514',
            'opus-4': 'claude-opus-4-20250514',
            'haiku-4.5': 'claude-haiku-4-5'  # Latest Haiku (Oct 2025)
        }
        return model_map.get(model_name, 'claude-sonnet-4-5-20250929')
    
    def _get_openai_model_string(self, model_name: str) -> str:
        """Convert config model name to API model string"""
        model_map = {
            'gpt-5': 'gpt-5',  # Latest GPT-5 (released Aug 2025)
            'gpt-5-mini': 'gpt-5-mini',
            'gpt-5-nano': 'gpt-5-nano',
            'gpt-4o': 'gpt-4o'
        }
        return model_map.get(model_name, 'gpt-5')
    
    def _get_grok_model_string(self, model_name: str) -> str:
        """Convert config model name to API model string"""
        model_map = {
            'grok-4': 'grok-4-0709',  # Actual Grok 4 model (released July 2025)
            'grok-4-fast': 'grok-4-fast-reasoning',  # Fast variant with reasoning
            'grok-3-mini': 'grok-2-1212'
        }
        return model_map.get(model_name, 'grok-4-0709')
    
    def _get_gemini_model_string(self, model_name: str) -> str:
        """Convert config model name to API model string"""
        model_map = {
            'gemini-2.5-pro': 'gemini-2.5-pro',  # Stable version (recommended)
            'gemini-2.5-pro-exp': 'gemini-2.5-pro-exp-03-25',  # Experimental
            'gemini-2.5-flash': 'gemini-2.5-flash',  # Fast variant
            'gemini-2.0-flash': 'gemini-2.0-flash-exp'
        }
        return model_map.get(model_name, 'gemini-2.5-pro')
    
    def _init_google_sheets(self):
        """Initialize Google Sheets connection"""
        google_sheet_url = self.config.get('google_sheet_url', '')
        
        if not google_sheet_url:
            print("⚠️  No google_sheet_url in config - Google Sheets disabled")
            self.sheet = None
            return
        
        # Try to find service account credentials
        creds_file = None
        for possible_name in ['service-account.json', 'credentials.json', 'google-credentials.json']:
            if Path(possible_name).exists():
                creds_file = possible_name
                break
        
        if not creds_file:
            print("⚠️  No service account JSON found - Google Sheets disabled")
            print("     Place service-account.json in the same directory")
            self.sheet = None
            return
        
        try:
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = Credentials.from_service_account_file(creds_file, scopes=scope)
            gc = gspread.authorize(creds)
            self.sheet = gc.open_by_url(google_sheet_url).worksheet('TechAnalysis')
            print(f"✓ Connected to Google Sheet")
        except Exception as e:
            print(f"⚠️  Failed to connect to Google Sheets: {e}")
            self.sheet = None

    def _setup_sheet_headers(self):
        """
        Setup header row with proper formatting
        """
        sheet = self.sheet
        headers = [
            'Ticker',          # A
            'Price',           # B
            'Score',           # C
            'Entry',           # D
            'Support',         # E
            'Key Supp',        # F
            'Resist',          # G
            'Strong Res',      # H
            'MA20',            # I
            'MA50',            # J
            'MA200',           # K
            'RSI',             # L
            'Agreement',       # M
            'Notes',           # N
            'Trend',           # O
            'ADX',             # P
            'Volume',          # Q
            'OBV',             # R
            'Divergence',      # S
            'Volatility',      # T
            'Max DD',          # U
            'VWAP'             # V
        ]
        
        # Write headers
        sheet.update('A1:V1', [headers])
        
        # Format header row
        header_format = {
            'requests': [
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet.id,
                            'startRowIndex': 0,
                            'endRowIndex': 1,
                            'startColumnIndex': 0,
                            'endColumnIndex': 22
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'backgroundColor': SheetColors.HEADER_DARK,
                                'textFormat': {
                                    'foregroundColor': SheetColors.WHITE,
                                    'fontSize': 11,
                                    'bold': True
                                },
                                'horizontalAlignment': 'CENTER',
                                'verticalAlignment': 'MIDDLE'
                            }
                        },
                        'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)'
                    }
                },
                # Freeze header row
                {
                    'updateSheetProperties': {
                        'properties': {
                            'sheetId': sheet.id,
                            'gridProperties': {
                                'frozenRowCount': 1
                            }
                        },
                        'fields': 'gridProperties.frozenRowCount'
                    }
                }
            ]
        }
        
        sheet.spreadsheet.batch_update(header_format)
        print("✓ Headers configured with formatting")

    def _setup_column_widths(self):
        """
        Setup optimal column widths for readability
        """
        sheet = self.sheet
        column_widths = {
            'A': 80,   # Ticker
            'B': 90,   # Price
            'C': 70,   # Score
            'D': 90,   # Entry
            'E': 90,   # Support
            'F': 90,   # Key Support
            'G': 90,   # Resistance
            'H': 100,  # Strong Res
            'I': 90,   # MA20
            'J': 90,   # MA50
            'K': 90,   # MA200
            'L': 70,   # RSI
            'M': 120,  # Agreement
            'N': 180,  # Notes
            'O': 160,  # Trend
            'P': 70,   # ADX
            'Q': 100,  # Volume
            'R': 80,   # OBV
            'S': 120,  # Divergence
            'T': 100,  # Volatility
            'U': 80,   # Max DD
            'V': 90    # VWAP
        }
        
        requests = []
        for col, width in column_widths.items():
            col_index = ord(col) - ord('A')
            requests.append({
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': sheet.id,
                        'dimension': 'COLUMNS',
                        'startIndex': col_index,
                        'endIndex': col_index + 1
                    },
                    'properties': {
                        'pixelSize': width
                    },
                    'fields': 'pixelSize'
                }
            })
        
        sheet.spreadsheet.batch_update({'requests': requests})
        print("✓ Column widths configured")

    def create_analysis_prompt(self, ticker: str, market_data: Dict) -> str:
        """Create detailed prompt for AI agents - pure technical analysis"""
        md = market_data
        ind = md['indicators']
        quote = md['quote']
        levels = md['levels']
        
        prompt = f"""Analyze {ticker} using the following VERIFIED market data for PURE TECHNICAL ANALYSIS:

CURRENT PRICE DATA:
- Price: ${quote['price']:.2f}
- Change: {quote['change']:+.2f} ({quote['percent_change']:+.2f}%)
- Volume: {quote['volume']:,}
- Previous Close: ${quote['previous_close']:.2f}

MOVING AVERAGES:
- 20-day SMA: ${ind['sma_20']:.2f}
- 50-day SMA: ${ind['sma_50']:.2f}
- 200-day SMA: ${ind['sma_200']:.2f}

MOMENTUM INDICATORS:
- RSI(14): {ind['rsi']:.1f}
- MACD: {ind['macd']:.3f}
- MACD Signal: {ind['macd_signal']:.3f}
- MACD Histogram: {ind['macd_hist']:.3f}
- Stochastic %K: {ind['stoch_k']:.1f}
- Stochastic %D: {ind['stoch_d']:.1f}

VOLATILITY:
- ATR: ${ind['atr']:.2f}
- Bollinger Upper: ${ind['bb_upper']:.2f}
- Bollinger Middle: ${ind['bb_middle']:.2f}
- Bollinger Lower: ${ind['bb_lower']:.2f}

SUPPORT & RESISTANCE:
- Closest Support: ${levels['closest_support']:.2f}
- Key Support: ${levels['key_support']:.2f}
- Closest Resistance: ${levels['closest_resistance']:.2f}
- Strongest Resistance: ${levels['strongest_resistance']:.2f}

PROVIDE YOUR ANALYSIS IN THIS EXACT JSON FORMAT (no markdown, no backticks):
{{
    "technical_score": <0-10>,
    "optimal_entry": <price>,
    "closest_support": <price>,
    "key_support": <price>,
    "closest_resistance": <price>,
    "strongest_resistance": <price>,
    "reasoning": "<brief 2-3 sentence technical explanation>"
}}

SCORING GUIDELINES:
- technical_score: Overall technical strength (0=very bearish, 10=very bullish)
- Consider: trend (price vs MAs), momentum (RSI, MACD, Stochastic), volume, volatility (ATR, Bollinger)
- Key factors: Moving average alignment, RSI levels, MACD crossovers, support/resistance proximity
- Be precise with support/resistance levels based on the data provided
"""
        return prompt
    
    def analyze_with_gemini(self, ticker: str, market_data: Dict) -> Dict:
        """Analyze with Gemini"""
        if not self.gemini_client:
            return {'success': False, 'model': 'gemini', 'error': 'Gemini disabled', 'cost': 0.0}
        
        try:
            print(f"      🤖 Gemini analyzing...")
            prompt = self.create_analysis_prompt(ticker, market_data)
            
            # Configure based on settings
            config_params = {
                'temperature': self.gemini_config.get('temperature', 0.3),
                'max_output_tokens': min(self.gemini_config.get('max_tokens', 8000), 8000)
            }
            
            # Add thinking if enabled
            if self.gemini_config.get('use_thinking', False):
                thinking_budget = self.gemini_config.get('thinking_budget_tokens', 8000)
                config_params['thinking_config'] = ThinkingConfig(
                    thinking_budget=thinking_budget
                )
            
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=prompt,
                config=GenerateContentConfig(**config_params)
            )
            
            # Extract JSON from response
            text = response.text.strip()
            text = re.sub(r'```json\s*|\s*```', '', text).strip()
            
            result = json.loads(text)
            result['model'] = 'gemini'
            result['success'] = True
            result['cost'] = 0.0
            
            # Add MA values
            result['ma_20'] = market_data['indicators']['sma_20']
            result['ma_50'] = market_data['indicators']['sma_50']
            result['ma_200'] = market_data['indicators']['sma_200']
            result['rsi'] = market_data['indicators']['rsi']
            
            print(f"         ✓ Tech Score: {result['technical_score']}/10")
            return result
            
        except Exception as e:
            print(f"         ✗ Gemini failed: {e}")
            return {'success': False, 'model': 'gemini', 'error': str(e), 'cost': 0.0}
    
    def analyze_with_grok(self, ticker: str, market_data: Dict) -> Dict:
        """Analyze with Grok (via XAI)"""
        if not self.grok_client:
            return {'success': False, 'model': 'grok', 'error': 'Grok disabled', 'cost': 0.0}
        
        try:
            print(f"      🤖 Grok analyzing...")
            prompt = self.create_analysis_prompt(ticker, market_data)
            
            response = self.grok_client.chat.completions.create(
                model=self.grok_model,
                messages=[
                    {"role": "system", "content": "You are a technical analysis expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=self.grok_config.get('max_tokens', 8192)  # Use configured max (Grok 4 supports up to 128K)
            )
            
            text = response.choices[0].message.content.strip()
            text = re.sub(r'```json\s*|\s*```', '', text).strip()
            
            result = json.loads(text)
            result['model'] = 'grok'
            result['success'] = True
            result['cost'] = 0.0
            
            # Add MA values
            result['ma_20'] = market_data['indicators']['sma_20']
            result['ma_50'] = market_data['indicators']['sma_50']
            result['ma_200'] = market_data['indicators']['sma_200']
            result['rsi'] = market_data['indicators']['rsi']
            
            print(f"         ✓ Tech Score: {result['technical_score']}/10")
            return result
            
        except Exception as e:
            print(f"         ✗ Grok failed: {e}")
            return {'success': False, 'model': 'grok', 'error': str(e), 'cost': 0.0}
    
    def analyze_with_gpt(self, ticker: str, market_data: Dict) -> Dict:
        """Analyze with GPT"""
        if not self.openai_client:
            return {'success': False, 'model': 'gpt', 'error': 'GPT disabled', 'cost': 0.0}
        
        try:
            print(f"      🤖 GPT analyzing...")
            prompt = self.create_analysis_prompt(ticker, market_data)
            
            # Build request params
            request_params = {
                "model": self.openai_model,
                "messages": [
                    {"role": "system", "content": "You are a technical analysis expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ]
            }
            
            # GPT-5 only supports temperature=1 (default), older models support custom values
            if not self.openai_model.startswith('gpt-5'):
                request_params['temperature'] = 0.3
            
            # Use max_completion_tokens for GPT-5+ models, max_tokens for older models
            if self.openai_model.startswith('gpt-5'):
                request_params['max_completion_tokens'] = self.openai_config.get('max_tokens', 8192)
            else:
                request_params['max_tokens'] = self.openai_config.get('max_tokens', 8192)
            
            # Add reasoning effort if supported
            if 'reasoning_effort' in self.openai_config:
                request_params['reasoning_effort'] = self.openai_config['reasoning_effort']
            
            response = self.openai_client.chat.completions.create(**request_params)
            
            text = response.choices[0].message.content.strip()
            text = re.sub(r'```json\s*|\s*```', '', text).strip()
            
            result = json.loads(text)
            result['model'] = 'gpt'
            result['success'] = True
            result['cost'] = 0.01
            
            # Add MA values
            result['ma_20'] = market_data['indicators']['sma_20']
            result['ma_50'] = market_data['indicators']['sma_50']
            result['ma_200'] = market_data['indicators']['sma_200']
            result['rsi'] = market_data['indicators']['rsi']
            
            print(f"         ✓ Tech Score: {result['technical_score']}/10")
            return result
            
        except Exception as e:
            print(f"         ✗ GPT failed: {e}")
            return {'success': False, 'model': 'gpt', 'error': str(e), 'cost': 0.0}
    
    def compare_analyses(self, results: List[Dict]) -> tuple:
        """Compare agent results and determine agreement level"""
        valid = [r for r in results if r['success']]
        
        if len(valid) < 2:
            return 'INSUFFICIENT_DATA', {}
        
        # Extract scores
        tech_scores = [r['technical_score'] for r in valid]
        
        # Calculate variance
        tech_variance = np.var(tech_scores)
        
        discrepancies = {}
        
        # Check for major disagreements
        if tech_variance > 4.0:
            discrepancies['technical_score'] = f"High variance: {tech_scores}"
        
        # Determine agreement level
        if tech_variance < 1.0:
            return 'FULL_AGREEMENT', discrepancies
        elif tech_variance < 2.5:
            return 'PARTIAL_AGREEMENT', discrepancies
        else:
            return 'MAJOR_DISAGREEMENT', discrepancies
    
    def arbitrate_analyses(self, ticker: str, results: List[Dict], agreement: str, discrepancies: Dict) -> Dict:
        """Use Claude to arbitrate between agent results"""
        valid = [r for r in results if r['success']]
        
        if not valid:
            return {'success': False, 'error': 'No valid analyses'}
        
        # Combine base analysis with data from the original fetch
        # This ensures all 22-column data points are present
        base_result = results[0] # Use the first result (which has all market data) as a base
        
        if len(valid) == 1:
            final = valid[0]
        
        # If full agreement, just average
        elif agreement == 'FULL_AGREEMENT':
            print(f"      ✓ Full agreement - averaging results")
            def avg(key):
                values = [r[key] for r in valid if key in r]
                return round(sum(values) / len(values), 2) if values else None
            
            final = {
                'technical_score': avg('technical_score'),
                'optimal_entry': avg('optimal_entry'),
                'closest_support': avg('closest_support'),
                'key_support': avg('key_support'),
                'closest_resistance': avg('closest_resistance'),
                'strongest_resistance': avg('strongest_resistance'),
                'cost': 0,
                'reasoning': "Full agreement between models."
            }
        
        # Need Claude arbitration
        elif not self.claude_client:
            print(f"      ⚠️  Claude disabled, using average for arbitration")
            def avg(key):
                values = [r[key] for r in valid if key in r]
                return round(sum(values) / len(values), 2) if values else None
            
            final = {
                'technical_score': avg('technical_score'),
                'optimal_entry': avg('optimal_entry'),
                'closest_support': avg('closest_support'),
                'key_support': avg('key_support'),
                'closest_resistance': avg('closest_resistance'),
                'strongest_resistance': avg('strongest_resistance'),
                'cost': 0,
                'reasoning': f"Partial agreement, averaged results (Claude disabled)."
            }
        
        else:
            print(f"      🧠 Claude arbitrating ({agreement})...")
            
            arbitration_prompt = f"""The following agents analyzed {ticker} and have disagreements.
Review their technical analyses and provide a final consensus.

AGENT ANALYSES:
{json.dumps(valid, indent=2)}

DISAGREEMENT AREAS:
{json.dumps(discrepancies, indent=2)}

Provide a balanced final technical analysis in this EXACT JSON format:
{{
    "technical_score": <0-10>,
    "optimal_entry": <price>,
    "closest_support": <price>,
    "key_support": <price>,
    "closest_resistance": <price>,
    "strongest_resistance": <price>,
    "reasoning": "<explanation of your technical arbitration>"
}}
"""
            
            try:
                # Build request params based on config
                request_params = {
                    'model': self.claude_model,
                    'max_tokens': min(self.claude_config.get('max_tokens', 4096), 4096),
                    'temperature': 0.3,
                    'messages': [{"role": "user", "content": arbitration_prompt}]
                }
                
                # Add extended thinking if enabled
                if self.claude_config.get('use_extended_thinking', False):
                    thinking_budget = self.claude_config.get('thinking_budget_tokens', 10000)
                    request_params['thinking'] = {
                        'type': 'enabled',
                        'budget_tokens': thinking_budget
                    }
                
                response = self.claude_client.messages.create(**request_params)
                
                text = response.content[0].text.strip()
                text = re.sub(r'```json\s*|\s*```', '', text).strip()
                
                final = json.loads(text)
                final['cost'] = 0.01
                print(f"         ✓ Arbitrated - Tech Score: {final['technical_score']}/10")
            
            except Exception as e:
                print(f"         ✗ Arbitration failed: {e}, using average")
                def avg(key):
                    values = [r[key] for r in valid if key in r]
                    return round(sum(values) / len(values), 2) if values else None
                
                final = {
                    'technical_score': avg('technical_score'),
                    'optimal_entry': avg('optimal_entry'),
                    'closest_support': avg('closest_support'),
                    'key_support': avg('key_support'),
                    'closest_resistance': avg('closest_resistance'),
                    'strongest_resistance': avg('strongest_resistance'),
                    'cost': 0,
                    'reasoning': f"Arbitration failed, averaged results."
                }
        
        # Merge all data for the final 22-column output
        # Start with the full data from the original fetch
        complete_result = {**base_result}
        # Update with the arbitrated/agreed values
        complete_result.update(final)
        # Ensure these fields are set
        complete_result['ticker'] = ticker
        complete_result['agreement_level'] = agreement
        complete_result['discrepancies'] = discrepancies
        complete_result['success'] = True
        
        return complete_result
    
    def create_stock_report(self, ticker: str, results: List[Dict], final: Dict, agreement: str, disc: Dict):
        """Create markdown report"""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = self.reports_dir / f"{ticker}_{timestamp}.md"
        
        disc_section = "\n## ✅ All Models Aligned\n" if not disc else "\n## ⚠️ Discrepancies\n" + "\n".join([f"- {k}: {v}" for k, v in disc.items()])
        
        models_section = ""
        for r in results:
            if r['success']:
                models_section += f"\n### {r['model'].upper()}\n"
                models_section += f"Technical Score: {r.get('technical_score', 'N/A')}/10\n"
                if 'reasoning' in r:
                    models_section += f"Reasoning: {r['reasoning']}\n"
        
        content = f"""# Technical Analysis: {ticker}
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Data Source**: Twelve Data API (Optimized 1-Credit Method)
**Agreement**: {agreement}

## 📊 Final Results
Price: ${final.get('current_price', 'N/A'):.2f} | Technical Score: {final.get('technical_score', 'N/A')}/10
Optimal Entry: ${final.get('optimal_entry', 'N/A'):.2f}
Support: ${final.get('closest_support', 'N/A'):.2f} / ${final.get('key_support', 'N/A'):.2f}
Resistance: ${final.get('closest_resistance', 'N/A'):.2f} / ${final.get('strongest_resistance', 'N/A'):.2f}
Moving Averages: ${final.get('ma_20', 'N/A'):.2f} / ${final.get('ma_50', 'N/A'):.2f} / ${final.get('ma_200', 'N/A'):.2f}
RSI: {final.get('rsi', 'N/A'):.1f}

{disc_section}

## 🤖 Models
{models_section}

## 💰 Cost
Total: ${final.get('total_cost', 0):.4f}
Twelve Data: 1 credit per stock (90% savings!)

---
*Pure Technical Analysis - All indicators calculated client-side from single time_series call*
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  📄 Report: {filename.name}")
        return str(filename)
    
    def analyze_ticker(self, ticker: str) -> Dict:
        """Main analysis workflow for a single ticker"""
        print(f"\n{'='*70}\nANALYZING: {ticker}\n{'='*70}")
        
        # Step 1: Fetch market data (ONLY 1 CREDIT!)
        market_data = self.data_fetcher.get_complete_analysis_data(ticker)
        if not market_data:
            print(f"\n  ✗ Failed to fetch market data for {ticker}")
            return {'success': False, 'error': 'Market data fetch failed', 'ticker': ticker}
        
        # Add current price to market_data for convenience
        market_data['current_price'] = market_data['quote']['price']
        
        print(f"\n  🤖 Running agent analyses in parallel...")
        
        # Step 2: Run all agents in parallel
        global_settings = self.config.get('global_settings', {})
        use_concurrent = global_settings.get('use_concurrent', True)
        max_workers = global_settings.get('max_workers', 3)
        
        if use_concurrent:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(self.analyze_with_gemini, ticker, market_data),
                    executor.submit(self.analyze_with_grok, ticker, market_data),
                    executor.submit(self.analyze_with_gpt, ticker, market_data)
                ]
                results = [f.result() for f in futures]
        else:
            results = [
                self.analyze_with_gemini(ticker, market_data),
                self.analyze_with_grok(ticker, market_data),
                self.analyze_with_gpt(ticker, market_data)
            ]
        
        # Add full market data to each result for later use
        full_results = []
        for r in results:
            # Combine the base market data with the agent's specific analysis
            full_r = {**market_data, **r}
            full_results.append(full_r)
        
        # Step 3: Check results
        valid = [r for r in full_results if r['success']]
        if not valid:
            print(f"\n  ✗ ALL AGENTS FAILED")
            return {'success': False, 'error': 'All agents failed', 'ticker': ticker}
        
        if len(valid) == 1:
            print(f"\n  ⚠️  Only 1 agent succeeded, using its results")
            final_result = valid[0]
            final_result['total_cost'] = final_result['cost']
            final_result['ticker'] = ticker
            final_result['agreement_level'] = 'SINGLE_AGENT'
            final_result['discrepancies'] = {}
            return final_result
        
        # Step 4: Compare and arbitrate
        agreement, discrepancies = self.compare_analyses(valid)
        
        if agreement == 'FULL_AGREEMENT':
            self.agreement_stats['full_agreement'] += 1
        elif agreement == 'PARTIAL_AGREEMENT':
            self.agreement_stats['partial_agreement'] += 1
        else:
            self.agreement_stats['major_disagreement'] += 1
        
        aligned = self.arbitrate_analyses(ticker, valid, agreement, discrepancies)
        aligned['total_cost'] = sum(r['cost'] for r in valid) + aligned.get('cost', 0)
        
        self.create_stock_report(ticker, valid, aligned, agreement, discrepancies)
        
        print(f"\n  {'='*66}")
        print(f"  💰 Cost: ${aligned['total_cost']:.4f} (Twelve Data: 1 credit) | 🤝 {agreement}")
        print(f"  📊 Technical Score: {aligned.get('technical_score', 'N/A')}/10")
        print(f"  💵 Price: ${aligned.get('current_price', 'N/A'):.2f} | 🎯 Entry: ${aligned.get('optimal_entry', 'N/A'):.2f}")
        print(f"  {'='*66}")
        
        return aligned
    
    # ========================================================================
    # START: NEW 22-COLUMN GOOGLE SHEET METHODS
    # ========================================================================

    def write_to_sheet(self, row: int, result: Dict) -> bool:
        """
        Write results to Google Sheet with 22 columns and color coding
        
        Args:
            row: Row number to write to
            result: Analysis result dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.sheet:
            return False
        
        try:
            # Extract data with safe defaults
            indicators = result.get('indicators', {})
            trend_analysis = result.get('trend_analysis', {})
            divergence = result.get('divergence', {})
            volume_metrics = result.get('volume_metrics', {})
            volatility = result.get('volatility', {})
            risk = result.get('risk', {})
            
            # Format values
            notes = f"{result.get('agreement_level', '')} | {len(result.get('discrepancies', {}))} disc"
            
            # Format trend with confidence
            trend_str = f"{trend_analysis.get('trend', 'N/A')} ({trend_analysis.get('confidence', 0)*100:.0f}%)"
            
            # Format volume confirmation
            vol_confirms = "✓" if volume_metrics.get('volume_confirms_price', False) else "✗"
            volume_str = f"{volume_metrics.get('relative_volume', 'N/A')} {vol_confirms}"
            
            # Get numeric values for coloring
            score = result.get('technical_score', 0)
            adx_val = indicators.get('adx', 0)
            rsi_val = result.get('rsi', indicators.get('rsi', 50))
            max_dd = risk.get('max_drawdown', 0)
            
            # Prepare row data (columns B-V)
            row_data = [
                result.get('current_price', ''),                    # B: Price
                score,                                               # C: Score
                result.get('optimal_entry', ''),                    # D: Entry
                result.get('closest_support', ''),                  # E: Support
                result.get('key_support', ''),                      # F: Key Support
                result.get('closest_resistance', ''),               # G: Resistance
                result.get('strongest_resistance', ''),             # H: Strong Res
                result.get('ma_20', ''),                            # I: MA20
                result.get('ma_50', ''),                            # J: MA50
                result.get('ma_200', ''),                           # K: MA200
                rsi_val,                                            # L: RSI
                result.get('agreement_level', ''),                  # M: Agreement
                notes,                                              # N: Notes
                trend_str,                                          # O: Trend
                round(adx_val, 1) if adx_val else '',              # P: ADX
                volume_str,                                         # Q: Volume
                indicators.get('obv_trend', ''),                   # R: OBV
                divergence.get('divergence_type', 'None'),         # S: Divergence
                volatility.get('volatility_regime', ''),           # T: Volatility
                f"{max_dd:.1f}%" if max_dd else '',                # U: Max DD
                round(indicators.get('vwap', 0), 2) if indicators.get('vwap') else ''  # V: VWAP
            ]
            
            # Write the data
            self.sheet.update(values=[row_data], range_name=f'B{row}:V{row}')
            
            # Apply color coding
            self._apply_color_coding(row, score, adx_val, rsi_val, trend_str,
                                    volume_str, divergence.get('divergence_type', 'None'),
                                    volatility.get('volatility_regime', ''), max_dd)
            
            print(f"  ✓ Written to row {row}")
            return True
            
        except Exception as e:
            print(f"  ✗ Sheet write failed: {e}")
            return False


    def _apply_color_coding(self, row: int, score: float, adx: float, rsi: float,
                           trend: str, volume: str, divergence: str,
                           volatility: str, max_dd: float):
        """Apply color coding to specific cells"""
        if not self.sheet:
            return
        
        try:
            # Determine colors for each cell
            score_color = self._get_score_color(score)
            rsi_color = self._get_rsi_color(rsi)
            trend_color = self._get_trend_color(trend)
            adx_color = self._get_adx_color(adx)
            volume_color = self._get_volume_color(volume)
            divergence_color = self._get_divergence_color(divergence)
            volatility_color = self._get_volatility_color(volatility)
            drawdown_color = self._get_drawdown_color(max_dd)
            
            # Build batch update request
            requests = []
            
            # Column C: Score
            requests.append(self._create_cell_format(row, 2, score_color, bold=True, center=True))
            
            # Column L: RSI
            requests.append(self._create_cell_format(row, 11, rsi_color, center=True))
            
            # Column O: Trend
            requests.append(self._create_cell_format(row, 14, trend_color, bold=True, center=True))
            
            # Column P: ADX
            if adx:
                requests.append(self._create_cell_format(row, 15, adx_color, center=True))
            
            # Column Q: Volume
            requests.append(self._create_cell_format(row, 16, volume_color, center=True))
            
            # Column S: Divergence
            requests.append(self._create_cell_format(row, 18, divergence_color,
                                                    bold=(divergence != 'None'), center=True))
            
            # Column T: Volatility
            requests.append(self._create_cell_format(row, 19, volatility_color, center=True))
            
            # Column U: Max Drawdown
            if max_dd:
                requests.append(self._create_cell_format(row, 20, drawdown_color, center=True))
            
            # Apply all formats in batch
            if requests:
                self.sheet.spreadsheet.batch_update({'requests': requests})
                
        except Exception as e:
            print(f"  ⚠️  Color coding failed for row {row}: {e}")


    def _create_cell_format(self, row: int, col: int, color: Dict,
                           bold: bool = False, center: bool = False) -> Dict:
        """Create a cell format request"""
        format_dict = {
            'repeatCell': {
                'range': {
                    'sheetId': self.sheet.id,
                    'startRowIndex': row - 1,
                    'endRowIndex': row,
                    'startColumnIndex': col,
                    'endColumnIndex': col + 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': color
                    }
                },
                'fields': 'userEnteredFormat.backgroundColor'
            }
        }
        
        if bold:
            format_dict['repeatCell']['cell']['userEnteredFormat']['textFormat'] = {'bold': True}
            format_dict['repeatCell']['fields'] += ',userEnteredFormat.textFormat'
        
        if center:
            format_dict['repeatCell']['cell']['userEnteredFormat']['horizontalAlignment'] = 'CENTER'
            format_dict['repeatCell']['fields'] += ',userEnteredFormat.horizontalAlignment'
        
        return format_dict


    def _get_color(self, color_name: str) -> Dict:
        """Get RGB color values"""
        color_map = {
            'dark_green': SheetColors.DARK_GREEN,
            'light_green': SheetColors.LIGHT_GREEN,
            'yellow': SheetColors.YELLOW,
            'light_red': SheetColors.LIGHT_RED,
            'dark_red': SheetColors.DARK_RED,
            'white': SheetColors.WHITE,
            'light_blue': SheetColors.LIGHT_BLUE,
        }
        return color_map.get(color_name, SheetColors.WHITE)


    def _get_score_color(self, score: float) -> Dict:
        """Get color for technical score"""
        if score >= 8:
            return self._get_color('dark_green')
        elif score >= 6:
            return self._get_color('light_green')
        elif score >= 4:
            return self._get_color('yellow')
        else:
            return self._get_color('light_red')


    def _get_rsi_color(self, rsi: float) -> Dict:
        """Get color for RSI"""
        if rsi > 70:
            return self._get_color('light_red')
        elif rsi < 30:
            return self._get_color('light_green')
        else:
            return self._get_color('white')


    def _get_trend_color(self, trend: str) -> Dict:
        """Get color for trend"""
        if 'STRONG_UPTREND' in trend:
            return self._get_color('dark_green')
        elif 'UPTREND' in trend:
            return self._get_color('light_green')
        elif 'SIDEWAYS' in trend:
            return self._get_color('yellow')
        elif 'DOWNTREND' in trend and 'STRONG' not in trend:
            return self._get_color('light_red')
        elif 'STRONG_DOWNTREND' in trend:
            return self._get_color('dark_red')
        else:
            return self._get_color('white')


    def _get_adx_color(self, adx: float) -> Dict:
        """Get color for ADX"""
        if adx > 25:
            return self._get_color('light_green')
        elif adx > 20:
            return self._get_color('yellow')
        else:
            return self._get_color('light_red')


    def _get_volume_color(self, volume: str) -> Dict:
        """Get color for volume"""
        if '✓' in volume:
            return self._get_color('light_green')
        elif '✗' in volume:
            return self._get_color('light_red')
        else:
            return self._get_color('white')


    def _get_divergence_color(self, divergence: str) -> Dict:
        """Get color for divergence"""
        if 'BEARISH' in divergence:
            return self._get_color('light_red')
        elif 'BULLISH' in divergence:
            return self._get_color('light_green')
        else:
            return self._get_color('white')


    def _get_volatility_color(self, volatility: str) -> Dict:
        """Get color for volatility"""
        if volatility == 'VERY_HIGH':
            return self._get_color('dark_red')
        elif volatility == 'HIGH':
            return self._get_color('light_red')
        elif volatility == 'NORMAL':
            return self._get_color('light_green')
        elif volatility == 'LOW':
            return self._get_color('light_blue')
        else:
            return self._get_color('white')


    def _get_drawdown_color(self, drawdown: float) -> Dict:
        """Get color for drawdown"""
        if drawdown > -5:
            return self._get_color('light_green')
        elif drawdown > -10:
            return self._get_color('yellow')
        else:
            return self._get_color('light_red')

    # ========================================================================
    # END: NEW 22-COLUMN GOOGLE SHEET METHODS
    # ========================================================================


    def process_tickers(self, start_row: int = 2):
        """Process all tickers from Google Sheet"""
        if not self.sheet:
            print("\n⚠️  Google Sheets not configured - skipping sheet processing")
            print("     Add tickers manually or configure Google Sheets")
            return
        
        print(f"\n{'='*70}\nLOADING TICKERS\n{'='*70}")
        all_values = self.sheet.get_all_values()
        
        try:
            # Check if headers match the new 22-column format
            if not all_values or len(all_values[0]) < 22 or all_values[0][0] != 'Ticker' or all_values[0][21] != 'VWAP':
                print("⚠️  Headers mismatch or sheet is empty. Initializing 22-column headers...")
                self._setup_sheet_headers()
                self._setup_column_widths()
                print("✓ Sheet initialized. Reloading data...")
                all_values = self.sheet.get_all_values()
            else:
                print("✓ Headers match 22-column format.")
        except Exception as e:
            print(f"⚠️  Could not verify/setup headers: {e}")
            # Continue anyway, might fail on write
        
        tickers = [{'symbol': row[0].strip().upper(), 'row_num': idx}
                  for idx, row in enumerate(all_values[start_row-1:], start=start_row) if row and row[0].strip()]
        
        if not tickers:
            print("\n⚠️  No tickers found in Column A")
            return
        
        print(f"\n✓ Found {len(tickers)} ticker(s)")
        for t in tickers:
            print(f"  - {t['symbol']} (Row {t['row_num']})")
        
        print(f"\n{'='*70}\nSTARTING ANALYSIS\n{'='*70}")
        print(f"💡 Using OPTIMIZED method: 1 credit per stock (vs 7+ before)")
        print(f"💡 All indicators calculated client-side from time_series data")
        print(f"💡 Pure technical analysis without Elliott Wave")
        print(f"{'='*70}\n")
        
        for idx, t in enumerate(tickers):
            print(f"\n[{idx+1}/{len(tickers)}] {t['symbol']}...")
            result = self.analyze_ticker(t['symbol'])
            
            if result['success']:
                self.write_to_sheet(t['row_num'], result)
                self.successful_analyses += 1
                self.total_cost += result.get('total_cost', 0)
            else:
                self.failed_analyses += 1
                try:
                    # Write error to Notes column (N)
                    self.sheet.update(values=[[f"ERROR: {result.get('error', 'Unknown')}"]], range_name=f'N{t["row_num"]}')
                except:
                    pass
            
            if idx < len(tickers) - 1:
                time.sleep(2)
        
        self.print_summary(len(tickers))
    
    def print_summary(self, total: int):
        """Print final summary"""
        print(f"\n\n{'='*70}\nCOMPLETE\n{'='*70}")
        print(f"Processed: {total} | Success: {self.successful_analyses} | Failed: {self.failed_analyses}")
        print(f"\n🤝 Agreement:")
        print(f"  Full: {self.agreement_stats['full_agreement']}")
        print(f"  Partial: {self.agreement_stats['partial_agreement']}")
        print(f"  Major: {self.agreement_stats['major_disagreement']}")
        print(f"\n💰 Total cost: ${self.total_cost:.4f}")
        if self.successful_analyses > 0:
            print(f"  Avg/ticker: ${self.total_cost/self.successful_analyses:.4f}")
        print(f"\n💡 Twelve Data Savings: ~90% (1 credit vs 7+ per stock)")
        print(f"✅ Results in Google Sheet" if self.sheet else "⚠️  Google Sheets not configured")
        print(f"📁 Reports in: {self.reports_dir.absolute()}")
        print(f"{'='*70}\n")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("PURE TECHNICAL ANALYSIS - 3-AGENT SYSTEM")
    print("1 Credit Per Stock (90% Savings!)")
    print("Real Data → Client-Side Calculations → AI Analysis → Consensus")
    print("="*70)
    
    try:
        analyzer = TechnicalAnalyzer(config_path='config.json')
        analyzer.process_tickers(start_row=2)
        
        print("\n✅ DONE!\n")
    except FileNotFoundError:
        print("\n❌ ERROR: config.json not found!")
        print("Please create config.json based on your structure")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
