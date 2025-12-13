from src.config import settings

def test_settings_defaults():
    """Test that settings load with default values."""
    assert settings.gsheet_name == "Product Hunt Rankings"
    assert settings.log_level == "INFO"

def test_settings_env_override(monkeypatch):
    """Test that environment variables override defaults."""
    monkeypatch.setenv("GSHEET_NAME", "Test Sheet")
    from src.config import Settings
    # Reload settings or create new instance
    new_settings = Settings()
    assert new_settings.gsheet_name == "Test Sheet"
