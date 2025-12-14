"""
Twelve Data API fetcher with client-side indicator calculation.

Fetches market data with a single API call per stock (1 credit),
then calculates all technical indicators locally.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import requests

from src.analysis.calculator import TechnicalCalculator

logger = logging.getLogger(__name__)


class TwelveDataFetcher:
    """
    Optimized data fetcher using Twelve Data API.
    
    Pulls only time_series data and calculates all indicators
    client-side, reducing API costs to 1 credit per stock.
    
    Attributes:
        api_key: Twelve Data API key
        base_url: API base URL
        calc: TechnicalCalculator instance
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the fetcher.
        
        Args:
            api_key: Twelve Data API key
        """
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com"
        self.calc = TechnicalCalculator()
    
    def get_complete_analysis_data(
        self,
        ticker: str,
        outputsize: int = 200
    ) -> Optional[Dict]:
        """
        Fetch all data needed for analysis with only 1 API credit.
        
        Args:
            ticker: Stock symbol (e.g., 'AAPL')
            outputsize: Number of days to retrieve (max 5000)
        
        Returns:
            Complete analysis data with all indicators, or None on failure
        """
        logger.info(f"Fetching market data for {ticker} (1 credit only)")
        
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
                logger.warning(f"API error for {ticker}: {data.get('message', 'Unknown error')}")
                return None
            
            if 'values' not in data or not data['values']:
                logger.warning(f"No data returned for {ticker}")
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
                logger.warning(f"Insufficient data for {ticker}: only {len(df)} bars")
                return None
            
            # Current price info
            current_price = float(df['close'].iloc[-1])
            previous_close = float(df['close'].iloc[-2]) if len(df) > 1 else current_price
            
            # Calculate ALL indicators from raw OHLCV data
            logger.debug(f"Calculating indicators for {ticker}")
            
            indicators = self._calculate_indicators(df, current_price)
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
            history = self._build_history(df)
            
            # TODO: Implement real calculations for these indicators
            # Currently using placeholder values for demonstration
            mock_data = self._get_mock_extended_indicators(current_price)
            
            result = {
                'ticker': ticker,
                'current_price': current_price,
                'quote': quote,
                'indicators': indicators,
                'history': history,
                'levels': levels,
                'timestamp': datetime.now().isoformat(),
                'data_points': len(df),
                **mock_data  # Add mock data (to be replaced with real calculations)
            }
            
            logger.info(
                f"Fetched {ticker}: ${current_price:.2f} ({quote['percent_change']:+.2f}%), "
                f"RSI: {indicators['rsi']:.1f}, Cost: 1 credit"
            )
            
            return result
            
        except requests.RequestException as e:
            logger.error(f"Network error fetching {ticker}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {ticker}: {e}", exc_info=True)
            return None
    
    def _calculate_indicators(self, df: pd.DataFrame, current_price: float) -> Dict:
        """Calculate all technical indicators from OHLCV data."""
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
        
        return indicators
    
    def _build_history(self, df: pd.DataFrame, days: int = 30) -> List[Dict]:
        """Build historical data list for agent analysis."""
        history = []
        for _, row in df.tail(days).iterrows():
            history.append({
                'date': row['datetime'].strftime('%Y-%m-%d'),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': int(row['volume'])
            })
        return history
    
    def _get_mock_extended_indicators(self, current_price: float) -> Dict:
        """
        Generate mock data for extended indicators.
        
        TODO: Replace with real calculations for:
        - ADX (Average Directional Index)
        - OBV (On-Balance Volume)
        - VWAP (Volume Weighted Average Price)
        - Trend analysis
        - Divergence detection
        """
        return {
            'indicators': {
                'adx': np.random.uniform(15, 40),
                'obv_trend': np.random.choice(['UP', 'DOWN', 'SIDEWAYS']),
                'vwap': current_price * np.random.uniform(0.99, 1.01),
            },
            'trend_analysis': {
                'trend': np.random.choice([
                    'STRONG_UPTREND', 'UPTREND', 'SIDEWAYS',
                    'DOWNTREND', 'STRONG_DOWNTREND'
                ]),
                'confidence': np.random.uniform(0.6, 1.0)
            },
            'volume_metrics': {
                'relative_volume': f"{np.random.uniform(0.8, 2.5):.2f}x",
                'volume_confirms_price': np.random.choice([True, False])
            },
            'divergence': {
                'divergence_type': np.random.choice(['None', 'BULLISH', 'BEARISH'])
            },
            'volatility': {
                'volatility_regime': np.random.choice(['LOW', 'NORMAL', 'HIGH', 'VERY_HIGH'])
            },
            'risk': {
                'max_drawdown': -np.random.uniform(2.0, 15.0)
            }
        }
