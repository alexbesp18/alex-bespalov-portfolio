import os
import pytest
from src.config import Settings

def test_settings_load_from_env():
    """Test that settings load correctly from environment variables."""
    os.environ['TWELVE_DATA_API_KEY'] = 'test_key'
    os.environ['GROK_API_KEY'] = 'test_grok'
    os.environ['GOOGLE_SHEET_NAME'] = 'test_sheet'
    
    settings = Settings()
    assert settings.twelve_data_api_key == 'test_key'
    assert settings.grok_api_key == 'test_grok'
    assert settings.llm_model == 'grok-4-1-fast-reasoning' # Default

def test_settings_missing_field():
    """Test validation error for missing fields."""
    # Clear specific var
    if 'TWELVE_DATA_API_KEY' in os.environ:
        del os.environ['TWELVE_DATA_API_KEY']
    
    with pytest.raises(ValueError):
        Settings()
