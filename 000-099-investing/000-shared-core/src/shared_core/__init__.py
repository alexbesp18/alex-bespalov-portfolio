"""
Shared core utilities for 000-099-investing projects.

Provides unified access to:
- LLM clients (multi-provider)
- Market data (Twelve Data, transcripts, technical indicators)
- Data caching (date-based JSON)
- Integrations (Google Sheets)

All imports are lazy to allow using subsets of functionality
when not all dependencies are installed.
"""

__all__ = [
    'LLMClient',
    'TechnicalCalculator',
    'TwelveDataClient',
    'TranscriptClient',
    'CacheAwareFetcher',
    'DataCache',
    'SheetManager',
]


def __getattr__(name):
    """Lazy import to avoid requiring all dependencies upfront."""
    if name == 'LLMClient':
        from .llm.client import LLMClient
        return LLMClient
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
    elif name == 'DataCache':
        from .cache.data_cache import DataCache
        return DataCache
    elif name == 'SheetManager':
        from .integrations.sheets import SheetManager
        return SheetManager
    raise AttributeError(f"module 'shared_core' has no attribute '{name}'")
