"""
Google Sheets integration for writing analysis results.

Provides color-coded output with 22 columns of technical data.
"""

import logging
from pathlib import Path
from typing import Dict, Optional

import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)


class SheetColors:
    """RGB color definitions for Google Sheets."""
    DARK_GREEN = {'red': 0.22, 'green': 0.6, 'blue': 0.29}
    LIGHT_GREEN = {'red': 0.71, 'green': 0.84, 'blue': 0.66}
    YELLOW = {'red': 1.0, 'green': 0.95, 'blue': 0.6}
    LIGHT_RED = {'red': 0.96, 'green': 0.6, 'blue': 0.6}
    DARK_RED = {'red': 0.8, 'green': 0.2, 'blue': 0.2}
    WHITE = {'red': 1.0, 'green': 1.0, 'blue': 1.0}
    LIGHT_BLUE = {'red': 0.8, 'green': 0.92, 'blue': 0.97}
    HEADER_DARK = {'red': 0.2, 'green': 0.2, 'blue': 0.2}


class SheetsWriter:
    """
    Write analysis results to Google Sheets with formatting.
    
    Creates a color-coded 22-column layout with:
    - Ticker info
    - Technical scores
    - Support/Resistance levels
    - Moving averages
    - Momentum indicators
    - Trend analysis
    """
    
    HEADERS = [
        'Ticker', 'Price', 'Score', 'Entry', 'Support', 'Key Supp',
        'Resist', 'Strong Res', 'MA20', 'MA50', 'MA200', 'RSI',
        'Agreement', 'Notes', 'Trend', 'ADX', 'Volume', 'OBV',
        'Divergence', 'Volatility', 'Max DD', 'VWAP'
    ]
    
    COLUMN_WIDTHS = {
        'A': 80, 'B': 90, 'C': 70, 'D': 90, 'E': 90, 'F': 90,
        'G': 90, 'H': 100, 'I': 90, 'J': 90, 'K': 90, 'L': 70,
        'M': 120, 'N': 180, 'O': 160, 'P': 70, 'Q': 100, 'R': 80,
        'S': 120, 'T': 100, 'U': 80, 'V': 90
    }
    
    def __init__(self, sheet_url: str, creds_file: Optional[str] = None):
        """
        Initialize sheets connection.
        
        Args:
            sheet_url: Google Sheets URL
            creds_file: Path to service account JSON (auto-detects if None)
        """
        self.sheet_url = sheet_url
        self.sheet = None
        
        if not sheet_url:
            logger.warning("No Google Sheet URL provided")
            return
        
        # Find credentials file
        if creds_file is None:
            creds_file = self._find_credentials()
        
        if creds_file is None:
            logger.warning("No service account JSON found, Sheets disabled")
            return
        
        self._connect(creds_file)
    
    def _find_credentials(self) -> Optional[str]:
        """Find service account credentials file."""
        for name in ['service-account.json', 'credentials.json', 'google-credentials.json']:
            if Path(name).exists():
                return name
        return None
    
    def _connect(self, creds_file: str) -> None:
        """Connect to Google Sheets."""
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_file(creds_file, scopes=scope)
            gc = gspread.authorize(creds)
            self.sheet = gc.open_by_url(self.sheet_url).worksheet('TechAnalysis')
            logger.info("Connected to Google Sheet")
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            self.sheet = None
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to sheets."""
        return self.sheet is not None
    
    def setup_headers(self) -> None:
        """Setup header row with proper formatting."""
        if not self.sheet:
            return
        
        self.sheet.update('A1:V1', [self.HEADERS])
        
        header_format = {
            'requests': [
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': self.sheet.id,
                            'startRowIndex': 0,
                            'endRowIndex': 1,
                            'startColumnIndex': 0,
                            'endColumnIndex': 22
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'backgroundColor': SheetColors.HEADER_DARK,
                                'textFormat': {
                                    'foregroundColor': SheetColors.WHITE,
                                    'fontSize': 11,
                                    'bold': True
                                },
                                'horizontalAlignment': 'CENTER',
                                'verticalAlignment': 'MIDDLE'
                            }
                        },
                        'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)'
                    }
                },
                {
                    'updateSheetProperties': {
                        'properties': {
                            'sheetId': self.sheet.id,
                            'gridProperties': {'frozenRowCount': 1}
                        },
                        'fields': 'gridProperties.frozenRowCount'
                    }
                }
            ]
        }
        
        self.sheet.spreadsheet.batch_update(header_format)
        self._setup_column_widths()
        logger.info("Headers configured with formatting")
    
    def _setup_column_widths(self) -> None:
        """Set optimal column widths."""
        requests = []
        for col, width in self.COLUMN_WIDTHS.items():
            col_index = ord(col) - ord('A')
            requests.append({
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': self.sheet.id,
                        'dimension': 'COLUMNS',
                        'startIndex': col_index,
                        'endIndex': col_index + 1
                    },
                    'properties': {'pixelSize': width},
                    'fields': 'pixelSize'
                }
            })
        self.sheet.spreadsheet.batch_update({'requests': requests})
    
    def write_result(self, row: int, result: Dict) -> bool:
        """
        Write analysis result to a row.
        
        Args:
            row: Row number to write to
            result: Analysis result dictionary
            
        Returns:
            True if successful
        """
        if not self.sheet:
            return False
        
        try:
            indicators = result.get('indicators', {})
            trend_analysis = result.get('trend_analysis', {})
            divergence = result.get('divergence', {})
            volume_metrics = result.get('volume_metrics', {})
            volatility = result.get('volatility', {})
            risk = result.get('risk', {})
            
            notes = f"{result.get('agreement_level', '')} | {len(result.get('discrepancies', {}))} disc"
            trend_str = f"{trend_analysis.get('trend', 'N/A')} ({trend_analysis.get('confidence', 0)*100:.0f}%)"
            
            vol_confirms = "✓" if volume_metrics.get('volume_confirms_price', False) else "✗"
            volume_str = f"{volume_metrics.get('relative_volume', 'N/A')} {vol_confirms}"
            
            score = result.get('technical_score', 0)
            adx_val = indicators.get('adx', 0)
            rsi_val = result.get('rsi', indicators.get('rsi', 50))
            max_dd = risk.get('max_drawdown', 0)
            
            row_data = [
                result.get('current_price', ''),
                score,
                result.get('optimal_entry', ''),
                result.get('closest_support', ''),
                result.get('key_support', ''),
                result.get('closest_resistance', ''),
                result.get('strongest_resistance', ''),
                result.get('ma_20', ''),
                result.get('ma_50', ''),
                result.get('ma_200', ''),
                rsi_val,
                result.get('agreement_level', ''),
                notes,
                trend_str,
                round(adx_val, 1) if adx_val else '',
                volume_str,
                indicators.get('obv_trend', ''),
                divergence.get('divergence_type', 'None'),
                volatility.get('volatility_regime', ''),
                f"{max_dd:.1f}%" if max_dd else '',
                round(indicators.get('vwap', 0), 2) if indicators.get('vwap') else ''
            ]
            
            self.sheet.update(values=[row_data], range_name=f'B{row}:V{row}')
            self._apply_color_coding(row, score, adx_val, rsi_val, trend_str,
                                    volume_str, divergence.get('divergence_type', 'None'),
                                    volatility.get('volatility_regime', ''), max_dd)
            
            logger.info(f"Written to row {row}")
            return True
            
        except Exception as e:
            logger.error(f"Sheet write failed: {e}")
            return False
    
    def _apply_color_coding(
        self, row: int, score: float, adx: float, rsi: float,
        trend: str, volume: str, divergence: str,
        volatility: str, max_dd: float
    ) -> None:
        """Apply color coding to cells based on values."""
        if not self.sheet:
            return
        
        try:
            requests = [
                self._cell_format(row, 2, self._score_color(score), bold=True, center=True),
                self._cell_format(row, 11, self._rsi_color(rsi), center=True),
                self._cell_format(row, 14, self._trend_color(trend), bold=True, center=True),
                self._cell_format(row, 16, self._volume_color(volume), center=True),
                self._cell_format(row, 18, self._divergence_color(divergence),
                                 bold=(divergence != 'None'), center=True),
                self._cell_format(row, 19, self._volatility_color(volatility), center=True),
            ]
            
            if adx:
                requests.append(self._cell_format(row, 15, self._adx_color(adx), center=True))
            if max_dd:
                requests.append(self._cell_format(row, 20, self._drawdown_color(max_dd), center=True))
            
            self.sheet.spreadsheet.batch_update({'requests': requests})
        except Exception as e:
            logger.warning(f"Color coding failed for row {row}: {e}")
    
    def _cell_format(
        self, row: int, col: int, color: Dict,
        bold: bool = False, center: bool = False
    ) -> Dict:
        """Create cell format request."""
        fmt = {
            'repeatCell': {
                'range': {
                    'sheetId': self.sheet.id,
                    'startRowIndex': row - 1,
                    'endRowIndex': row,
                    'startColumnIndex': col,
                    'endColumnIndex': col + 1
                },
                'cell': {'userEnteredFormat': {'backgroundColor': color}},
                'fields': 'userEnteredFormat.backgroundColor'
            }
        }
        
        if bold:
            fmt['repeatCell']['cell']['userEnteredFormat']['textFormat'] = {'bold': True}
            fmt['repeatCell']['fields'] += ',userEnteredFormat.textFormat'
        if center:
            fmt['repeatCell']['cell']['userEnteredFormat']['horizontalAlignment'] = 'CENTER'
            fmt['repeatCell']['fields'] += ',userEnteredFormat.horizontalAlignment'
        
        return fmt
    
    # Color helper methods
    def _score_color(self, score: float) -> Dict:
        if score >= 8: return SheetColors.DARK_GREEN
        if score >= 6: return SheetColors.LIGHT_GREEN
        if score >= 4: return SheetColors.YELLOW
        return SheetColors.LIGHT_RED
    
    def _rsi_color(self, rsi: float) -> Dict:
        if rsi > 70: return SheetColors.LIGHT_RED
        if rsi < 30: return SheetColors.LIGHT_GREEN
        return SheetColors.WHITE
    
    def _trend_color(self, trend: str) -> Dict:
        if 'STRONG_UPTREND' in trend: return SheetColors.DARK_GREEN
        if 'UPTREND' in trend: return SheetColors.LIGHT_GREEN
        if 'SIDEWAYS' in trend: return SheetColors.YELLOW
        if 'STRONG_DOWNTREND' in trend: return SheetColors.DARK_RED
        if 'DOWNTREND' in trend: return SheetColors.LIGHT_RED
        return SheetColors.WHITE
    
    def _adx_color(self, adx: float) -> Dict:
        if adx > 25: return SheetColors.LIGHT_GREEN
        if adx > 20: return SheetColors.YELLOW
        return SheetColors.LIGHT_RED
    
    def _volume_color(self, volume: str) -> Dict:
        if '✓' in volume: return SheetColors.LIGHT_GREEN
        if '✗' in volume: return SheetColors.LIGHT_RED
        return SheetColors.WHITE
    
    def _divergence_color(self, divergence: str) -> Dict:
        if 'BEARISH' in divergence: return SheetColors.LIGHT_RED
        if 'BULLISH' in divergence: return SheetColors.LIGHT_GREEN
        return SheetColors.WHITE
    
    def _volatility_color(self, volatility: str) -> Dict:
        if volatility == 'VERY_HIGH': return SheetColors.DARK_RED
        if volatility == 'HIGH': return SheetColors.LIGHT_RED
        if volatility == 'NORMAL': return SheetColors.LIGHT_GREEN
        if volatility == 'LOW': return SheetColors.LIGHT_BLUE
        return SheetColors.WHITE
    
    def _drawdown_color(self, drawdown: float) -> Dict:
        if drawdown > -5: return SheetColors.LIGHT_GREEN
        if drawdown > -10: return SheetColors.YELLOW
        return SheetColors.LIGHT_RED
