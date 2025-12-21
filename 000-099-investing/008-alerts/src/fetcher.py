import os
import time
import requests
import json
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class TwelveDataFetcher:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def fetch_time_series(self, symbol, interval="1day", outputsize=300):
        url = f"{self.base_url}/time_series"
        params = {
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize,
            "apikey": self.api_key
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if "status" in data and data["status"] == "error":
                logger.error(f"API Error Response for {symbol}: {data}") # Added logging
                raise ValueError(f"API Error for {symbol}: {data['message']}")
            if "values" not in data:
                 logger.warning(f"Unexpected API response for {symbol}: {data.keys()}") # Added logging
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching {symbol}: {e}")
            raise

    def fetch_batch_time_series(self, symbols, interval="1day", outputsize=300):
        """
        Fetches data for multiple symbols sequentially to respect API rate limits.
        Free Tier: ~8 requests per minute.
        Strategy: 1 request every 12 seconds (~5 req/min) to be safe.
        """
        results = {}
        total = len(symbols)
        
        for i, symbol in enumerate(symbols):
            logger.info(f"Fetching {symbol} ({i+1}/{total})...")
            try:
                # Reuse the single fetch method with retry logic
                data = self.fetch_time_series(symbol, interval, outputsize)
                results[symbol] = data
                
                # Sleep to respect rate limit, but don't sleep after the last one
                if i < total - 1:
                    logger.info("Sleeping 12s for rate limit...")
                    time.sleep(12) 
                    
            except Exception as e:
                logger.error(f"Failed to fetch {symbol}: {e}")
                # Continue to next symbol even if one fails
                continue
        
        return results

if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    api_key = os.getenv("TWELVE_DATA_API_KEY")
    if api_key:
        fetcher = TwelveDataFetcher(api_key)
        data = fetcher.fetch_time_series("AAPL")
        print(f"Fetched {len(data['values'])} rows for AAPL")
