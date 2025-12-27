"""
Supabase client for archiving daily indicator snapshots.

Archives computed technical indicators to Supabase for historical analysis,
backtesting, and pattern recognition.
"""

import logging
import math
import os
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


_sanitize_count = 0  # Track how many values were sanitized


def _sanitize_float(value: Any) -> Any:
    """
    Sanitize float values for JSON serialization.

    Replaces inf, -inf, and NaN with None since JSON doesn't support these.
    """
    global _sanitize_count
    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            _sanitize_count += 1
            return None
    return value


def _reset_sanitize_count() -> int:
    """Reset and return the sanitize count."""
    global _sanitize_count
    count = _sanitize_count
    _sanitize_count = 0
    return count


@dataclass
class IndicatorSnapshot:
    """A single day's indicator values for one ticker."""
    date: str
    symbol: str
    close: float
    # Momentum
    rsi: Optional[float] = None
    stoch_k: Optional[float] = None
    stoch_d: Optional[float] = None
    williams_r: Optional[float] = None
    roc: Optional[float] = None
    # Trend
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    adx: Optional[float] = None
    # Moving averages
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    # Volatility
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_position: Optional[float] = None
    atr: Optional[float] = None
    # Volume
    volume: Optional[int] = None
    volume_ratio: Optional[float] = None
    obv: Optional[int] = None
    # Scores
    bullish_score: Optional[float] = None
    reversal_score: Optional[float] = None
    oversold_score: Optional[float] = None
    action: Optional[str] = None
    # AI Analysis (from Grok)
    bullish_reason: Optional[str] = None
    tech_summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Supabase insert.

        Sanitizes float values to replace inf/nan with None for JSON compatibility.
        Only includes non-None values to avoid overwriting existing data on upsert.
        """
        result = {
            "date": self.date,
            "symbol": self.symbol,
        }

        # Only include fields that have values (not None)
        # This prevents overwriting existing data when another scanner upserts
        fields = [
            ("close", _sanitize_float(self.close)),
            ("rsi", _sanitize_float(self.rsi)),
            ("stoch_k", _sanitize_float(self.stoch_k)),
            ("stoch_d", _sanitize_float(self.stoch_d)),
            ("williams_r", _sanitize_float(self.williams_r)),
            ("roc", _sanitize_float(self.roc)),
            ("macd", _sanitize_float(self.macd)),
            ("macd_signal", _sanitize_float(self.macd_signal)),
            ("macd_hist", _sanitize_float(self.macd_hist)),
            ("adx", _sanitize_float(self.adx)),
            ("sma_20", _sanitize_float(self.sma_20)),
            ("sma_50", _sanitize_float(self.sma_50)),
            ("sma_200", _sanitize_float(self.sma_200)),
            ("bb_upper", _sanitize_float(self.bb_upper)),
            ("bb_lower", _sanitize_float(self.bb_lower)),
            ("bb_position", _sanitize_float(self.bb_position)),
            ("atr", _sanitize_float(self.atr)),
            ("volume", self.volume),
            ("volume_ratio", _sanitize_float(self.volume_ratio)),
            ("obv", self.obv),
            ("bullish_score", _sanitize_float(self.bullish_score)),
            ("reversal_score", _sanitize_float(self.reversal_score)),
            ("oversold_score", _sanitize_float(self.oversold_score)),
            ("action", self.action),
            ("bullish_reason", self.bullish_reason),
            ("tech_summary", self.tech_summary),
        ]

        for key, value in fields:
            if value is not None:
                result[key] = value

        return result


class SupabaseArchiver:
    """
    Archives daily indicator snapshots to Supabase.

    Uses the service_role key to bypass RLS for server-side operations.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None,
    ):
        """
        Initialize the Supabase archiver.

        Args:
            url: Supabase project URL (defaults to SUPABASE_URL env var)
            key: Supabase service role key (defaults to SUPABASE_SERVICE_KEY env var)
        """
        self.url = url or os.environ.get("SUPABASE_URL")
        self.key = key or os.environ.get("SUPABASE_SERVICE_KEY")
        self._client = None

        if not self.url or not self.key:
            logger.debug(
                "Supabase credentials not configured. "
                "Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables."
            )

    @property
    def client(self):
        """Lazy-load the Supabase client."""
        if self._client is None:
            if not self.url or not self.key:
                raise ValueError(
                    "Supabase credentials not configured. "
                    "Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables."
                )
            try:
                from supabase import create_client
                self._client = create_client(self.url, self.key)
            except ImportError:
                raise ImportError(
                    "supabase package not installed. Run: pip install supabase"
                )
        return self._client

    @property
    def is_configured(self) -> bool:
        """Check if Supabase credentials are available."""
        return bool(self.url and self.key)

    def archive_snapshots(
        self,
        snapshots: List[IndicatorSnapshot],
    ) -> int:
        """
        Archive indicator snapshots to Supabase.

        Uses upsert to handle re-runs on the same day.

        Args:
            snapshots: List of IndicatorSnapshot objects to archive

        Returns:
            Number of records upserted
        """
        if not snapshots:
            logger.debug("No snapshots to archive")
            return 0

        if not self.is_configured:
            logger.debug("Supabase not configured, skipping archive")
            return 0

        _reset_sanitize_count()  # Reset before converting
        records = [s.to_dict() for s in snapshots]
        sanitized = _reset_sanitize_count()
        if sanitized > 0:
            logger.info(f"DEBUG: Sanitized {sanitized} inf/nan values to None for JSON compatibility")

        try:
            # Upsert in batches of 500 to avoid payload limits
            batch_size = 500
            total_upserted = 0

            # Debug: Log sample record structure
            if records:
                sample = records[0]
                logger.info(f"DEBUG: Sample record keys: {list(sample.keys())}")
                logger.info(f"DEBUG: Sample record - symbol={sample.get('symbol')}, date={sample.get('date')}, close={sample.get('close')}")

            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                logger.info(f"DEBUG: Upserting batch {i // batch_size + 1} with {len(batch)} records to 'daily_indicators'")

                response = self.client.table("daily_indicators").upsert(
                    batch, on_conflict="date,symbol"
                ).execute()

                # Debug: Log response details
                logger.info(f"DEBUG: Upsert response - data count: {len(response.data) if response.data else 0}")
                if hasattr(response, 'count'):
                    logger.info(f"DEBUG: Response count attribute: {response.count}")

                total_upserted += len(batch)
                logger.info(f"Upserted batch {i // batch_size + 1}: {len(batch)} records")

            logger.info(f"Archived {total_upserted} indicator snapshots to Supabase")
            return total_upserted

        except Exception as e:
            logger.error(f"Failed to archive to Supabase: {e}")
            logger.error(f"DEBUG: Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"DEBUG: Full traceback:\n{traceback.format_exc()}")
            raise

    def get_history(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 365,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve historical indicator data for a symbol.

        Args:
            symbol: Ticker symbol
            start_date: Start date (YYYY-MM-DD), optional
            end_date: End date (YYYY-MM-DD), optional
            limit: Maximum records to return (default 365)

        Returns:
            List of indicator records
        """
        if not self.is_configured:
            logger.debug("Supabase not configured")
            return []

        try:
            query = (
                self.client
                .table("daily_indicators")
                .select("*")
                .eq("symbol", symbol)
                .order("date", desc=True)
                .limit(limit)
            )

            if start_date:
                query = query.gte("date", start_date)
            if end_date:
                query = query.lte("date", end_date)

            result = query.execute()
            return result.data

        except Exception as e:
            logger.error(f"Failed to fetch history from Supabase: {e}")
            return []

    def get_latest_scores(
        self,
        score_type: str = "bullish_score",
        min_score: float = 7.0,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get tickers with highest scores from the latest day.

        Args:
            score_type: Which score to filter by (bullish_score, reversal_score, oversold_score)
            min_score: Minimum score threshold
            limit: Maximum records to return

        Returns:
            List of ticker records with high scores
        """
        if not self.is_configured:
            return []

        try:
            # Get the latest date in the database
            latest = (
                self.client
                .table("daily_indicators")
                .select("date")
                .order("date", desc=True)
                .limit(1)
                .execute()
            )

            if not latest.data:
                return []

            latest_date = latest.data[0]["date"]

            # Get high-scoring tickers from that date
            result = (
                self.client
                .table("daily_indicators")
                .select("*")
                .eq("date", latest_date)
                .gte(score_type, min_score)
                .order(score_type, desc=True)
                .limit(limit)
                .execute()
            )

            return result.data

        except Exception as e:
            logger.error(f"Failed to fetch latest scores: {e}")
            return []

    def delete_date(self, target_date: str) -> int:
        """
        Delete all daily indicator records for a specific date.

        Useful for re-runs to ensure clean data (though upsert handles this too).

        Args:
            target_date: Date string in YYYY-MM-DD format

        Returns:
            Number of records deleted
        """
        if not self.is_configured:
            return 0

        try:
            result = (
                self.client
                .table("daily_indicators")
                .delete()
                .eq("date", target_date)
                .execute()
            )

            deleted = len(result.data) if result.data else 0
            logger.info(f"Deleted {deleted} daily records for {target_date}")
            return deleted

        except Exception as e:
            logger.error(f"Failed to delete data for {target_date}: {e}")
            return 0


# Module-level convenience functions

_archiver: Optional[SupabaseArchiver] = None


def _get_archiver() -> SupabaseArchiver:
    """Get or create the singleton archiver instance."""
    global _archiver
    if _archiver is None:
        _archiver = SupabaseArchiver()
    return _archiver


def archive_daily_indicators(
    results: List[Dict[str, Any]],
    scan_date: Optional[date] = None,
    score_type: str = "bullish",
) -> int:
    """
    Archive indicator data to Supabase.

    All scanners (008-alerts, 009-reversals, 010-oversold) pass a list of dicts
    with standardized field names. Each dict should contain:

    Required:
        - symbol: Ticker symbol (str)
        - close: Closing price (float)

    Optional indicators (pass whatever the scanner computes):
        - rsi, stoch_k, stoch_d, williams_r, roc
        - macd, macd_signal, macd_hist, adx
        - sma_20, sma_50, sma_200
        - bb_upper, bb_lower, bb_position, atr
        - volume, volume_ratio, obv

    Optional scores (one per scanner type):
        - bullish_score (008-alerts)
        - reversal_score or upside_rev_score (009-reversals)
        - oversold_score (010-oversold)

    Args:
        results: List of dicts with indicator data
        scan_date: Date of the scan (defaults to today)
        score_type: Type of scanner ("bullish", "reversal", "oversold")

    Returns:
        Number of records archived
    """
    if not results:
        logger.info("archive_daily_indicators: No results to archive")
        return 0

    archiver = _get_archiver()

    # Debug: Check env vars presence (not values)
    url_present = bool(os.environ.get("SUPABASE_URL"))
    key_present = bool(os.environ.get("SUPABASE_SERVICE_KEY"))
    logger.info(f"DEBUG: SUPABASE_URL present: {url_present}, SUPABASE_SERVICE_KEY present: {key_present}")
    logger.info(f"DEBUG: archiver.url set: {bool(archiver.url)}, archiver.key set: {bool(archiver.key)}")
    logger.info(f"archive_daily_indicators: archiver.is_configured={archiver.is_configured}")

    if not archiver.is_configured:
        logger.warning("Supabase not configured, skipping archive. Check SUPABASE_URL and SUPABASE_SERVICE_KEY env vars.")
        return 0

    date_str = (scan_date or date.today()).isoformat()
    logger.info(f"archive_daily_indicators: Processing {len(results)} results for date {date_str}")
    snapshots = []

    for r in results:
        if not isinstance(r, dict):
            logger.warning(f"Skipping non-dict result: {type(r)}")
            continue

        symbol = r.get('symbol', '')
        if not symbol:
            continue

        # Get close price (support legacy _price key)
        close = r.get('close') or r.get('_price', 0.0)

        # Get RSI (support legacy _rsi key)
        rsi = r.get('rsi') or r.get('_rsi')

        # Determine score based on score_type
        # Each scanner passes its own score field
        bullish_score = None
        reversal_score = None
        oversold_score = None

        if score_type == "bullish":
            bullish_score = r.get('bullish_score') or r.get('score')
        elif score_type == "reversal":
            # 009-reversals passes upside_rev_score for reversal score
            reversal_score = r.get('upside_rev_score') or r.get('reversal_score')
        elif score_type == "oversold":
            oversold_score = r.get('oversold_score') or r.get('score')

        snapshot = IndicatorSnapshot(
            date=date_str,
            symbol=symbol,
            close=close,
            # Momentum
            rsi=rsi,
            stoch_k=r.get('stoch_k'),
            stoch_d=r.get('stoch_d'),
            williams_r=r.get('williams_r'),
            roc=r.get('roc'),
            # Trend
            macd=r.get('macd'),
            macd_signal=r.get('macd_signal'),
            macd_hist=r.get('macd_hist'),
            adx=r.get('adx'),
            # Moving averages
            sma_20=r.get('sma_20'),
            sma_50=r.get('sma_50'),
            sma_200=r.get('sma_200'),
            # Volatility
            bb_upper=r.get('bb_upper'),
            bb_lower=r.get('bb_lower'),
            bb_position=r.get('bb_position'),
            atr=r.get('atr'),
            # Volume
            volume=r.get('volume'),
            volume_ratio=r.get('volume_ratio'),
            obv=r.get('obv'),
            # Scores
            bullish_score=bullish_score,
            reversal_score=reversal_score,
            oversold_score=oversold_score,
            action=r.get('action'),
            # AI Analysis
            bullish_reason=r.get('bullish_reason'),
            tech_summary=r.get('tech_summary'),
        )
        snapshots.append(snapshot)

    logger.info(f"archive_daily_indicators: Created {len(snapshots)} snapshots, calling archive_snapshots")
    return archiver.archive_snapshots(snapshots)


def get_historical_data(
    symbol: str,
    days: int = 90,
) -> List[Dict[str, Any]]:
    """
    Get historical indicator data for a symbol.

    Args:
        symbol: Ticker symbol
        days: Number of days of history to retrieve

    Returns:
        List of historical indicator records
    """
    archiver = _get_archiver()
    return archiver.get_history(symbol, limit=days)


def delete_daily_data(target_date: Optional[date] = None) -> int:
    """
    Delete all daily indicator records for a specific date.

    Useful for re-runs when you want to clear existing data first.
    Note: upsert already handles this, so this is optional.

    Args:
        target_date: Date to delete (defaults to today)

    Returns:
        Number of records deleted
    """
    archiver = _get_archiver()
    date_str = (target_date or date.today()).isoformat()
    return archiver.delete_date(date_str)
