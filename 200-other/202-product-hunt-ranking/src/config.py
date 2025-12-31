from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment variables:
    - SUPABASE_URL: Supabase project URL
    - SUPABASE_SERVICE_KEY: Supabase service role key
    - GROK_API_KEY: Grok API key for AI analysis
    - RESEND_API_KEY: Resend API key for email notifications
    - EMAIL_FROM: Sender email address
    - EMAIL_TO: Comma-separated recipient emails
    """

    # Supabase (unified across all projects)
    supabase_url: str = Field(default="", validation_alias="SUPABASE_URL")
    supabase_key: str = Field(default="", validation_alias="SUPABASE_SERVICE_KEY")

    # Grok AI
    xai_api_key: str = Field(default="", validation_alias="GROK_API_KEY")
    grok_model: str = "grok-4-1-fast-reasoning"

    # Email notifications
    resend_api_key: str = Field(default="", validation_alias="RESEND_API_KEY")
    email_from: str = Field(
        default="digest@producthunt-tracker.com", validation_alias="EMAIL_FROM"
    )
    email_to: str = Field(default="", validation_alias="EMAIL_TO")

    # General
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore old Google Sheets env vars during migration
    )


settings = Settings()
