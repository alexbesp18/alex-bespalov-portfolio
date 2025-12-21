from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Product Hunt specific secrets use PH_ prefix to avoid conflicts
    with other projects using Google Sheets.
    """
    gdrive_api_key_json: str = Field(
        default="",
        validation_alias="PH_GDRIVE_API_KEY_JSON"
    )
    gsheet_id: str = Field(
        default="",
        validation_alias="PH_GSHEET_ID"
    )
    gsheet_name: str = "Product Hunt Rankings"
    gsheet_tab: str = "Weekly Top 10"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()
