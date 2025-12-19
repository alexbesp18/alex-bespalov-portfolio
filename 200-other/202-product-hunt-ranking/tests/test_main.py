"""
Tests for main.py functionality including Google Sheets integration.
Uses mocking to avoid actual API calls.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.main import save_to_gsheet, fetch_html, main
from src.models import Product


class TestSaveToGsheet:
    """Test suite for Google Sheets saving functionality."""

    @pytest.fixture
    def sample_products(self):
        """Create sample products for testing."""
        return [
            Product(rank=1, name="Test Product 1", url="https://producthunt.com/products/test-1", 
                   description="A great product", upvotes=500),
            Product(rank=2, name="Test Product 2", url="https://producthunt.com/products/test-2",
                   description="Another product", upvotes=300),
        ]

    @patch('src.main.gspread.authorize')
    @patch('src.main.Credentials.from_service_account_info')
    @patch('src.main.settings')
    def test_save_to_gsheet_success(self, mock_settings, mock_creds, mock_authorize, sample_products):
        """Test successful save to Google Sheets."""
        # Setup mocks
        mock_settings.gdrive_api_key_json = '{"client_email": "test@test.iam.gserviceaccount.com", "private_key": "fake"}'
        mock_settings.gsheet_id = "test-sheet-id"
        mock_settings.gsheet_tab = "Weekly Top 10"
        mock_settings.gsheet_name = "Test Sheet"
        
        mock_sheet = Mock()
        mock_spreadsheet = Mock()
        mock_spreadsheet.worksheet.return_value = mock_sheet
        mock_authorize.return_value.open_by_key.return_value = mock_spreadsheet
        
        # Execute
        save_to_gsheet(sample_products)
        
        # Verify
        mock_sheet.append_rows.assert_called_once()
        call_args = mock_sheet.append_rows.call_args[0][0]
        assert len(call_args) == 2  # Two products
        assert call_args[0][1] == 1  # First product rank
        assert call_args[0][2] == "Test Product 1"  # First product name
        assert call_args[0][4] == 500  # Upvotes
    
    @patch('src.main.settings')
    def test_save_to_gsheet_no_credentials(self, mock_settings, sample_products, caplog):
        """Test graceful handling when no credentials are provided."""
        mock_settings.gdrive_api_key_json = None
        
        # Should not raise, just log warning
        save_to_gsheet(sample_products)
        
        assert "No Google Drive Creds" in caplog.text

    @patch('src.main.settings')
    def test_save_to_gsheet_with_date_override(self, mock_settings, sample_products):
        """Test that date_override parameter is respected."""
        mock_settings.gdrive_api_key_json = None  # Skip actual API call
        
        # This should use the date_override parameter
        save_to_gsheet(sample_products, date_override="2025-01-01")
        # Just ensuring no exception is raised


class TestFetchHtml:
    """Test suite for HTML fetching functionality."""

    @patch('src.main.urllib.request.urlopen')
    def test_fetch_html_success(self, mock_urlopen):
        """Test successful HTML fetch."""
        mock_response = Mock()
        mock_response.read.return_value = b"<html><body>Test</body></html>"
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        result = fetch_html("https://example.com")
        
        assert result == "<html><body>Test</body></html>"
        mock_urlopen.assert_called_once()

    @patch('src.main.urllib.request.urlopen')
    def test_fetch_html_with_retry(self, mock_urlopen):
        """Test that fetch retries on failure."""
        # First call fails, second succeeds
        mock_response = Mock()
        mock_response.read.return_value = b"<html>Success</html>"
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        
        mock_urlopen.side_effect = [Exception("Network error"), mock_response]
        
        # Should succeed on retry
        result = fetch_html("https://example.com")
        assert "Success" in result


class TestProductModel:
    """Test suite for Product Pydantic model."""

    def test_product_creation(self):
        """Test creating a valid product."""
        product = Product(
            rank=1,
            name="Test",
            url="https://example.com",
            description="Description",
            upvotes=100
        )
        assert product.rank == 1
        assert product.upvotes == 100

    def test_product_defaults(self):
        """Test that default values are applied."""
        product = Product(rank=1, name="Test", url="https://example.com")
        assert product.description == ""
        assert product.upvotes == 0

    def test_product_validation(self):
        """Test that validation works."""
        with pytest.raises(Exception):
            Product(rank=0, name="", url="")  # Invalid: rank must be >= 1, name min 1 char
