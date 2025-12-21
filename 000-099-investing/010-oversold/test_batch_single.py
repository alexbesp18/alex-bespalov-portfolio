
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("TWELVE_DATA_API_KEY")
if not api_key:
    print("No API key found")
    exit(1)

url = "https://api.twelvedata.com/time_series"
symbols = "AAPL"
params = {
    "symbol": symbols,
    "interval": "1day",
    "outputsize": 1,
    "apikey": api_key
}

print(f"Requesting batch for {symbols}...")
response = requests.get(url, params=params)
try:
    data = response.json()
    print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Error parsing JSON: {e}")
