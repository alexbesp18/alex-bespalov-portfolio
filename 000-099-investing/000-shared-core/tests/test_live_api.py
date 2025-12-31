"""
Live API tests - hits real Twelve Data API.

Run with: pytest tests/test_live_api.py -v -s
Limit to 1-2 tickers to stay within rate limits.
"""

import pytest
import requests
import json
import time
from pathlib import Path

from shared_core.data import add_standard_indicators, calculate_matrix, calculate_bullish_score
from shared_core.divergence import detect_combined_divergence
from shared_core.triggers import evaluate_ticker
from shared_core.scoring import DivergenceType

# Load API key from config
CONFIG_PATH = Path(__file__).parent.parent.parent / "007-ticker-analysis" / "config.json"


def get_api_key():
    """Load Twelve Data API key from config."""
    if not CONFIG_PATH.exists():
        return None
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    return config.get("twelve_data", {}).get("api_key")


def fetch_from_api(ticker: str, api_key: str, outputsize: int = 250):
    """Fetch real data from Twelve Data API."""
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": ticker,
        "interval": "1day",
        "outputsize": outputsize,
        "apikey": api_key,
    }
    
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    if "values" not in data:
        raise ValueError(f"API error: {data.get('message', 'No data')}")
    
    return data


def api_response_to_dataframe(data: dict):
    """Convert Twelve Data API response to DataFrame."""
    import pandas as pd
    
    df = pd.DataFrame(data["values"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.set_index("datetime").sort_index()
    
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    return df


API_KEY = get_api_key()
SKIP_NO_API = pytest.mark.skipif(
    API_KEY is None,
    reason="No API key found in config.json"
)

# Test tickers - limit to 2 for rate limits
TEST_TICKERS = ["NVDA", "AAPL"]


@SKIP_NO_API
class TestLiveDataFetch:
    """Test fetching real data from Twelve Data API."""
    
    @pytest.mark.parametrize("ticker", TEST_TICKERS)
    def test_fetch_real_data(self, ticker):
        """Fetch real OHLCV data from API."""
        data = fetch_from_api(ticker, API_KEY, outputsize=250)
        
        assert "values" in data
        assert len(data["values"]) >= 200
        
        # Check first value has expected fields
        first = data["values"][0]
        assert "datetime" in first
        assert "open" in first
        assert "close" in first
        assert "volume" in first
        
        print(f"✅ {ticker}: Fetched {len(data['values'])} days of data")
        print(f"   Latest: {first['datetime']} Close=${first['close']}")
        
        time.sleep(8)  # Rate limit: 8 req/min
    
    @pytest.mark.parametrize("ticker", TEST_TICKERS[:1])  # Just 1 ticker
    def test_full_pipeline_live(self, ticker):
        """Full pipeline with live API data."""
        # 1. Fetch from API
        data = fetch_from_api(ticker, API_KEY, outputsize=250)
        df = api_response_to_dataframe(data)
        
        assert len(df) >= 200
        print(f"\n📊 {ticker} Live Data Pipeline:")
        print(f"   Data Range: {df.index[0].date()} to {df.index[-1].date()}")
        
        # 2. Add indicators
        df = add_standard_indicators(df)
        
        last = df.iloc[-1]
        print(f"   Price: ${last['close']:.2f}")
        print(f"   RSI: {last['RSI']:.1f}")
        print(f"   SMA20: ${last['SMA_20']:.2f}")
        print(f"   SMA200: ${last['SMA_200']:.2f}")
        
        # 3. Calculate score
        score, breakdown = calculate_bullish_score(df)
        print(f"   Bullish Score: {score:.1f}/10")
        print(f"   Breakdown: {breakdown}")
        
        assert 0 <= score <= 10
        
        # 4. Calculate matrix
        matrix = calculate_matrix(df)
        matrix['score'] = score
        
        print(f"   Above SMA200: {matrix.get('above_SMA200', 'N/A')}")
        print(f"   Golden Cross: {matrix.get('golden_cross', 'N/A')}")
        
        # 5. Evaluate triggers
        results = evaluate_ticker(
            ticker=ticker,
            flags=matrix,
            list_type='watchlist',
            cooldowns={},
            actioned={},
        )
        
        if results:
            print(f"   🚨 SIGNALS:")
            for r in results:
                print(f"      {r.signal} -> {r.action}")
        else:
            print(f"   No signals triggered")
        
        # 6. Check divergence
        divergence = detect_combined_divergence(df, lookback=14)
        if divergence.type != DivergenceType.NONE:
            print(f"   Divergence: {divergence.type.value} (strength={divergence.strength:.2f})")
        
        time.sleep(8)


@SKIP_NO_API 
class TestLiveIndicatorAccuracy:
    """Verify indicator calculations against live data."""
    
    def test_nvda_indicators_reasonable(self):
        """NVDA indicators should be in reasonable ranges."""
        data = fetch_from_api("NVDA", API_KEY, outputsize=250)
        df = api_response_to_dataframe(data)
        df = add_standard_indicators(df)
        
        last = df.iloc[-1]
        
        # RSI should be 0-100
        assert 0 <= last['RSI'] <= 100, f"RSI out of range: {last['RSI']}"
        
        # Stochastic should be 0-100
        assert 0 <= last['STOCH_K'] <= 100, f"Stoch K out of range: {last['STOCH_K']}"
        
        # Price should be above $50 (NVDA is a high-value stock)
        assert last['close'] > 50, f"NVDA price too low: {last['close']}"
        
        # SMA200 should exist and be positive
        assert last['SMA_200'] > 0, f"SMA200 invalid: {last['SMA_200']}"
        
        # MACD should exist
        assert 'MACD' in df.columns
        assert 'MACD_HIST' in df.columns
        
        print(f"\n✅ NVDA Indicators Validated:")
        print(f"   RSI: {last['RSI']:.1f}")
        print(f"   Stoch K: {last['STOCH_K']:.1f}")
        print(f"   MACD Hist: {last['MACD_HIST']:.4f}")
        print(f"   BB Width: {last['BB_WIDTH']:.2f}%")
        
        time.sleep(8)


@SKIP_NO_API
class TestLiveTriggerDetection:
    """Test trigger detection with live data."""
    
    def test_evaluate_nvda_triggers(self):
        """Evaluate all trigger types for NVDA."""
        data = fetch_from_api("NVDA", API_KEY, outputsize=250)
        df = api_response_to_dataframe(data)
        df = add_standard_indicators(df)
        
        matrix = calculate_matrix(df)
        score, _ = calculate_bullish_score(df)
        matrix['score'] = score
        
        # Test watchlist signals
        watchlist_results = evaluate_ticker(
            ticker="NVDA",
            flags=matrix,
            list_type='watchlist',
            cooldowns={},
            actioned={},
        )
        
        # Test portfolio signals
        portfolio_results = evaluate_ticker(
            ticker="NVDA",
            flags=matrix,
            list_type='portfolio',
            cooldowns={},
            actioned={},
        )
        
        print(f"\n📈 NVDA Live Trigger Evaluation:")
        print(f"   Score: {score:.1f}/10")
        print(f"   Watchlist Signals: {len(watchlist_results)}")
        for r in watchlist_results:
            print(f"      • {r.signal}: {r.action}")
        
        print(f"   Portfolio Signals: {len(portfolio_results)}")
        for r in portfolio_results:
            print(f"      • {r.signal}: {r.action}")
        
        # Validate signal structure
        for r in watchlist_results + portfolio_results:
            assert r.ticker == "NVDA"
            assert r.action in ['BUY', 'SELL', 'ALERT']
            assert len(r.signal) > 0


if __name__ == "__main__":
    # Run directly for quick testing
    import sys
    
    if API_KEY:
        print(f"API Key found: {API_KEY[:10]}...")
        
        for ticker in TEST_TICKERS:
            print(f"\nFetching {ticker}...")
            try:
                data = fetch_from_api(ticker, API_KEY)
                df = api_response_to_dataframe(data)
                df = add_standard_indicators(df)
                
                score, _ = calculate_bullish_score(df)
                print(f"  {ticker}: Price=${df['close'].iloc[-1]:.2f}, Score={score:.1f}")
                
                time.sleep(8)
            except Exception as e:
                print(f"  Error: {e}")
    else:
        print("No API key found")
        sys.exit(1)

