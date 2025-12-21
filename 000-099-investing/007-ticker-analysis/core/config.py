"""
Configuration loader and validator for vFinal.
Loads settings from config.json and provides typed access.
"""

import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class GoogleSheetsConfig:
    credentials_file: str
    spreadsheet_name: str
    main_tab: str
    ticker_column: str
    start_row: int
    tech_data_tab: str
    transcripts_tab: str


@dataclass
class TwelveDataConfig:
    api_key: str
    output_size: int
    rate_limit_sleep: float


@dataclass
class GrokConfig:
    api_key: str
    model: str
    summarization_enabled: bool
    max_summary_tokens: int


@dataclass
class DefeatbetaConfig:
    quarters_to_fetch: int
    min_chars: int
    earliest_year_offset: int


@dataclass
class AppConfig:
    google_sheets: GoogleSheetsConfig
    twelve_data: TwelveDataConfig
    grok: GrokConfig
    defeatbeta: DefeatbetaConfig
    
    # Runtime settings (not from config file)
    verbose: bool = False
    dry_run: bool = False
    limit: int = 0
    batch_size: int = 0
    clean: bool = False
    force_refresh: bool = False


def load_config(config_path: str, **runtime_kwargs) -> AppConfig:
    """
    Load configuration from JSON file and validate.
    
    Args:
        config_path: Path to config.json file
        **runtime_kwargs: Runtime settings (verbose, dry_run, limit, etc.)
    
    Returns:
        AppConfig object with all settings
    
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If required fields are missing
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Validate required sections
    required_sections = ['google_sheets', 'twelve_data', 'grok']
    for section in required_sections:
        if section not in data:
            raise ValueError(f"Missing required config section: {section}")
    
    # Parse Google Sheets config
    gs = data['google_sheets']
    google_sheets = GoogleSheetsConfig(
        credentials_file=gs.get('credentials_file', 'google_service_account.json'),
        spreadsheet_name=gs['spreadsheet_name'],
        main_tab=gs.get('main_tab', 'Sheet1'),
        ticker_column=gs.get('ticker_column', 'A'),
        start_row=gs.get('start_row', 2),
        tech_data_tab=gs.get('tech_data_tab', 'Tech_Data'),
        transcripts_tab=gs.get('transcripts_tab', 'Transcripts'),
    )
    
    # Parse Twelve Data config
    td = data['twelve_data']
    twelve_data = TwelveDataConfig(
        api_key=td['api_key'],
        output_size=td.get('output_size', 365),
        rate_limit_sleep=td.get('rate_limit_sleep', 0.5),
    )
    
    # Parse Grok config
    gk = data['grok']
    grok = GrokConfig(
        api_key=gk['api_key'],
        model=gk.get('model', 'grok-4-1-fast-reasoning'),
        summarization_enabled=gk.get('summarization_enabled', True),
        max_summary_tokens=gk.get('max_summary_tokens', 2000),
    )
    
    # Parse defeatbeta config (optional)
    db = data.get('defeatbeta', {})
    defeatbeta = DefeatbetaConfig(
        quarters_to_fetch=db.get('quarters_to_fetch', 1),
        min_chars=db.get('min_chars', 600),
        earliest_year_offset=db.get('earliest_year_offset', 1),
    )
    
    # Build final config with runtime overrides
    return AppConfig(
        google_sheets=google_sheets,
        twelve_data=twelve_data,
        grok=grok,
        defeatbeta=defeatbeta,
        verbose=runtime_kwargs.get('verbose', False),
        dry_run=runtime_kwargs.get('dry_run', False),
        limit=runtime_kwargs.get('limit', 0),
        batch_size=runtime_kwargs.get('batch_size', 0),
        clean=runtime_kwargs.get('clean', False),
        force_refresh=runtime_kwargs.get('force_refresh', False),
    )


def get_config_template() -> str:
    """Return a template config.json for reference."""
    return """{
  "google_sheets": {
    "credentials_file": "google_service_account.json",
    "spreadsheet_name": "Your Spreadsheet Name",
    "main_tab": "Sheet1",
    "ticker_column": "A",
    "start_row": 2,
    "tech_data_tab": "Tech_Data",
    "transcripts_tab": "Transcripts"
  },
  "twelve_data": {
    "api_key": "YOUR_TWELVE_DATA_API_KEY",
    "output_size": 365,
    "rate_limit_sleep": 0.5
  },
  "grok": {
    "api_key": "YOUR_GROK_API_KEY",
    "model": "grok-4-1-fast-reasoning",
    "summarization_enabled": true,
    "max_summary_tokens": 2000
  },
  "defeatbeta": {
    "quarters_to_fetch": 1,
    "min_chars": 600,
    "earliest_year_offset": 1
  }
}"""

