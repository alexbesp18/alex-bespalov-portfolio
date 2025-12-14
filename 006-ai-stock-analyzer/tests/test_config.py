"""Tests for configuration loading."""

import json
import tempfile
from pathlib import Path

import pytest

from src.config import (
    APIKeys,
    ClaudeSettings,
    GeminiSettings,
    GrokSettings,
    OpenAISettings,
    Settings,
)


class TestAPIKeys:
    """Test API key configuration."""
    
    def test_get_twelve_data_key_primary(self):
        """Test getting Twelve Data key from primary field."""
        keys = APIKeys(twelve_data='test-key-123')
        assert keys.get_twelve_data_key() == 'test-key-123'
    
    def test_get_twelve_data_key_alias(self):
        """Test getting Twelve Data key from alias field."""
        keys = APIKeys(twelve_data_api_key='alias-key-456')
        assert keys.get_twelve_data_key() == 'alias-key-456'
    
    def test_get_twelve_data_key_prefers_alias(self):
        """Test that alias takes precedence."""
        keys = APIKeys(twelve_data='primary', twelve_data_api_key='alias')
        assert keys.get_twelve_data_key() == 'alias'


class TestModelSettings:
    """Test model-specific settings."""
    
    def test_claude_defaults(self):
        """Test Claude settings have sensible defaults."""
        settings = ClaudeSettings()
        assert settings.enabled is True
        assert settings.temperature == 0.3
        assert settings.max_tokens > 0
    
    def test_openai_defaults(self):
        """Test OpenAI settings have sensible defaults."""
        settings = OpenAISettings()
        assert settings.enabled is True
        assert settings.model in ['gpt-4o', 'gpt-5', 'gpt-5-mini']
    
    def test_grok_defaults(self):
        """Test Grok settings have sensible defaults."""
        settings = GrokSettings()
        assert settings.enabled is True
    
    def test_gemini_defaults(self):
        """Test Gemini settings have sensible defaults."""
        settings = GeminiSettings()
        assert settings.enabled is True
        assert settings.use_thinking is False


class TestSettingsLoading:
    """Test config file loading."""
    
    def test_from_valid_config_file(self, sample_config_dict):
        """Test loading from a valid config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_config_dict, f)
            f.flush()
            
            settings = Settings.from_config_file(f.name)
            
            assert settings.api_keys.anthropic == 'test-key'
            assert settings.api_keys.twelve_data == 'test-key'
            assert settings.claude_settings.enabled is True
            assert settings.global_settings.max_workers == 3
            
            Path(f.name).unlink()  # Cleanup
    
    def test_from_missing_file(self):
        """Test that missing config file raises error."""
        with pytest.raises(FileNotFoundError):
            Settings.from_config_file('/nonexistent/config.json')
    
    def test_from_invalid_json(self):
        """Test that invalid JSON raises error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('not valid json {{{')
            f.flush()
            
            with pytest.raises(ValueError):
                Settings.from_config_file(f.name)
            
            Path(f.name).unlink()


class TestSettingsIntegration:
    """Integration tests for settings."""
    
    def test_nested_settings_access(self, sample_config_dict):
        """Test accessing nested settings."""
        settings = Settings(**sample_config_dict)
        
        # Access nested model settings
        assert settings.claude_settings.model == 'sonnet-4.5'
        assert settings.openai_settings.model == 'gpt-4o'
        assert settings.gemini_settings.model == 'gemini-2.0-flash'
        
        # Access API keys
        assert settings.api_keys.get_twelve_data_key() == 'test-key'
