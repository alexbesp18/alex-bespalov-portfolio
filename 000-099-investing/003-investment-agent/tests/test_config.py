"""Tests for configuration management."""

import os
from pathlib import Path

import pytest

from src.config import Settings


def test_settings_loads_from_env(test_settings: Settings):
    """Test that settings can be instantiated."""
    assert test_settings.anthropic_api_key is not None
    assert test_settings.openai_api_key is not None
    assert test_settings.default_provider == "claude"
    assert test_settings.default_max_tokens == 64000


def test_provider_settings_claude(test_settings: Settings):
    """Test Claude provider settings."""
    settings = test_settings.get_provider_settings("claude")
    assert settings["enabled"] == test_settings.claude_enabled
    assert settings["model"] == test_settings.claude_model
    assert "max_tokens" in settings


def test_provider_settings_openai(test_settings: Settings):
    """Test OpenAI provider settings."""
    settings = test_settings.get_provider_settings("openai")
    assert settings["enabled"] == test_settings.openai_enabled
    assert settings["model"] == test_settings.openai_model
    assert "max_tokens" in settings


def test_provider_settings_grok(test_settings: Settings):
    """Test Grok provider settings."""
    settings = test_settings.get_provider_settings("grok")
    assert settings["enabled"] == test_settings.grok_enabled
    assert settings["model"] == test_settings.grok_model


def test_provider_settings_gemini(test_settings: Settings):
    """Test Gemini provider settings."""
    settings = test_settings.get_provider_settings("gemini")
    assert settings["enabled"] == test_settings.gemini_enabled
    assert settings["model"] == test_settings.gemini_model


def test_invalid_provider(test_settings: Settings):
    """Test that invalid provider raises ValueError."""
    with pytest.raises(ValueError):
        test_settings.get_provider_settings("invalid")


def test_path_settings(test_settings: Settings):
    """Test path settings."""
    assert isinstance(test_settings.input_folder, Path)
    assert isinstance(test_settings.output_folder, Path)

