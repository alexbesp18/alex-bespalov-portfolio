"""
Date-based caching layer for API responses.
Stores Twelve Data time series and transcript data as JSON files.
Each file is stamped with the fetch date to enable daily refresh logic.
"""

import json
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd


class DataCache:
    """
    Manages local JSON cache for API data.
    
    Cache structure:
        data/
        ├── twelve_data/
        │   └── AAPL_2025-12-19.json
        └── transcripts/
            └── AAPL_2025-12-19.json
    """

    def __init__(self, cache_dir: Path, verbose: bool = False):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Root directory for cache (e.g., project/data/)
            verbose: Print cache operations
        """
        self.cache_dir = Path(cache_dir)
        self.verbose = verbose
        self.today = datetime.date.today().isoformat()

        # Ensure directories exist
        self.twelve_data_dir = self.cache_dir / "twelve_data"
        self.transcripts_dir = self.cache_dir / "transcripts"
        self.twelve_data_dir.mkdir(parents=True, exist_ok=True)
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)

    def _get_twelve_data_path(self, ticker: str, date: Optional[str] = None) -> Path:
        """Get path for a ticker's time series cache file."""
        date = date or self.today
        return self.twelve_data_dir / f"{ticker.upper()}_{date}.json"

    def _get_transcript_path(self, ticker: str, date: Optional[str] = None) -> Path:
        """Get path for a ticker's transcript cache file."""
        date = date or self.today
        return self.transcripts_dir / f"{ticker.upper()}_{date}.json"

    # =========================================================================
    # TWELVE DATA CACHE
    # =========================================================================

    def get_twelve_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """
        Get cached time series data for today.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            DataFrame with OHLCV data if cached today, else None
        """
        path = self._get_twelve_data_path(ticker)

        if not path.exists():
            if self.verbose:
                print(f"    📁 Cache miss: {ticker} (no file)")
            return None

        try:
            df = pd.read_json(path)
            if self.verbose:
                print(f"    📁 Cache hit: {ticker} ({len(df)} bars)")
            return df
        except Exception as e:
            if self.verbose:
                print(f"    📁 Cache error: {ticker} ({e})")
            return None

    def save_twelve_data(self, ticker: str, df: pd.DataFrame) -> None:
        """
        Save time series data to cache with today's date.
        
        Args:
            ticker: Stock ticker symbol
            df: DataFrame with OHLCV data
        """
        path = self._get_twelve_data_path(ticker)

        try:
            df.to_json(path, date_format='iso')
            if self.verbose:
                print(f"    💾 Cached: {ticker} ({len(df)} bars)")
        except Exception as e:
            if self.verbose:
                print(f"    ⚠️  Cache save failed: {ticker} ({e})")

    # =========================================================================
    # TRANSCRIPT CACHE
    # =========================================================================

    def get_transcript(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get cached transcript data for today.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict with transcript metadata and text if cached, else None
        """
        path = self._get_transcript_path(ticker)

        if not path.exists():
            if self.verbose:
                print(f"    📁 Transcript cache miss: {ticker}")
            return None

        try:
            with open(path, 'r') as f:
                data = json.load(f)
            if self.verbose:
                print(f"    📁 Transcript cache hit: {ticker} ({data.get('Period', 'N/A')})")
            return data
        except Exception as e:
            if self.verbose:
                print(f"    📁 Transcript cache error: {ticker} ({e})")
            return None

    def save_transcript(self, ticker: str, data: Dict[str, Any]) -> None:
        """
        Save transcript data to cache.
        
        Args:
            ticker: Stock ticker symbol
            data: Dict with transcript metadata and text
        """
        path = self._get_transcript_path(ticker)

        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            if self.verbose:
                print(f"    💾 Transcript cached: {ticker}")
        except Exception as e:
            if self.verbose:
                print(f"    ⚠️  Transcript cache save failed: {ticker} ({e})")

    # =========================================================================
    # CACHE MANAGEMENT
    # =========================================================================

    def list_cached_tickers(self, data_type: str = 'twelve_data') -> List[str]:
        """
        List all tickers with cache files for today.
        
        Args:
            data_type: 'twelve_data' or 'transcripts'
            
        Returns:
            List of ticker symbols
        """
        if data_type == 'twelve_data':
            directory = self.twelve_data_dir
        else:
            directory = self.transcripts_dir

        suffix = f"_{self.today}.json"
        tickers = []

        for path in directory.glob(f"*{suffix}"):
            ticker = path.stem.replace(f"_{self.today}", "")
            tickers.append(ticker)

        return sorted(tickers)

    def clear_old_cache(self, days: int = 7) -> int:
        """
        Remove cache files older than N days.
        
        Args:
            days: Delete files older than this many days
            
        Returns:
            Number of files deleted
        """
        cutoff = datetime.date.today() - datetime.timedelta(days=days)
        deleted = 0

        for directory in [self.twelve_data_dir, self.transcripts_dir]:
            for path in directory.glob("*.json"):
                try:
                    # Extract date from filename (TICKER_YYYY-MM-DD.json)
                    date_str = path.stem.split('_')[-1]
                    file_date = datetime.date.fromisoformat(date_str)

                    if file_date < cutoff:
                        path.unlink()
                        deleted += 1
                        if self.verbose:
                            print(f"    🗑️  Deleted old cache: {path.name}")
                except (ValueError, IndexError):
                    # Skip files that don't match expected format
                    continue

        return deleted

    def clear_all_cache(self) -> int:
        """
        Remove all cache files.
        
        Returns:
            Number of files deleted
        """
        deleted = 0

        for directory in [self.twelve_data_dir, self.transcripts_dir]:
            for path in directory.glob("*.json"):
                path.unlink()
                deleted += 1

        if self.verbose:
            print(f"    🗑️  Cleared {deleted} cache files")

        return deleted

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dict with cache statistics
        """
        twelve_data_files = list(self.twelve_data_dir.glob("*.json"))
        transcript_files = list(self.transcripts_dir.glob("*.json"))

        today_twelve = len([f for f in twelve_data_files if self.today in f.name])
        today_transcripts = len([f for f in transcript_files if self.today in f.name])

        total_size = sum(f.stat().st_size for f in twelve_data_files + transcript_files)

        return {
            'twelve_data_total': len(twelve_data_files),
            'twelve_data_today': today_twelve,
            'transcripts_total': len(transcript_files),
            'transcripts_today': today_transcripts,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'cache_date': self.today,
        }

