from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment variables:
    - SUPABASE_URL: Supabase project URL
    - SUPABASE_SERVICE_KEY: Supabase service role key
    - GROK_API_KEY: Grok API key for AI analysis
    """
    # Supabase (unified across all projects)
    supabase_url: str = Field(
        default="",
        validation_alias="SUPABASE_URL"
    )
    supabase_key: str = Field(
        default="",
        validation_alias="SUPABASE_SERVICE_KEY"
    )

    # Grok AI
    xai_api_key: str = Field(
        default="",
        validation_alias="GROK_API_KEY"
    )
    grok_model: str = "grok-4-1-fast-reasoning"

    # General
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore old Google Sheets env vars during migration
    )


settings = Settings()
