"""
008-ticker-analysis Core Module
===============================

Uses shared_core for common utilities:
- DataCache (data caching)
- TechnicalCalculator (technical indicators)
- TwelveDataClient (Twelve Data API)
- TranscriptClient (earnings transcripts)
- SheetManager (Google Sheets I/O)

Project-specific modules:
- AppConfig, load_config (configuration)
- GrokAnalyzer (Grok AI analysis)
"""

# Re-export from shared_core
from shared_core import (
    DataCache,
    TechnicalCalculator,
    TwelveDataClient,
    TranscriptClient,
    SheetManager,
)

# Project-specific modules
from .config import AppConfig, load_config, get_config_template
from .grok_analyzer import GrokAnalyzer

__all__ = [
    # From shared_core
    'DataCache',
    'TechnicalCalculator',
    'TwelveDataClient',
    'TranscriptClient',
    'SheetManager',
    # Project-specific
    'AppConfig',
    'load_config',
    'get_config_template',
    'GrokAnalyzer',
]

__version__ = '2.0.0'
