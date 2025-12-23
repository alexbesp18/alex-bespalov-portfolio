"""
Configuration Management

Centralized configuration using pydantic-settings.
All hardcoded values should be defined here for easy customization.

Usage:
    from src.config import settings
    
    transcript = result.full_text[:settings.max_transcript_length]
    chunks = segmenter.segment_by_words(text, words_per_chunk=settings.words_per_chunk)
"""

import os
from pathlib import Path
from typing import Optional, List
from functools import lru_cache

try:
    from pydantic_settings import BaseSettings
    from pydantic import Field
except ImportError:
    # Fallback for environments without pydantic-settings
    from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables.
    
    All settings can be overridden via environment variables or .env file.
    Environment variable names are uppercase versions of the field names.
    """
    
    # ==========================================================================
    # API Keys
    # ==========================================================================
    openrouter_api_key: Optional[str] = Field(
        default=None,
        description="OpenRouter API key for LLM access",
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key (optional, if using OpenAI directly)",
    )
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key (optional, if using Anthropic directly)",
    )
    
    # ==========================================================================
    # Supabase
    # ==========================================================================
    supabase_url: Optional[str] = Field(
        default=None,
        description="Supabase project URL",
    )
    supabase_key: Optional[str] = Field(
        default=None,
        description="Supabase service role key",
    )
    
    # ==========================================================================
    # Processing Limits
    # ==========================================================================
    max_transcript_length: int = Field(
        default=10000,
        description="Maximum characters of transcript to send to LLM",
    )
    words_per_chunk: int = Field(
        default=500,
        description="Words per chunk when segmenting transcript",
    )
    max_chunks: Optional[int] = Field(
        default=None,
        description="Maximum chunks to process (None = all)",
    )
    max_opportunities: int = Field(
        default=5,
        description="Maximum automation opportunities to process",
    )
    max_ideas: int = Field(
        default=5,
        description="Maximum business ideas to generate",
    )
    
    # ==========================================================================
    # Cost Controls
    # ==========================================================================
    max_cost_per_video: float = Field(
        default=1.0,
        description="Maximum LLM cost per video in USD",
    )
    daily_budget_usd: float = Field(
        default=10.0,
        description="Daily budget limit in USD",
    )
    cost_alert_threshold: float = Field(
        default=0.75,
        description="Alert when daily budget reaches this percentage (0.0-1.0)",
    )
    
    # ==========================================================================
    # LLM Settings
    # ==========================================================================
    default_provider: str = Field(
        default="openrouter",
        description="Default LLM provider (openrouter, openai, anthropic)",
    )
    default_model: str = Field(
        default="x-ai/grok-4.1-fast",
        description="Default model to use",
    )
    default_temperature: float = Field(
        default=0.7,
        description="Default temperature for LLM calls",
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for LLM calls",
    )
    retry_delay: float = Field(
        default=2.0,
        description="Initial retry delay in seconds",
    )
    
    # ==========================================================================
    # Paths
    # ==========================================================================
    output_dir: Path = Field(
        default=Path("data/outputs"),
        description="Directory for output files",
    )
    prompts_dir: Path = Field(
        default=Path("prompts"),
        description="Directory for prompt templates",
    )
    queue_file: Path = Field(
        default=Path("queue.yaml"),
        description="Path to video processing queue",
    )
    
    # ==========================================================================
    # Notifications
    # ==========================================================================
    slack_webhook_url: Optional[str] = Field(
        default=None,
        description="Slack webhook URL for notifications",
    )
    discord_webhook_url: Optional[str] = Field(
        default=None,
        description="Discord webhook URL for notifications",
    )
    notification_email: Optional[str] = Field(
        default=None,
        description="Email address for notifications",
    )
    sendgrid_api_key: Optional[str] = Field(
        default=None,
        description="SendGrid API key for email notifications",
    )
    
    # ==========================================================================
    # Feature Flags
    # ==========================================================================
    enable_parallel_enrichment: bool = Field(
        default=True,
        description="Enable parallel execution for enrichment pipelines",
    )
    enable_cost_tracking: bool = Field(
        default=True,
        description="Track and log LLM costs",
    )
    enable_budget_enforcement: bool = Field(
        default=False,
        description="Enforce daily budget limits (stop processing if exceeded)",
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
    
    def has_openrouter(self) -> bool:
        """Check if OpenRouter is configured."""
        return bool(self.openrouter_api_key)
    
    def has_supabase(self) -> bool:
        """Check if Supabase is configured."""
        return bool(self.supabase_url and self.supabase_key)
    
    def has_notifications(self) -> bool:
        """Check if any notification channel is configured."""
        return bool(
            self.slack_webhook_url or
            self.discord_webhook_url or
            self.notification_email
        )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.
    
    Returns:
        Settings instance (cached after first call).
    """
    return Settings()


# Convenience alias
settings = get_settings()

