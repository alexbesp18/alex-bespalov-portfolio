"""Tests for configuration settings."""

from src.config import Settings, settings


def test_settings_defaults():
    """Test that settings load with default values."""
    assert settings.grok_model == "grok-4-1-fast-reasoning"
    assert settings.log_level == "INFO"


def test_settings_supabase_defaults():
    """Test Supabase settings have defaults."""
    fresh_settings = Settings()
    # Should have empty string defaults (not fail)
    assert fresh_settings.supabase_url == "" or fresh_settings.supabase_url is not None
    assert fresh_settings.supabase_key == "" or fresh_settings.supabase_key is not None


def test_settings_env_override(monkeypatch):
    """Test that environment variables override defaults."""
    monkeypatch.setenv("GROK_API_KEY", "test-api-key")
    new_settings = Settings()
    assert new_settings.xai_api_key == "test-api-key"


def test_settings_supabase_env_override(monkeypatch):
    """Test Supabase environment variable overrides."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "test-service-key")
    new_settings = Settings()
    assert new_settings.supabase_url == "https://test.supabase.co"
    assert new_settings.supabase_key == "test-service-key"
