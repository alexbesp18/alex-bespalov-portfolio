"""Configuration. Tickers come from Supabase watchlist, not config."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    supabase_url: str = ""
    supabase_service_key: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    fetch_delay_seconds: float = 2.0

    @property
    def has_supabase(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_key)

    @property
    def has_telegram(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)


def get_settings() -> Settings:
    return Settings()
