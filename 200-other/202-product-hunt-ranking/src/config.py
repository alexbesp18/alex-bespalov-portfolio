from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    gdrive_api_key_json: str = ""
    gsheet_name: str = "Product Hunt Rankings"
    gsheet_id: str = ""
    gsheet_tab: str = "Weekly Top 10"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()
