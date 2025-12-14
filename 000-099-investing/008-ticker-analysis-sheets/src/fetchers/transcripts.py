import pandas as pd
import datetime as dt
import json
from typing import Dict, Any, Optional

from src.utils.logging import setup_logger

logger = setup_logger(__name__)

# Optional import
try:
    from defeatbeta_api.data.ticker import Ticker
    DEFEATBETA_AVAILABLE = True
except ImportError:
    DEFEATBETA_AVAILABLE = False
    logger.warning("defeatbeta-api not installed. Transcripts will be skipped.")

class TranscriptFetcher:
    """Fetch earnings transcripts from defeatbeta-api"""
    
    def __init__(self, min_chars: int = 600, earliest_year_offset: int = 1):
        self.min_chars = min_chars
        self.earliest_year = dt.date.today().year - earliest_year_offset
    
    def fetch_latest(self, ticker: str) -> Dict[str, Any]:
        """Fetch the latest transcript for a ticker."""
        if not DEFEATBETA_AVAILABLE:
            return {'Ticker': ticker, 'Status': "ERROR: defeatbeta not installed"}
        
        logger.info(f"📝 Fetching transcript for {ticker}...")
        
        try:
            tkr = Ticker(ticker)
            tr = tkr.earning_call_transcripts()
            df_list = tr.get_transcripts_list()
            
            try:
                df = pd.DataFrame(df_list)
            except Exception:
                df = df_list if isinstance(df_list, pd.DataFrame) else pd.DataFrame(df_list)
            
            if df.empty:
                logger.warning(f"No transcripts found for {ticker}")
                return {'Ticker': ticker, 'Status': 'NO_DATA', 'Period': 'N/A'}
            
            # Filter by year
            if 'fiscal_year' in df.columns:
                df = df[df['fiscal_year'].astype(int) >= self.earliest_year]
            
            if df.empty:
                logger.warning(f"No recent transcripts for {ticker}")
                return {'Ticker': ticker, 'Status': 'NO_DATA', 'Period': 'N/A'}
            
            # Sort by date
            sort_cols = [c for c in ['report_date', 'fiscal_year', 'fiscal_quarter'] if c in df.columns]
            if sort_cols:
                df = df.sort_values(sort_cols, ascending=[False] * len(sort_cols))
            
            # Get the latest transcript
            row = df.iloc[0]
            y = int(row.get('fiscal_year', 0))
            q = int(row.get('fiscal_quarter', 0))
            report_date = str(row.get('report_date', 'N/A'))
            period = f"{y}Q{q}"
            
            # Fetch full transcript
            tx = tr.get_transcript(y, q)
            
            # Extract text
            text = self._normalize_transcript_text(tx)
            
            text = (text or "").strip()
            char_count = len(text)
            
            if char_count < self.min_chars:
                logger.warning(f"Transcript too short for {ticker}: {char_count} chars")
                return {
                    'Ticker': ticker,
                    'Period': period,
                    'Earnings_Date': report_date,
                    'Char_Count': char_count,
                    'Status': f'NO_DATA (only {char_count} chars)',
                    'Full_Text': ''
                }
            
            logger.info(f"✅ {ticker} {period}: {char_count:,} chars")
            
            return {
                'Ticker': ticker,
                'Period': period,
                'Earnings_Date': report_date,
                'Char_Count': char_count,
                'Status': 'OK',
                'Full_Text': text
            }
            
        except Exception as e:
            logger.error(f"Error fetching transcript for {ticker}: {e}")
            return {'Ticker': ticker, 'Status': f"ERROR: {str(e)[:50]}"}
    
    def _normalize_transcript_text(self, obj: Any) -> str:
        """Convert various transcript formats to plain text."""
        # Helper to extract text from pandas/dict/list structure
        try:
             # If it's a DataFrame-like object
            if hasattr(obj, 'columns') and 'content' in obj.columns:
                 return "\n".join(str(x) for x in obj['content'].tolist())
        except Exception:
            pass

        if obj is None:
            return ""
        if isinstance(obj, str):
            return obj
        if isinstance(obj, list):
            parts = []
            for item in obj:
                if isinstance(item, dict):
                    speaker = item.get('speaker') or item.get('name', '')
                    content = item.get('text') or item.get('content', '')
                    parts.append(f"{speaker}: {content}" if speaker else str(content))
                else:
                    parts.append(str(item))
            return "\n".join(parts)
        if isinstance(obj, dict):
            for k in ('transcript', 'prepared_remarks', 'q_and_a', 'content', 'text'):
                if k in obj:
                    return self._normalize_transcript_text(obj[k])
            try:
                return json.dumps(obj, ensure_ascii=False, indent=2)
            except Exception:
                return str(obj)
        return str(obj)
