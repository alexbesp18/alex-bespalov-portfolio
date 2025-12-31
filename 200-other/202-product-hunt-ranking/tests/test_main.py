"""
Tests for main.py functionality including Supabase and Grok integration.
Uses mocking to avoid actual API calls.
"""

import datetime
from unittest.mock import Mock, patch

import pytest

from src.main import fetch_html, get_current_week_info, get_week_url, run_pipeline
from src.models import Product


class TestGetWeekInfo:
    """Test suite for week URL and date calculation."""

    def test_get_current_week_info(self):
        """Test that current week info is returned correctly."""
        url, week, year, week_date = get_current_week_info()

        assert "producthunt.com/leaderboard/weekly" in url
        assert 1 <= week <= 53
        assert year >= 2024
        assert isinstance(week_date, datetime.date)
        assert week_date.weekday() == 0  # Monday

    def test_get_week_url(self):
        """Test URL construction for specific week."""
        url, week_date = get_week_url(2025, 10)

        assert url == "https://www.producthunt.com/leaderboard/weekly/2025/10"
        assert isinstance(week_date, datetime.date)
        assert week_date.weekday() == 0  # Monday


class TestFetchHtml:
    """Test suite for HTML fetching functionality."""

    @patch("src.main.urllib.request.urlopen")
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

    @patch("src.main.urllib.request.urlopen")
    def test_fetch_html_with_retry(self, mock_urlopen):
        """Test that fetch retries on failure."""
        mock_response = Mock()
        mock_response.read.return_value = b"<html>Success</html>"
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        mock_urlopen.side_effect = [Exception("Network error"), mock_response]

        result = fetch_html("https://example.com")
        assert "Success" in result


class TestRunPipeline:
    """Test suite for the main pipeline function."""

    @patch("src.main.settings")
    def test_pipeline_fails_without_supabase_credentials(self, mock_settings):
        """Test pipeline fails gracefully without Supabase credentials."""
        mock_settings.supabase_url = ""
        mock_settings.supabase_key = ""

        result = run_pipeline()

        assert result is False

    @patch("src.main.PHSupabaseClient")
    @patch("src.main.fetch_html")
    @patch("src.main.parse_products")
    @patch("src.main.settings")
    def test_pipeline_skips_existing_week(
        self, mock_settings, mock_parse, mock_fetch, mock_db_class
    ):
        """Test pipeline skips weeks that already exist."""
        mock_settings.supabase_url = "https://test.supabase.co"
        mock_settings.supabase_key = "test-key"
        mock_settings.xai_api_key = ""
        mock_settings.grok_model = "grok-4-1-fast-reasoning"

        mock_db = Mock()
        mock_db.week_exists.return_value = True
        mock_db_class.return_value = mock_db

        result = run_pipeline(year=2025, week=10, skip_if_exists=True)

        assert result is True
        mock_fetch.assert_not_called()

    @patch("src.main.PHSupabaseClient")
    @patch("src.main.fetch_html")
    @patch("src.main.parse_products")
    @patch("src.main.settings")
    def test_pipeline_saves_products_without_grok(
        self, mock_settings, mock_parse, mock_fetch, mock_db_class
    ):
        """Test pipeline saves products without Grok enrichment."""
        mock_settings.supabase_url = "https://test.supabase.co"
        mock_settings.supabase_key = "test-key"
        mock_settings.xai_api_key = ""  # No Grok
        mock_settings.grok_model = "grok-4-1-fast-reasoning"

        mock_db = Mock()
        mock_db.week_exists.return_value = False
        mock_db.save_products.return_value = 2
        mock_db_class.return_value = mock_db

        mock_fetch.return_value = "<html></html>"
        mock_parse.return_value = [
            Product(rank=1, name="Test", url="https://example.com", upvotes=100),
            Product(rank=2, name="Test 2", url="https://example2.com", upvotes=50),
        ]

        result = run_pipeline(year=2025, week=10)

        assert result is True
        mock_db.save_products.assert_called_once()
        # Should not save insights without Grok
        mock_db.save_insights.assert_not_called()

    @patch("src.main.PHGrokAnalyzer")
    @patch("src.main.PHSupabaseClient")
    @patch("src.main.fetch_html")
    @patch("src.main.parse_products")
    @patch("src.main.settings")
    def test_pipeline_with_grok_enrichment(
        self, mock_settings, mock_parse, mock_fetch, mock_db_class, mock_analyzer_class
    ):
        """Test pipeline with full Grok enrichment."""
        mock_settings.supabase_url = "https://test.supabase.co"
        mock_settings.supabase_key = "test-key"
        mock_settings.xai_api_key = "test-xai-key"
        mock_settings.grok_model = "grok-4-1-fast-reasoning"

        mock_db = Mock()
        mock_db.week_exists.return_value = False
        mock_db.save_products.return_value = 2
        mock_db_class.return_value = mock_db

        mock_analyzer = Mock()
        mock_analyzer.enrich_products_batch.return_value = []
        mock_analyzer.generate_weekly_insights.return_value = Mock()
        mock_analyzer_class.return_value = mock_analyzer

        mock_fetch.return_value = "<html></html>"
        mock_parse.return_value = [
            Product(rank=1, name="Test", url="https://example.com", upvotes=100),
        ]

        result = run_pipeline(year=2025, week=10)

        assert result is True
        mock_analyzer.enrich_products_batch.assert_called_once()


class TestProductModel:
    """Test suite for Product Pydantic model."""

    def test_product_creation(self):
        """Test creating a valid product."""
        product = Product(
            rank=1,
            name="Test",
            url="https://example.com",
            description="Description",
            upvotes=100,
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
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Product(rank=0, name="", url="")  # Invalid
