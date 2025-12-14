"""
Configuration management using Pydantic Settings.

Loads configuration from config.json and provides typed access
to all settings including API keys and model configurations.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class ClaudeSettings(BaseModel):
    """Claude/Anthropic model settings."""
    enabled: bool = True
    model: str = "sonnet-4.5"
    max_tokens: int = 4096
    temperature: float = 0.3
    use_extended_thinking: bool = False
    thinking_budget_tokens: int = 10000


class OpenAISettings(BaseModel):
    """OpenAI/GPT model settings."""
    enabled: bool = True
    model: str = "gpt-4o"
    max_tokens: int = 8192
    temperature: float = 0.3
    reasoning_effort: Optional[str] = None


class GrokSettings(BaseModel):
    """Grok/XAI model settings."""
    enabled: bool = True
    model: str = "grok-2"
    max_tokens: int = 8192
    temperature: float = 0.3


class GeminiSettings(BaseModel):
    """Google Gemini model settings."""
    enabled: bool = True
    model: str = "gemini-2.0-flash"
    max_tokens: int = 8000
    temperature: float = 0.3
    use_thinking: bool = False
    thinking_budget_tokens: int = 8000


class GlobalSettings(BaseModel):
    """Global execution settings."""
    use_concurrent: bool = True
    max_workers: int = 3


class APIKeys(BaseModel):
    """API key configuration."""
    anthropic: Optional[str] = None
    openai: Optional[str] = None
    google: Optional[str] = None
    xai: Optional[str] = None
    twelve_data: Optional[str] = None
    twelve_data_api_key: Optional[str] = None  # Alias

    def get_twelve_data_key(self) -> Optional[str]:
        """Get Twelve Data API key from either field."""
        return self.twelve_data_api_key or self.twelve_data


class Settings(BaseSettings):
    """
    Main settings container.
    
    Loads from config.json in the project root.
    """
    api_keys: APIKeys = Field(default_factory=APIKeys)
    google_sheet_url: str = ""
    claude_settings: ClaudeSettings = Field(default_factory=ClaudeSettings)
    openai_settings: OpenAISettings = Field(default_factory=OpenAISettings)
    grok_settings: GrokSettings = Field(default_factory=GrokSettings)
    gemini_settings: GeminiSettings = Field(default_factory=GeminiSettings)
    global_settings: GlobalSettings = Field(default_factory=GlobalSettings)
    
    @classmethod
    def from_config_file(cls, config_path: str = "config.json") -> "Settings":
        """
        Load settings from a JSON config file.
        
        Args:
            config_path: Path to the config.json file
            
        Returns:
            Settings instance with loaded configuration
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid JSON
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        try:
            with open(path, 'r') as f:
                config_data = json.load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return cls(**config_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")


# Default settings instance (loaded lazily)
_settings: Optional[Settings] = None


def get_settings(config_path: str = "config.json") -> Settings:
    """
    Get the global settings instance.
    
    Args:
        config_path: Path to config file (only used on first call)
        
    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings.from_config_file(config_path)
    return _settings


def reload_settings(config_path: str = "config.json") -> Settings:
    """
    Force reload settings from config file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Fresh Settings instance
    """
    global _settings
    _settings = Settings.from_config_file(config_path)
    return _settings
