"""
Quick test script to verify yfinance API is working.

This is a utility script for testing the API client functionality.
Run from project root: python scripts/test_api.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api_client import StockDataClient

print("Testing yfinance API...")
print("-" * 50)

# Test a single stock
symbol = "AAPL"
duration = "1 year"

print(f"Fetching {symbol} data for {duration}...")
hist_data = StockDataClient.get_historical_data(symbol, duration)

if hist_data is not None:
    print(f"✓ Success! Retrieved {len(hist_data)} data points")
    print(f"\nFirst few rows:")
    print(hist_data.head())
    print(f"\nLast few rows:")
    print(hist_data.tail())
else:
    print("✗ Failed to fetch data")
    print("Check your internet connection and verify yfinance is installed:")
    print("  pip install -r requirements.txt")

