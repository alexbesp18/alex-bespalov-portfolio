"""Configuration management using pydantic-settings."""

from pathlib import Path
from typing import Any, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys (optional for testing, validated at runtime)
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    openai_api_key: str = Field(default="", description="OpenAI API key")
    xai_api_key: str = Field(default="", description="xAI (Grok) API key")
    google_api_key: str = Field(default="", description="Google (Gemini) API key")
    
    # Model Configuration
    default_provider: Literal["claude", "openai", "grok", "gemini"] = Field(
        default="claude",
        description="Default LLM provider"
    )
    default_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Default model name"
    )
    default_max_tokens: int = Field(
        default=64000,
        description="Default max tokens"
    )
    default_temperature: float = Field(
        default=0.7,
        description="Default temperature"
    )
    
    # Claude-specific settings
    claude_enabled: bool = Field(default=True, description="Enable Claude provider")
    claude_model: str = Field(default="sonnet-4.5", description="Claude model key")
    claude_use_extended_thinking: bool = Field(
        default=True,
        description="Use extended thinking for Claude"
    )
    claude_thinking_budget_tokens: int = Field(
        default=32000,
        description="Claude thinking budget tokens"
    )
    claude_max_tokens: int = Field(default=64000, description="Claude max tokens")
    
    # OpenAI-specific settings
    openai_enabled: bool = Field(default=True, description="Enable OpenAI provider")
    openai_model: str = Field(default="gpt-4", description="OpenAI model key")
    openai_reasoning_effort: Literal["low", "medium", "high"] = Field(
        default="high",
        description="OpenAI reasoning effort"
    )
    openai_max_tokens: int = Field(default=128000, description="OpenAI max tokens")
    openai_web_search_enabled: bool = Field(
        default=False,
        description="Enable web search for OpenAI"
    )
    
    # Grok-specific settings
    grok_enabled: bool = Field(default=True, description="Enable Grok provider")
    grok_model: str = Field(default="grok-4", description="Grok model key")
    grok_max_tokens: int = Field(default=128000, description="Grok max tokens")
    
    # Gemini-specific settings
    gemini_enabled: bool = Field(default=True, description="Enable Gemini provider")
    gemini_model: str = Field(default="gemini-2.5-pro", description="Gemini model key")
    gemini_max_tokens: int = Field(default=65000, description="Gemini max tokens")
    gemini_temperature: float = Field(default=0.7, description="Gemini temperature")
    gemini_web_search_enabled: bool = Field(
        default=False,
        description="Enable web search for Gemini"
    )
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Path | None = Field(default=None, description="Optional log file path")
    
    # Paths
    input_folder: Path = Field(default=Path("input"), description="Input folder path")
    output_folder: Path = Field(default=Path("output"), description="Output folder path")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_ignore_empty=True,  # Allow empty values for testing
    )
    
    def validate_api_keys(self) -> None:
        """Validate that at least one API key is set.
        
        Raises:
            ValueError: If no API keys are configured
        """
        if not any([
            self.anthropic_api_key,
            self.openai_api_key,
            self.xai_api_key,
            self.google_api_key,
        ]):
            raise ValueError(
                "No API keys configured. Please set at least one API key in .env file. "
                "See .env.example for template."
            )
    
    def get_provider_settings(self, provider: str) -> dict[str, Any]:
        """Get settings for a specific provider.
        
        Args:
            provider: Provider name (claude, openai, grok, gemini)
            
        Returns:
            Dictionary of provider-specific settings
        """
        if provider == "claude":
            return {
                "enabled": self.claude_enabled,
                "model": self.claude_model,
                "use_extended_thinking": self.claude_use_extended_thinking,
                "thinking_budget_tokens": self.claude_thinking_budget_tokens,
                "max_tokens": self.claude_max_tokens,
            }
        elif provider == "openai":
            return {
                "enabled": self.openai_enabled,
                "model": self.openai_model,
                "reasoning_effort": self.openai_reasoning_effort,
                "max_tokens": self.openai_max_tokens,
                "web_search": {"enabled": self.openai_web_search_enabled},
            }
        elif provider == "grok":
            return {
                "enabled": self.grok_enabled,
                "model": self.grok_model,
                "max_tokens": self.grok_max_tokens,
            }
        elif provider == "gemini":
            return {
                "enabled": self.gemini_enabled,
                "model": self.gemini_model,
                "max_tokens": self.gemini_max_tokens,
                "temperature": self.gemini_temperature,
                "web_search": {"enabled": self.gemini_web_search_enabled},
            }
        else:
            raise ValueError(f"Unknown provider: {provider}")


# Global settings instance (lazy-loaded to allow tests without .env)
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create global settings instance.
    
    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Module-level settings accessor (lazy singleton pattern)
class _SettingsAccessor:
    """Accessor for lazy-loaded settings that behaves like a Settings instance."""
    
    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to settings instance."""
        return getattr(get_settings(), name)
    
    def __call__(self) -> Settings:
        """Allow calling settings() to get instance."""
        return get_settings()


settings = _SettingsAccessor()

