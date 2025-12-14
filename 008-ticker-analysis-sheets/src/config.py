from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    """
    Application configuration via environment variables.
    """
    # API Keys
    twelve_data_api_key: str = Field(..., alias="TWELVE_DATA_API_KEY")
    grok_api_key: str = Field(..., alias="GROK_API_KEY")
    
    # Google Sheets
    google_service_account_path: str = Field("google_service_account.json", alias="GOOGLE_SERVICE_ACCOUNT_PATH")
    google_sheet_name: str = Field(..., alias="GOOGLE_SHEET_NAME")
    
    # Logic Configuration
    llm_model: str = Field("grok-4-1-fast-reasoning", alias="MODEL_NAME")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
try:
    settings = Settings()
except Exception:
    # Allow import without env vars (e.g. for testing or docker build)
    # The actual validation will happen when accessing attributes or verifying setup
    settings = None

def get_settings() -> Settings:
    """Get settings or raise error if credentials missing."""
    if settings is None:
        return Settings()
    return settings
