import datetime
import urllib.request
import urllib.error
import json
import logging
import sys
import os
from typing import List, Dict, Optional, Any

import gspread
from google.oauth2.service_account import Credentials
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

def save_to_gsheet(products: List[Product], date_override: Optional[str] = None) -> None:
    """Saves the list of products to Google Sheets.
    
    Args:
        products: List of Product objects to save.
        date_override: Optional date string to use instead of today's date.
    """
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

        creds: Any = Credentials.from_service_account_info(creds_dict, scopes=scope)
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
            sheet = sh.add_worksheet(title=settings.gsheet_tab, rows=500, cols=10)
        
        # Ensure headers exist on row 1
        headers = ["Date", "Rank", "Name", "Description", "Upvotes", "URL"]
        current_headers = sheet.row_values(1)
        if current_headers != headers:
            logger.info("Setting up headers on row 1")
            sheet.update('A1:F1', [headers])
            
        # Use date_override if provided, otherwise use today
        row_date = date_override if date_override else datetime.datetime.now().strftime("%Y-%m-%d")
        
        rows_to_add: List[List[Any]] = []
        for p in products:
            rows_to_add.append([
                row_date,
                p.rank,
                p.name,
                p.description,
                p.upvotes,
                str(p.url)
            ])
            
        sheet.append_rows(rows_to_add)
        logger.info(f"Appended {len(rows_to_add)} rows.")
        
        # Sort data by Date (desc) then Rank (asc) - excluding header row
        # Column A = Date, Column B = Rank
        try:
            # Get all data to find range
            all_data = sheet.get_all_values()
            if len(all_data) > 1:  # More than just headers
                end_row = len(all_data)
                # Sort range A2:F{end_row} by column A descending, then column B ascending
                sheet.sort((1, 'des'), (2, 'asc'), range=f'A2:F{end_row}')
                logger.info("Sorted data by Date (newest first) then Rank.")
        except Exception as sort_error:
            logger.warning(f"Could not sort sheet: {sort_error}")
        
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
