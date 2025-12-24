"""
Google Sheets manager with row replacement support.
Handles reading tickers and writing data back to sheets.
"""

from typing import Dict, List, Any

import gspread
from google.oauth2.service_account import Credentials


class SheetManager:
    """
    Google Sheets manager with:
    - Ticker reading from main sheet
    - Row replacement for updates (not just append)
    - Conditional formatting for transcripts
    """

    # Column order for tech data
    TECH_COLUMNS = [
        'Ticker', 'Bullish_Score', 'Price', 'Change%', 'RSI', 'MACD', 'MACD_Signal', 'MACD_Hist',
        'ADX', 'Trend', 'SMA_20', 'SMA_50', 'SMA_200', 'BB_Upper', 'BB_Lower',
        'ATR', 'Stoch_K', 'Stoch_D', 'VWAP', 'OBV_Trend', 'Volatility',
        'Divergence', 'Volume_Rel', '52W_High', '52W_Low', 'Status', 'Updated',
        'Bullish_Reason', 'Tech_Summary'
    ]

    # Column order for transcripts
    TRANSCRIPT_COLUMNS = [
        'Ticker', 'Period', 'Earnings_Date', 'Char_Count',
        'Key_Metrics', 'Guidance', 'Tone', 'Summary', 'Status', 'Updated', 'Days_Since_Earnings'
    ]

    def __init__(self, credentials_file: str, spreadsheet_name: str, verbose: bool = False):
        """
        Initialize Sheet manager.

        Args:
            credentials_file: Path to Google service account JSON
            spreadsheet_name: Name of the spreadsheet to open
            verbose: Print detailed progress
        """
        self.verbose = verbose

        if verbose:
            print("📊 Connecting to Google Sheets...")

        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
        self.gc = gspread.authorize(creds)

        try:
            self.spreadsheet = self.gc.open(spreadsheet_name)
            if verbose:
                print(f"   ✅ Connected to: {spreadsheet_name}")
        except gspread.SpreadsheetNotFound:
            raise ValueError(f"Spreadsheet '{spreadsheet_name}' not found. "
                           "Make sure you shared it with the service account.")

    @staticmethod
    def col_num_to_letter(col_num: int) -> str:
        """
        Convert 1-based column number to Excel-style letter(s).
        e.g., 1 -> 'A', 26 -> 'Z', 27 -> 'AA', 29 -> 'AC'
        """
        result = ""
        while col_num > 0:
            col_num, remainder = divmod(col_num - 1, 26)
            result = chr(65 + remainder) + result
        return result

    # =========================================================================
    # TICKER READING
    # =========================================================================

    def get_tickers(self, tab_name: str, column: str = 'A', start_row: int = 2) -> List[str]:
        """
        Read tickers from specified tab and column.

        Args:
            tab_name: Name of the sheet tab
            column: Column letter containing tickers
            start_row: First row with data (default 2 = skip header)

        Returns:
            List of ticker symbols (uppercase, cleaned)
        """
        try:
            sheet = self.spreadsheet.worksheet(tab_name)
        except gspread.WorksheetNotFound:
            raise ValueError(f"Tab '{tab_name}' not found in spreadsheet")

        col_idx = ord(column.upper()) - ord('A') + 1
        values = sheet.col_values(col_idx)

        tickers = []
        for i, val in enumerate(values):
            if i < start_row - 1:  # Skip header rows
                continue
            val = str(val).strip().upper()
            if val and val not in ('TICKER', 'SYMBOL', ''):
                tickers.append(val)

        return tickers

    def get_existing_tickers(self, tab_name: str, column: str = 'A',
                             start_row: int = 2) -> List[str]:
        """Read tickers from specified tab to see what's already there."""
        try:
            return self.get_tickers(tab_name, column, start_row)
        except (ValueError, gspread.WorksheetNotFound):
            return []

    def get_existing_tech_data(self, tab_name: str) -> Dict[str, Dict[str, Any]]:
        """
        Read all existing tech data from the specified tab.

        Returns:
            Dict mapping ticker -> {Price: float, row_number: int, ...}
        """
        try:
            sheet = self.spreadsheet.worksheet(tab_name)
        except gspread.WorksheetNotFound:
            return {}

        try:
            records = sheet.get_all_records()
        except Exception as e:
            if self.verbose:
                print(f"    ⚠️  Error reading existing data: {e}")
            return {}

        result = {}
        for i, record in enumerate(records):
            ticker = str(record.get('Ticker', '')).strip().upper()
            if not ticker:
                continue

            # Parse price - handle various formats
            price_val = record.get('Price', '')
            try:
                if isinstance(price_val, (int, float)):
                    price = float(price_val)
                elif isinstance(price_val, str):
                    price = float(price_val.replace('$', '').replace(',', '').strip())
                else:
                    price = None
            except (ValueError, TypeError):
                price = None

            # Row number is i + 2 (0-indexed records + 1 header row + 1 for 1-based)
            result[ticker] = {
                'Price': price,
                'row_number': i + 2,
                'record': record
            }

        return result

    # =========================================================================
    # TECH DATA WRITING
    # =========================================================================

    def write_tech_data(self, tab_name: str, data: List[Dict], append: bool = False):
        """
        Write technical data to specified tab (simple overwrite or append).

        Args:
            tab_name: Name of the sheet tab
            data: List of dicts with tech indicator values
            append: If True, append to existing data
        """
        if not data:
            return

        try:
            sheet = self.spreadsheet.worksheet(tab_name)
        except gspread.WorksheetNotFound:
            sheet = self.spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=35)
            append = False

        rows = []
        if not append:
            rows.append(self.TECH_COLUMNS)

        for d in data:
            row = [d.get(col, '') for col in self.TECH_COLUMNS]
            rows.append(row)

        if append:
            sheet.append_rows(rows)
            if self.verbose:
                print(f"   ✅ Appended {len(data)} rows to {tab_name}")
        else:
            sheet.clear()
            sheet.update(rows, 'A1')
            if self.verbose:
                print(f"   ✅ Wrote {len(data)} rows to {tab_name}")

    def write_tech_data_with_replacements(self, tab_name: str, data: List[Dict],
                                           existing_data: Dict[str, Dict]):
        """
        Write technical data with row replacement support.

        - For tickers that exist: update the specific row
        - For new tickers: append to the end

        Args:
            tab_name: Name of the sheet tab
            data: List of dicts with tech indicator values
            existing_data: Dict from get_existing_tech_data()
        """
        if not data:
            return

        try:
            sheet = self.spreadsheet.worksheet(tab_name)
        except gspread.WorksheetNotFound:
            sheet = self.spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=35)
            sheet.update([self.TECH_COLUMNS], 'A1')

        # Separate into updates and appends
        rows_to_update = []  # (row_number, row_data)
        rows_to_append = []

        for d in data:
            ticker = d.get('Ticker', '').upper()
            row_data = [d.get(col, '') for col in self.TECH_COLUMNS]

            if ticker in existing_data:
                row_num = existing_data[ticker]['row_number']
                rows_to_update.append((row_num, row_data))
            else:
                rows_to_append.append(row_data)

        # Perform updates for existing rows
        if rows_to_update:
            updates = []
            last_col = self.col_num_to_letter(len(self.TECH_COLUMNS))

            for row_num, row_data in rows_to_update:
                range_str = f'A{row_num}:{last_col}{row_num}'
                updates.append({
                    'range': range_str,
                    'values': [row_data]
                })

            sheet.batch_update(updates)
            if self.verbose:
                print(f"   ✅ Updated {len(rows_to_update)} existing rows in {tab_name}")

        # Append new rows
        if rows_to_append:
            sheet.append_rows(rows_to_append)
            if self.verbose:
                print(f"   ✅ Appended {len(rows_to_append)} new rows to {tab_name}")

    # =========================================================================
    # TRANSCRIPT WRITING
    # =========================================================================

    def write_transcripts(self, tab_name: str, data: List[Dict], append: bool = False):
        """
        Write transcript data to specified tab.

        Args:
            tab_name: Name of the sheet tab
            data: List of dicts with transcript data
            append: If True, append to existing data
        """
        if not data:
            return

        try:
            sheet = self.spreadsheet.worksheet(tab_name)
        except gspread.WorksheetNotFound:
            sheet = self.spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=15)
            append = False

        rows = []
        if not append:
            rows.append(self.TRANSCRIPT_COLUMNS)

        for d in data:
            row = [d.get(col, '') for col in self.TRANSCRIPT_COLUMNS]
            rows.append(row)

        if append:
            sheet.append_rows(rows)
            if self.verbose:
                print(f"   ✅ Appended {len(data)} rows to {tab_name}")
        else:
            sheet.clear()
            sheet.update(rows, 'A1')
            if self.verbose:
                print(f"   ✅ Wrote {len(data)} rows to {tab_name}")

        # Apply conditional formatting
        self.apply_transcript_formatting(tab_name)

    def apply_transcript_formatting(self, tab_name: str):
        """
        Apply conditional formatting to Days_Since_Earnings column.
        - > 90 days: Yellow background
        - > 180 days: Red background
        """
        try:
            sheet = self.spreadsheet.worksheet(tab_name)
            sheet.clear_basic_filter()

            # Column K (Days_Since_Earnings) is index 10 (0-based)
            requests = [
                {
                    "addConditionalFormatRule": {
                        "rule": {
                            "ranges": [{"sheetId": sheet.id, "startColumnIndex": 10,
                                       "endColumnIndex": 11, "startRowIndex": 1}],
                            "booleanRule": {
                                "condition": {"type": "NUMBER_GREATER",
                                            "values": [{"userEnteredValue": "180"}]},
                                "format": {
                                    "backgroundColor": {"red": 1, "green": 0.8, "blue": 0.8},
                                    "textFormat": {"foregroundColor": {"red": 0, "green": 0, "blue": 0}}
                                }
                            }
                        },
                        "index": 0
                    }
                },
                {
                    "addConditionalFormatRule": {
                        "rule": {
                            "ranges": [{"sheetId": sheet.id, "startColumnIndex": 10,
                                       "endColumnIndex": 11, "startRowIndex": 1}],
                            "booleanRule": {
                                "condition": {"type": "NUMBER_GREATER",
                                            "values": [{"userEnteredValue": "90"}]},
                                "format": {
                                    "backgroundColor": {"red": 1, "green": 1, "blue": 0.8},
                                    "textFormat": {"foregroundColor": {"red": 0, "green": 0, "blue": 0}}
                                }
                            }
                        },
                        "index": 1
                    }
                }
            ]

            self.spreadsheet.batch_update({"requests": requests})
            if self.verbose:
                print(f"   🎨 Applied conditional formatting to {tab_name}")

        except Exception as e:
            if self.verbose:
                print(f"   ⚠️  Could not apply formatting: {e}")

