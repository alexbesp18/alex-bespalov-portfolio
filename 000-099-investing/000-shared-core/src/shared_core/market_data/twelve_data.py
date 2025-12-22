"""
Twelve Data API client with daily caching.
Fetches OHLCV time series and calculates all technical indicators.

Unified client for all investing projects in 000-099-investing.
"""

import datetime as dt
import requests
import pandas as pd
from typing import Dict, List, Optional, Any

from ..cache.data_cache import DataCache
from .technical import TechnicalCalculator


class TwelveDataClient:
    """
    Twelve Data API client with:
    - Daily caching: if data exists for today, use it; otherwise fetch fresh
    - Full technical indicator calculation
    """

    def __init__(self, api_key: str, cache: Optional[DataCache] = None, 
                 output_size: int = 365, rate_limit_sleep: float = 0.5, 
                 verbose: bool = False):
        """
        Initialize Twelve Data client.
        
        Args:
            api_key: Twelve Data API key
            cache: Optional DataCache instance for storing/retrieving data
            output_size: Number of daily bars to fetch (default 365)
            rate_limit_sleep: Seconds to wait between API calls
            verbose: Print detailed progress
        """
        self.api_key = api_key
        self.cache = cache
        self.base_url = "https://api.twelvedata.com"
        self.output_size = output_size
        self.rate_limit_sleep = rate_limit_sleep
        self.verbose = verbose
        self.calc = TechnicalCalculator()

    def get_tickers_needing_refresh(self, tickers: List[str]) -> List[str]:
        """
        Determine which tickers need fresh API data.
        
        Simple logic: if no cache exists for today, ticker needs refresh.
        
        Args:
            tickers: List of all tickers to evaluate
            
        Returns:
            List of ticker symbols needing API refresh
        """
        if self.cache is None:
            return tickers

        needs_refresh = []
        cached_count = 0

        for ticker in tickers:
            cached = self.cache.get_twelve_data(ticker)
            if cached is None:
                needs_refresh.append(ticker)
            else:
                cached_count += 1

        if self.verbose:
            if cached_count > 0:
                print(f"   ✅ {cached_count} tickers already cached today")
            if needs_refresh:
                print(f"   📝 {len(needs_refresh)} tickers need fresh data")

        return needs_refresh

    # =========================================================================
    # RAW DATA FETCH
    # =========================================================================

    def fetch_raw(self, ticker: str) -> Optional[pd.DataFrame]:
        """
        Fetch raw OHLCV data from Twelve Data API.
        
        Returns:
            DataFrame with datetime, open, high, low, close, volume columns
            or None on error
        """
        if self.verbose:
            print(f"    📊 Fetching {ticker} from Twelve Data API...")

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
                return None

            if 'values' not in data or not data['values']:
                if self.verbose:
                    print("    ❌ No data returned")
                return None

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
                return None

            return df

        except requests.exceptions.Timeout:
            if self.verbose:
                print(f"    ❌ Request timeout for {ticker}")
            return None
        except Exception as e:
            if self.verbose:
                print(f"    ❌ Error fetching {ticker}: {str(e)[:50]}")
            return None

    def _calculate_indicators(self, ticker: str, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate all technical indicators from OHLCV data.
        
        Returns:
            Dict with all indicator values ready for sheet output
        """
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

        # Current values from series
        rsi_current = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50.0
        macd_hist = float(histogram.iloc[-1])
        atr_current = float(atr_series.iloc[-1])

        # Moving averages
        sma_20 = float(self.calc.sma(df['close'], 20).iloc[-1])
        sma_50 = float(self.calc.sma(df['close'], 50).iloc[-1])
        sma_200 = float(self.calc.sma(df['close'], min(200, len(df))).iloc[-1])

        # Classifications
        trend = self.calc.classify_trend(current_price, sma_20, sma_50, sma_200, macd_hist)
        obv_trend = self.calc.classify_obv_trend(obv_series)
        divergence = self.calc.detect_divergence(df, rsi_series)
        volatility = self.calc.classify_volatility(atr_series)

        # Relative volume
        avg_volume = df['volume'].tail(20).mean()
        current_volume = df['volume'].iloc[-1]
        rel_volume = f"{current_volume / avg_volume:.1f}x" if avg_volume > 0 else "N/A"

        # 52-week range
        high_52w = float(df['high'].max())
        low_52w = float(df['low'].min())

        # VWAP and ADX
        vwap = self.calc.vwap(df, period=20)
        adx = self.calc.adx(df)

        return {
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

    def fetch_and_calculate(self, ticker: str, 
                            force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Fetch data and calculate all indicators for a ticker.
        Uses cache unless force_refresh is True.
        
        Args:
            ticker: Stock ticker symbol
            force_refresh: Bypass cache and fetch fresh data
            
        Returns:
            Dict with all indicator values, or error dict on failure
        """
        ticker = ticker.upper()

        # Check cache first (unless forcing refresh)
        if not force_refresh and self.cache is not None:
            cached_df = self.cache.get_twelve_data(ticker)
            if cached_df is not None:
                if self.verbose:
                    print(f"    ✅ Using cached data for {ticker}")
                return self._calculate_indicators(ticker, cached_df)

        # Fetch from API
        df = self.fetch_raw(ticker)

        if df is None:
            return {'Ticker': ticker, 'Status': 'ERROR: Failed to fetch data'}

        # Save to cache
        if self.cache is not None:
            self.cache.save_twelve_data(ticker, df)

        # Calculate and return indicators
        result = self._calculate_indicators(ticker, df)

        if self.verbose:
            print(f"    ✅ {ticker}: ${result['Price']}, RSI={result['RSI']}, Trend={result['Trend']}")

        return result

    def get_dataframe(self, ticker: str, force_refresh: bool = False) -> Optional[pd.DataFrame]:
        """
        Get OHLCV DataFrame for a ticker (with caching).
        
        Args:
            ticker: Stock ticker symbol
            force_refresh: Bypass cache and fetch fresh data
            
        Returns:
            DataFrame with OHLCV data, or None on failure
        """
        ticker = ticker.upper()

        # Check cache first
        if not force_refresh and self.cache is not None:
            cached_df = self.cache.get_twelve_data(ticker)
            if cached_df is not None:
                if self.verbose:
                    print(f"    ✅ Using cached data for {ticker}")
                return cached_df

        # Fetch from API
        df = self.fetch_raw(ticker)

        if df is not None and self.cache is not None:
            self.cache.save_twelve_data(ticker, df)

        return df

