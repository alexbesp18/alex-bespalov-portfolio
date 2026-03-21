"""
Application settings using Pydantic.

Loads configuration from environment variables with sensible defaults.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Scraper settings (optimized for maximum coverage)
    max_concurrent_cities: int = 40  # Doubled again for 3x daily runs
    days_ahead: int = 60  # Extended from 30
    min_delay: float = 0.1  # Aggressive - no rate limit issues observed
    max_delay: float = 0.3  # Aggressive - no rate limit issues observed
    max_retries: int = 3
    retry_delay: float = 2.0
    request_timeout: float = 30.0

    # Deal retention mode: 'all' or 'best'
    # 'all' = keep all deals (duplicates allowed, shows price history)
    # 'best' = keep only best yield per (hotel, check_in, check_out)
    deal_retention_mode: str = "best"

    # BUG 7 FIX: Validate retention mode to catch typos early
    @field_validator('deal_retention_mode')
    @classmethod
    def validate_retention_mode(cls, v: str) -> str:
        """Validate deal retention mode is 'all' or 'best'."""
        valid_modes = ('all', 'best')
        if v not in valid_modes:
            raise ValueError(f"deal_retention_mode must be 'all' or 'best', got '{v}'")
        return v

    # Database
    database_path: str = "data/hotels.db"
    db_mode: str = "sqlite"  # 'sqlite' or 'supabase'
    supabase_url: str = ""
    supabase_key: str = ""

    # Web dashboard
    web_host: str = "127.0.0.1"
    web_port: int = 8000

    # Logging
    log_level: str = "INFO"

    # Star rating multipliers for quality-adjusted scoring
    star_multiplier_5: float = 1.25  # 5-star gets 25% boost
    star_multiplier_4: float = 1.15  # 4-star gets 15% boost
    star_multiplier_3: float = 1.00  # 3-star neutral
    star_multiplier_2: float = 0.85  # 2-star needs 15% better yield
    star_multiplier_1: float = 0.70  # 1-star needs 30% better yield

    # Exceptional yield thresholds by star rating
    exceptional_5star: float = 20.0
    exceptional_4star: float = 22.0
    exceptional_3star: float = 28.0
    exceptional_2star: float = 40.0
    exceptional_1star: float = 50.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def db_path(self) -> Path:
        """Get database path as Path object."""
        return Path(self.database_path)

    def get_star_multiplier(self, stars: int) -> float:
        """Get the score multiplier for a star rating."""
        multipliers = {
            5: self.star_multiplier_5,
            4: self.star_multiplier_4,
            3: self.star_multiplier_3,
            2: self.star_multiplier_2,
            1: self.star_multiplier_1,
            0: 0.60,  # Unknown/unrated
        }
        return multipliers.get(stars, 0.60)

    def get_exceptional_threshold(self, stars: int) -> float:
        """Get the exceptional yield threshold for a star rating."""
        thresholds = {
            5: self.exceptional_5star,
            4: self.exceptional_4star,
            3: self.exceptional_3star,
            2: self.exceptional_2star,
            1: self.exceptional_1star,
            0: self.exceptional_1star,  # Unknown needs to be exceptional
        }
        return thresholds.get(stars, self.exceptional_1star)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
