"""Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    xai_api_key: str
    tavily_api_key: str
    model_name: str = "grok-4-1-fast-reasoning-latest"


# Singleton instance
settings = Settings()


if __name__ == "__main__":
    # Test that settings load correctly
    print("Settings loaded successfully!")
    print(f"XAI API Key: {settings.xai_api_key[:10]}...{settings.xai_api_key[-4:]}")
    print(f"Tavily API Key: {settings.tavily_api_key[:10]}...{settings.tavily_api_key[-4:]}")
    print(f"Model Name: {settings.model_name}")

