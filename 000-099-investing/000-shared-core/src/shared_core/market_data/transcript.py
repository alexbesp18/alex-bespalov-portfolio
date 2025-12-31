"""
Earnings transcript client using defeatbeta-api with caching.
Fetches the latest earnings call transcript for each ticker.
"""

import datetime as dt
import json
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

from ..cache.data_cache import DataCache

# defeatbeta is optional
DEFEATBETA_AVAILABLE = True
try:
    from defeatbeta_api.data.ticker import Ticker
except ImportError:
    DEFEATBETA_AVAILABLE = False


class TranscriptClient:
    """
    Earnings transcript fetcher with daily caching.
    Uses defeatbeta-api to fetch transcripts.
    """

    def __init__(self, cache: DataCache, min_chars: int = 600,
                 earliest_year_offset: int = 1, verbose: bool = False):
        """
        Initialize transcript client.

        Args:
            cache: DataCache instance for storing/retrieving data
            min_chars: Minimum transcript length to accept
            earliest_year_offset: How many years back to look for transcripts
            verbose: Print detailed progress
        """
        self.cache = cache
        self.min_chars = min_chars
        self.earliest_year = dt.date.today().year - earliest_year_offset
        self.verbose = verbose

    @staticmethod
    def is_available() -> bool:
        """Check if defeatbeta-api is installed."""
        return DEFEATBETA_AVAILABLE

    def _normalize_text(self, obj: Any) -> str:
        """Convert various transcript formats to plain text."""
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
                    return self._normalize_text(obj[k])
            try:
                return json.dumps(obj, ensure_ascii=False, indent=2)
            except (TypeError, ValueError):
                return str(obj)
        return str(obj)

    def _fetch_from_api(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch the latest transcript from defeatbeta API.

        Returns:
            Dict with transcript metadata and full text, or None on error
        """
        if not DEFEATBETA_AVAILABLE:
            return {'Ticker': ticker, 'Status': "ERROR: defeatbeta not installed"}

        if self.verbose:
            print(f"    📝 Fetching transcript for {ticker} from defeatbeta...")

        try:
            tkr = Ticker(ticker)
            tr = tkr.earning_call_transcripts()
            df_list = tr.get_transcripts_list()

            try:
                df = pd.DataFrame(df_list)
            except (ValueError, TypeError):
                df = df_list if isinstance(df_list, pd.DataFrame) else pd.DataFrame(df_list)

            if df.empty:
                if self.verbose:
                    print("    ⚠️  No transcripts found")
                return {'Ticker': ticker, 'Status': 'NO_DATA', 'Period': 'N/A'}

            # Filter by year
            if 'fiscal_year' in df.columns:
                df = df[df['fiscal_year'].astype(int) >= self.earliest_year]

            if df.empty:
                if self.verbose:
                    print(f"    ⚠️  No recent transcripts (>= {self.earliest_year})")
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
            try:
                tdf = pd.DataFrame(tx)
            except (ValueError, TypeError):
                tdf = tx if isinstance(tx, pd.DataFrame) else pd.DataFrame(tx)

            if not tdf.empty and 'content' in tdf.columns:
                text = "\n".join(str(x) for x in tdf['content'].tolist())
            elif isinstance(tx, dict):
                text = self._normalize_text(tx)
            elif isinstance(tx, list):
                text = self._normalize_text(tx)
            else:
                text = ""

            text = (text or "").strip()
            char_count = len(text)

            if char_count < self.min_chars:
                if self.verbose:
                    print(f"    ⚠️  Transcript too short: {char_count} chars")
                return {
                    'Ticker': ticker,
                    'Period': period,
                    'Earnings_Date': report_date,
                    'Char_Count': char_count,
                    'Status': f'NO_DATA (only {char_count} chars)',
                    'Full_Text': ''
                }

            if self.verbose:
                print(f"    ✅ {ticker} {period}: {char_count:,} chars")

            return {
                'Ticker': ticker,
                'Period': period,
                'Earnings_Date': report_date,
                'Char_Count': char_count,
                'Status': 'OK',
                'Full_Text': text
            }

        except (AttributeError, KeyError, ValueError, TypeError) as e:
            if self.verbose:
                print(f"    ❌ Error: {e}")
            return {'Ticker': ticker, 'Status': f"ERROR: {str(e)[:50]}"}
        except requests.exceptions.RequestException as e:
            if self.verbose:
                print(f"    ❌ Network error: {e}")
            return {'Ticker': ticker, 'Status': f"ERROR: {str(e)[:50]}"}

    def fetch_transcript(self, ticker: str,
                         force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Fetch transcript for a ticker, using cache if available.

        Args:
            ticker: Stock ticker symbol
            force_refresh: Bypass cache and fetch fresh data

        Returns:
            Dict with transcript metadata and text
        """
        ticker = ticker.upper()

        # Check cache first (unless forcing refresh)
        if not force_refresh:
            cached = self.cache.get_transcript(ticker)
            if cached is not None:
                if self.verbose:
                    print(f"    ✅ Using cached transcript for {ticker}")
                return cached

        # Fetch from API
        result = self._fetch_from_api(ticker)

        if result is None:
            return {'Ticker': ticker, 'Status': 'ERROR: Failed to fetch transcript'}

        # Save to cache (include full text for potential re-analysis)
        self.cache.save_transcript(ticker, result)

        return result

    def get_tickers_needing_refresh(self, tickers: List[str]) -> List[str]:
        """
        Determine which tickers need fresh transcript data.

        Args:
            tickers: List of all tickers to evaluate

        Returns:
            List of ticker symbols needing API refresh
        """
        needs_refresh = []

        for ticker in tickers:
            cached = self.cache.get_transcript(ticker)
            if cached is None:
                needs_refresh.append(ticker)

        if self.verbose and needs_refresh:
            print(f"   📝 {len(needs_refresh)} tickers without cached transcripts")

        return needs_refresh

    def calculate_days_since_earnings(self, earnings_date: str) -> Optional[int]:
        """
        Calculate days since earnings date.

        Args:
            earnings_date: Date string in YYYY-MM-DD format

        Returns:
            Number of days, or None if date is invalid
        """
        if not earnings_date or earnings_date == 'N/A':
            return None

        try:
            date = dt.datetime.strptime(earnings_date, '%Y-%m-%d').date()
            return (dt.date.today() - date).days
        except (ValueError, TypeError):
            return None

