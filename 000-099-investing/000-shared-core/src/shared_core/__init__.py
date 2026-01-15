"""
Shared core utilities for 000-099-investing projects.

Provides unified access to:
- LLM clients (multi-provider)
- Market data (Twelve Data, transcripts, technical indicators)
- Data caching (date-based JSON)
- Integrations (Google Sheets)
- State management (deduplication, archiving)
- Scoring engines (reversal, oversold, component scorers)
- Trigger evaluation (signal detection)
- Notifications (email via Resend)
- Models (shared data structures)

All imports are lazy to allow using subsets of functionality
when not all dependencies are installed.
"""

__all__ = [
    # LLM
    'LLMClient',
    # Market Data
    'TechnicalCalculator',
    'TwelveDataClient',
    'TranscriptClient',
    'CacheAwareFetcher',
    # Cache
    'DataCache',
    # Integrations
    'SheetManager',
    # State Management
    'StateManager',
    'ArchiveManager',
    'Digest',
    'ArchiveEntry',
    # State Utils
    'safe_read_json',
    'safe_write_json',
    'utc_now_iso',
    'parse_iso_datetime',
    # General Utils
    'get_cached_tickers',
    'get_latest_cached_tickers',
    'check_time_guard',
    'setup_logging',
    # Scoring
    'DivergenceType',
    'DivergenceResult',
    'ReversalScore',
    'OversoldScore',
    'BullishScore',
    # Data Processing
    'process_ohlcv_data',
    'add_standard_indicators',
    'calculate_matrix',
    'calculate_bullish_score',
    # Triggers
    'TriggerEngine',
    'TriggerResult',
    'check_conditions',
    'evaluate_ticker',
    'PORTFOLIO_SIGNALS',
    'WATCHLIST_SIGNALS',
    'ALL_SIGNALS',
    # Notifications
    'ResendEmailClient',
    'format_html_table',
    'format_subject',
    # Models
    'TickerResult',
    'ScanResult',
    'Watchlist',
    'ScanConfig',
    'OutputFormat',
    # Validators
    'ValidationError',
    'validate_ticker',
    'validate_tickers',
    'validate_date',
    'validate_api_key',
    'validate_positive_number',
    'validate_range',
    # Archive
    'SupabaseArchiver',
    'archive_daily_indicators',
    'get_historical_data',
    'MonthlyAggregator',
    'run_monthly_aggregation',
]


def __getattr__(name):
    """Lazy import to avoid requiring all dependencies upfront."""
    # LLM
    if name == 'LLMClient':
        from .llm.client import LLMClient
        return LLMClient
    # Market Data
    elif name == 'TechnicalCalculator':
        from .market_data.technical import TechnicalCalculator
        return TechnicalCalculator
    elif name == 'TwelveDataClient':
        from .market_data.twelve_data import TwelveDataClient
        return TwelveDataClient
    elif name == 'TranscriptClient':
        from .market_data.transcript import TranscriptClient
        return TranscriptClient
    elif name == 'CacheAwareFetcher':
        from .market_data.cached_fetcher import CacheAwareFetcher
        return CacheAwareFetcher
    # Cache
    elif name == 'DataCache':
        from .cache.data_cache import DataCache
        return DataCache
    # Integrations
    elif name == 'SheetManager':
        from .integrations.sheets import SheetManager
        return SheetManager
    # State Management
    elif name == 'StateManager':
        from .state.manager import StateManager
        return StateManager
    elif name == 'ArchiveManager':
        from .state.archiver import ArchiveManager
        return ArchiveManager
    elif name == 'Digest':
        from .state.digest import Digest
        return Digest
    elif name == 'ArchiveEntry':
        from .state.archiver import ArchiveEntry
        return ArchiveEntry
    # State Utils
    elif name == 'safe_read_json':
        from .state.utils import safe_read_json
        return safe_read_json
    elif name == 'safe_write_json':
        from .state.utils import safe_write_json
        return safe_write_json
    elif name == 'utc_now_iso':
        from .state.utils import utc_now_iso
        return utc_now_iso
    elif name == 'parse_iso_datetime':
        from .state.utils import parse_iso_datetime
        return parse_iso_datetime
    # General Utils
    elif name == 'get_cached_tickers':
        from .utils.cache_tickers import get_cached_tickers
        return get_cached_tickers
    elif name == 'get_latest_cached_tickers':
        from .utils.cache_tickers import get_latest_cached_tickers
        return get_latest_cached_tickers
    elif name == 'check_time_guard':
        from .utils.time_guard import check_time_guard
        return check_time_guard
    elif name == 'setup_logging':
        from .utils.logging_setup import setup_logging
        return setup_logging
    # Scoring
    elif name == 'DivergenceType':
        from .scoring.models import DivergenceType
        return DivergenceType
    elif name == 'DivergenceResult':
        from .scoring.models import DivergenceResult
        return DivergenceResult
    elif name == 'ReversalScore':
        from .scoring.models import ReversalScore
        return ReversalScore
    elif name == 'OversoldScore':
        from .scoring.models import OversoldScore
        return OversoldScore
    elif name == 'BullishScore':
        from .scoring.models import BullishScore
        return BullishScore
    # Data Processing
    elif name == 'process_ohlcv_data':
        from .data.process_ohlcv import process_ohlcv_data
        return process_ohlcv_data
    elif name == 'add_standard_indicators':
        from .data.process_ohlcv import add_standard_indicators
        return add_standard_indicators
    elif name == 'calculate_matrix':
        from .data.flags_matrix import calculate_matrix
        return calculate_matrix
    elif name == 'calculate_bullish_score':
        from .data.bullish_score import calculate_bullish_score
        return calculate_bullish_score
    # Triggers
    elif name == 'TriggerEngine':
        from .triggers.engine import TriggerEngine
        return TriggerEngine
    elif name == 'TriggerResult':
        from .triggers.evaluation import TriggerResult
        return TriggerResult
    elif name == 'check_conditions':
        from .triggers.conditions import check_conditions
        return check_conditions
    elif name == 'evaluate_ticker':
        from .triggers.evaluation import evaluate_ticker
        return evaluate_ticker
    elif name == 'PORTFOLIO_SIGNALS':
        from .triggers.definitions import PORTFOLIO_SIGNALS
        return PORTFOLIO_SIGNALS
    elif name == 'WATCHLIST_SIGNALS':
        from .triggers.definitions import WATCHLIST_SIGNALS
        return WATCHLIST_SIGNALS
    elif name == 'ALL_SIGNALS':
        from .triggers.definitions import ALL_SIGNALS
        return ALL_SIGNALS
    # Notifications
    elif name == 'ResendEmailClient':
        from .notifications.resend_client import ResendEmailClient
        return ResendEmailClient
    elif name == 'format_html_table':
        from .notifications.formatters import format_html_table
        return format_html_table
    elif name == 'format_subject':
        from .notifications.formatters import format_subject
        return format_subject
    # Models
    elif name == 'TickerResult':
        from .models.results import TickerResult
        return TickerResult
    elif name == 'ScanResult':
        from .models.results import ScanResult
        return ScanResult
    elif name == 'Watchlist':
        from .models.watchlist import Watchlist
        return Watchlist
    elif name == 'ScanConfig':
        from .models.config import ScanConfig
        return ScanConfig
    elif name == 'OutputFormat':
        from .models.config import OutputFormat
        return OutputFormat
    # Validators
    elif name == 'ValidationError':
        from .validators import ValidationError
        return ValidationError
    elif name == 'validate_ticker':
        from .validators import validate_ticker
        return validate_ticker
    elif name == 'validate_tickers':
        from .validators import validate_tickers
        return validate_tickers
    elif name == 'validate_date':
        from .validators import validate_date
        return validate_date
    elif name == 'validate_api_key':
        from .validators import validate_api_key
        return validate_api_key
    elif name == 'validate_positive_number':
        from .validators import validate_positive_number
        return validate_positive_number
    elif name == 'validate_range':
        from .validators import validate_range
        return validate_range
    # Archive
    elif name == 'SupabaseArchiver':
        from .archive.supabase_client import SupabaseArchiver
        return SupabaseArchiver
    elif name == 'archive_daily_indicators':
        from .archive.supabase_client import archive_daily_indicators
        return archive_daily_indicators
    elif name == 'get_historical_data':
        from .archive.supabase_client import get_historical_data
        return get_historical_data
    elif name == 'MonthlyAggregator':
        from .archive.aggregator import MonthlyAggregator
        return MonthlyAggregator
    elif name == 'run_monthly_aggregation':
        from .archive.aggregator import run_monthly_aggregation
        return run_monthly_aggregation
    raise AttributeError(f"module 'shared_core' has no attribute '{name}'")
