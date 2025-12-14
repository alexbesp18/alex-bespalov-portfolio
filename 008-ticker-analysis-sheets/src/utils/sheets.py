import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Any, Union
import datetime as dt
from src.utils.logging import setup_logger

logger = setup_logger(__name__)

class SheetManager:
    """Manage Google Sheets read/write operations"""
    
    def __init__(self, credentials_file: str, spreadsheet_name: str):
        logger.info("📊 Connecting to Google Sheets...")
        
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        try:
            creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
            self.gc = gspread.authorize(creds)
            self.spreadsheet = self.gc.open(spreadsheet_name)
            logger.info(f"✅ Connected to: {spreadsheet_name}")
        except FileNotFoundError:
            logger.error(f"❌ Credentials file not found: {credentials_file}")
            raise
        except gspread.SpreadsheetNotFound:
            logger.error(f"❌ Spreadsheet '{spreadsheet_name}' not found.")
            raise ValueError(f"Spreadsheet '{spreadsheet_name}' not found.")
        except Exception as e:
            logger.error(f"❌ Error connecting to Sheets: {e}")
            raise
    
    def get_tickers(self, tab_name: str, column: str = 'A', start_row: int = 2) -> List[str]:
        """Read tickers from specified tab and column."""
        try:
            sheet = self.spreadsheet.worksheet(tab_name)
        except gspread.WorksheetNotFound:
            # logger.warning(f"Tab '{tab_name}' not found looking for tickers.")
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
    
    def write_tech_data(self, tab_name: str, data: List[Dict[str, Any]], append: bool = False) -> None:
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
        try:
            if append:
                sheet.append_rows(rows)
                logger.info(f"✅ Appended {len(data)} rows to {tab_name}")
            else:
                sheet.clear()
                sheet.update(rows, 'A1')
                logger.info(f"✅ Wrote {len(data)} rows to {tab_name}")
        except Exception as e:
            logger.error(f"❌ Error writing to {tab_name}: {e}")
            raise
    
    def write_transcripts(self, tab_name: str, data: List[Dict[str, Any]], append: bool = False) -> None:
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

        try:
            if append:
                sheet.append_rows(rows)
                logger.info(f"✅ Appended {len(data)} rows to {tab_name}")
            else:
                sheet.clear()
                sheet.update(rows, 'A1')
                logger.info(f"✅ Wrote {len(data)} rows to {tab_name}")
        except Exception as e:
            logger.error(f"❌ Error writing transcripts to {tab_name}: {e}")
            raise
