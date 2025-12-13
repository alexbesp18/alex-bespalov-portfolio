import datetime
import urllib.request
import urllib.error
import json
import logging
import sys
import os
from typing import List, Dict, Optional, Any

import gspread  # type: ignore
from google.oauth2.service_account import Credentials  # type: ignore
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings
from src.utils.parsing import parse_products
from src.models import Product

# Setup Logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_current_week_url() -> str:
    """
    Constructs the URL for the CURRENT week.
    For Product Hunt, the URL structure is /leaderboard/weekly/YEAR/WEEK.
    """
    today = datetime.datetime.now()
    year = today.year
    # ISO week
    week = today.isocalendar()[1]
    
    url = f"https://www.producthunt.com/leaderboard/weekly/{year}/{week}"
    logger.info(f"Target URL: {url}")
    return url

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60)
)
def fetch_html(url: str) -> str:
    """
    Fetches HTML content from the given URL with robust headers and retry logic.
    Raises exception on failure to trigger retry.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as response:
        result: str = response.read().decode('utf-8')
        return result

def save_to_gsheet(products: List[Product]) -> None:
    """Saves the list of products to Google Sheets."""
    if not settings.gdrive_api_key_json:
        logger.warning("No Google Drive Creds found (GDRIVE_API_KEY). Skipping Sheet update.")
        # Dump model to json string for logging
        logger.info(f"Data to be saved: {[p.model_dump() for p in products]}")
        return

    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        try:
            creds_dict = json.loads(settings.gdrive_api_key_json)
        except json.JSONDecodeError:
            # Fallback if it's a file path
            if os.path.exists(settings.gdrive_api_key_json):
                 logger.info(f"Loading credentials from file: {settings.gdrive_api_key_json}")
                 with open(settings.gdrive_api_key_json, 'r') as f:
                     creds_dict = json.load(f)
            else:
                logger.error("GDRIVE_API_KEY is not valid JSON string nor a valid file path.")
                return

        # Log the service account email to help user debug
        if 'client_email' in creds_dict:
            logger.info(f"Authenticating as: {creds_dict['client_email']}")

        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        try:
            if settings.gsheet_id:
                logger.info(f"Opening sheet by ID: {settings.gsheet_id}")
                sh = client.open_by_key(settings.gsheet_id)
                sheet = sh.worksheet(settings.gsheet_tab)
            else:
                logger.info(f"Opening sheet by Name: {settings.gsheet_name}")
                sheet = client.open(settings.gsheet_name).worksheet(settings.gsheet_tab)
        except gspread.WorksheetNotFound:
            logger.info(f"Worksheet {settings.gsheet_tab} not found, creating it.")
            if settings.gsheet_id:
                sh = client.open_by_key(settings.gsheet_id)
            else:
                sh = client.open(settings.gsheet_name)
            sheet = sh.add_worksheet(title=settings.gsheet_tab, rows=100, cols=10)
            sheet.append_row(["Date", "Rank", "Name", "URL", "Description"])
            
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        rows_to_add: List[List[Any]] = []
        for i, p in enumerate(products):
            rows_to_add.append([
                today,
                i+1,
                p.name,
                str(p.url),
                p.description
            ])
            
        sheet.append_rows(rows_to_add)
        logger.info("Successfully wrote to Google Sheet.")
        
    except Exception as e:
        logger.error(f"Error saving to Sheet: {e}", exc_info=True)

def main() -> None:
    logger.info("Starting Product Hunt Extraction Job")
    url = get_current_week_url()
    
    try:
        html = fetch_html(url)
    except Exception as e:
        logger.error(f"Failed to fetch {url} after retries: {e}")
        return

    if not html:
        logger.error("No HTML returned. Aborting.")
        return

    top_products = parse_products(html, limit=10)
    
    if top_products:
        save_to_gsheet(top_products)
    else:
        logger.warning("No products found in HTML.")

if __name__ == "__main__":
    main()
