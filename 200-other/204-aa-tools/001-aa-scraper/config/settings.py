"""
Central configuration for AA Points Monitor.
All thresholds, API config, and feature flags in one place.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class AlertThresholds:
    """Thresholds for triggering alerts."""

    # Stacked deals (Portal + SimplyMiles + CC)
    stack_immediate_alert: float = 15.0  # LP/$ - send email NOW
    stack_daily_digest: float = 10.0     # LP/$ - include in daily summary

    # Hotel deals
    hotel_immediate_alert: float = 25.0  # LP/$
    hotel_daily_digest: float = 15.0     # LP/$

    # Portal-only (no SimplyMiles match)
    portal_immediate_alert: float = 20.0  # LP/$ (rare, but possible during promos)
    portal_daily_digest: float = 10.0     # LP/$

    # Cooldown to prevent duplicate alerts
    alert_cooldown_hours: int = 24

    # Improvement threshold - re-alert if yield improves by this percentage
    improvement_threshold_pct: float = 20.0


@dataclass
class ScraperConfig:
    """Configuration for scrapers."""

    # Request delays (anti-detection)
    min_delay_seconds: float = 2.0
    max_delay_seconds: float = 5.0

    # Retry settings
    max_retries: int = 3
    retry_delay_seconds: float = 10.0

    # Staleness thresholds (hours)
    simplymiles_stale_hours: float = 6.0
    portal_stale_hours: float = 12.0
    hotels_stale_hours: float = 24.0

    # User agent for requests
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )


@dataclass
class MatchingConfig:
    """Configuration for merchant name matching."""

    # Fuzzy matching threshold (0-100)
    fuzzy_threshold: int = 85

    # Known merchant aliases (normalized name -> canonical name)
    aliases: dict = field(default_factory=lambda: {
        "kindle and kindle unlimited": "amazon kindle",
        "amazoncom": "amazon",
        "amazon com": "amazon",
        "walmartcom": "walmart",
        "walmart com": "walmart",
        "targetcom": "target",
        "target com": "target",
        "uber eats": "ubereats",
        "door dash": "doordash",
        "grub hub": "grubhub",
        "macys": "macy's",
        "nordstrom rack": "nordstromrack",
        "1800flowers": "1-800-flowers",
        "1 800 flowers": "1-800-flowers",
    })


@dataclass
class ScoringConfig:
    """Configuration for deal scoring."""

    # Credit card earning rate (LP per $)
    cc_earning_rate: float = 1.0

    # Low commitment bonuses (by min spend)
    bonus_under_50: float = 1.4   # Very low commitment
    bonus_under_100: float = 1.3
    bonus_under_200: float = 1.1
    penalty_over_500: float = 0.8  # High commitment penalty

    # Urgency bonus (expiring within 48 hours)
    urgency_bonus: float = 1.2

    # Austin local bonus (for hotels)
    austin_bonus: float = 1.15


@dataclass
class EmailConfig:
    """Email configuration via Resend."""

    api_key: str = field(default_factory=lambda: os.getenv("RESEND_API_KEY", ""))
    from_email: str = field(default_factory=lambda: os.getenv("ALERT_EMAIL_FROM", "alerts@example.com"))
    to_emails: List[str] = field(default_factory=lambda: [
        e.strip() for e in os.getenv("ALERT_EMAIL_TO", "").split(",") if e.strip()
    ])

    def __post_init__(self):
        if not self.to_emails:
            self.to_emails = ["user@example.com", "user@example.com"]


@dataclass
class HealthConfig:
    """Health monitoring configuration."""

    # Alert after this many consecutive failures
    failure_threshold: int = 3

    # Include health status in daily digest
    include_in_digest: bool = True


@dataclass
class Settings:
    """Main settings container."""

    # Sub-configs
    thresholds: AlertThresholds = field(default_factory=AlertThresholds)
    scraper: ScraperConfig = field(default_factory=ScraperConfig)
    matching: MatchingConfig = field(default_factory=MatchingConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    email: EmailConfig = field(default_factory=EmailConfig)
    health: HealthConfig = field(default_factory=HealthConfig)

    # Paths
    database_path: Path = field(default_factory=lambda: PROJECT_ROOT / os.getenv("DATABASE_PATH", "data/aa_monitor.db"))
    browser_data_path: Path = field(default_factory=lambda: PROJECT_ROOT / os.getenv("BROWSER_DATA_PATH", "browser_data"))
    logs_path: Path = field(default_factory=lambda: PROJECT_ROOT / "logs")

    # Supabase configuration
    supabase_url: str = field(default_factory=lambda: os.getenv("SUPABASE_URL", ""))
    supabase_key: str = field(default_factory=lambda: os.getenv("SUPABASE_KEY", ""))
    db_mode: str = field(default_factory=lambda: os.getenv("DB_MODE", "sqlite"))  # 'sqlite', 'supabase', or 'dual'

    # Alex's info
    current_lp: int = 40000  # Gold status
    target_lp: int = 75000   # Platinum status
    monthly_budget: float = 500.0

    # Timezone
    timezone: str = field(default_factory=lambda: os.getenv("TZ", "America/Chicago"))

    # Log level
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    def __post_init__(self):
        """Ensure directories exist."""
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.browser_data_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)

    @property
    def lp_gap(self) -> int:
        """Calculate LP gap to target."""
        return self.target_lp - self.current_lp


# Singleton instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

