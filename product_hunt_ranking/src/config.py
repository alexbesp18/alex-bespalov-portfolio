import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    gdrive_api_key_json: str = "" # Optional if not using gsheet, but required for original logic
    gsheet_name: str = "Product Hunt Rankings"
    gsheet_tab: str = "Weekly Top 10"
    
    # Logger
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
