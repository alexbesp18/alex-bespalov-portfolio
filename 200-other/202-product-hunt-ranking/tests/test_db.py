"""Tests for database module."""

import datetime
from unittest.mock import Mock, patch, MagicMock
import pytest

from src.db.supabase_client import PHSupabaseClient
from src.db.models import PHProduct, EnrichedProduct, PHWeeklyInsights, GrokEnrichment


class TestEnrichedProduct:
    """Test suite for EnrichedProduct model."""

    def test_basic_creation(self):
        """Test basic enriched product creation."""
        product = EnrichedProduct(
            week_date=datetime.date(2025, 1, 6),
            week_number=2,
            year=2025,
            rank=1,
            name="Test Product",
            description="A test product",
            upvotes=500,
            url="https://example.com"
        )

        assert product.rank == 1
        assert product.name == "Test Product"
        assert product.category is None

    def test_with_enrichment(self):
        """Test enriched product with AI fields."""
        product = EnrichedProduct(
            week_date=datetime.date(2025, 1, 6),
            week_number=2,
            year=2025,
            rank=1,
            name="AI Tool",
            description="An AI tool",
            upvotes=1000,
            url="https://example.com",
            category="AI",
            subcategory="AI Assistant",
            target_audience="Developers",
            innovation_score=8.5,
            market_fit_score=7.0
        )

        assert product.category == "AI"
        assert product.innovation_score == 8.5

    def test_to_db_dict_minimal(self):
        """Test to_db_dict with minimal fields."""
        product = EnrichedProduct(
            week_date=datetime.date(2025, 1, 6),
            week_number=2,
            year=2025,
            rank=1,
            name="Test",
            description="",
            upvotes=0,
            url="https://example.com"
        )

        db_dict = product.to_db_dict()

        assert db_dict["week_date"] == "2025-01-06"
        assert db_dict["rank"] == 1
        assert "category" not in db_dict  # None fields excluded

    def test_to_db_dict_full(self):
        """Test to_db_dict with all fields."""
        product = EnrichedProduct(
            week_date=datetime.date(2025, 1, 6),
            week_number=2,
            year=2025,
            rank=1,
            name="Full Product",
            description="Description",
            upvotes=500,
            url="https://example.com",
            category="AI",
            subcategory="Assistant",
            target_audience="Developers",
            tech_stack=["Python", "React"],
            pricing_model="Freemium",
            innovation_score=8.0,
            market_fit_score=7.0,
            analyzed_at=datetime.datetime(2025, 1, 6, 12, 0, 0)
        )

        db_dict = product.to_db_dict()

        assert db_dict["category"] == "AI"
        assert db_dict["tech_stack"] == ["Python", "React"]
        assert db_dict["innovation_score"] == 8.0
        assert "analyzed_at" in db_dict


class TestPHWeeklyInsights:
    """Test suite for PHWeeklyInsights model."""

    def test_creation(self):
        """Test weekly insights creation."""
        insights = PHWeeklyInsights(
            week_date=datetime.date(2025, 1, 6),
            year=2025,
            week_number=2,
            top_trends=["AI dominance", "Developer tools"],
            notable_launches="Great week for AI.",
            category_breakdown={"AI": 5, "SaaS": 3},
            avg_upvotes=450.5,
            sentiment="Bullish",
            full_analysis='{"key": "value"}'
        )

        assert len(insights.top_trends) == 2
        assert insights.sentiment == "Bullish"

    def test_to_db_dict(self):
        """Test insights to_db_dict."""
        insights = PHWeeklyInsights(
            week_date=datetime.date(2025, 1, 6),
            year=2025,
            week_number=2,
            top_trends=["Trend 1"],
            category_breakdown={"AI": 3},
            avg_upvotes=300.0,
            sentiment="Neutral"
        )

        db_dict = insights.to_db_dict()

        assert db_dict["week_date"] == "2025-01-06"
        assert db_dict["sentiment"] == "Neutral"


class TestGrokEnrichment:
    """Test suite for GrokEnrichment model."""

    def test_empty_enrichment(self):
        """Test empty enrichment creation."""
        enrichment = GrokEnrichment()

        assert enrichment.category is None
        assert enrichment.innovation_score is None

    def test_full_enrichment(self):
        """Test full enrichment creation."""
        enrichment = GrokEnrichment(
            category="AI",
            subcategory="Assistant",
            target_audience="Developers",
            tech_stack=["Python"],
            pricing_model="Free",
            innovation_score=9.0,
            market_fit_score=8.0
        )

        assert enrichment.category == "AI"
        assert enrichment.innovation_score == 9.0

    def test_score_validation(self):
        """Test that scores are validated."""
        # Score should be between 0 and 10
        enrichment = GrokEnrichment(innovation_score=5.0)
        assert enrichment.innovation_score == 5.0


class TestPHSupabaseClient:
    """Test suite for Supabase client."""

    @pytest.fixture
    def client(self):
        """Create client instance."""
        return PHSupabaseClient(
            url="https://test.supabase.co",
            key="test-key"
        )

    def test_init(self, client):
        """Test client initialization."""
        assert client.url == "https://test.supabase.co"
        assert client.key == "test-key"
        assert client._client is None  # Lazy loaded

    @patch('src.db.supabase_client.create_client')
    def test_lazy_client_creation(self, mock_create, client):
        """Test that Supabase client is lazily created."""
        mock_supabase = Mock()
        mock_create.return_value = mock_supabase

        # Access client property
        _ = client.client

        mock_create.assert_called_once_with(
            "https://test.supabase.co",
            "test-key"
        )

    @patch('src.db.supabase_client.create_client')
    def test_save_products_empty(self, mock_create, client):
        """Test saving empty product list."""
        result = client.save_products([])

        assert result == 0
        mock_create.assert_not_called()

    @patch('src.db.supabase_client.create_client')
    def test_save_products(self, mock_create, client):
        """Test saving products."""
        mock_supabase = Mock()
        mock_table = Mock()
        mock_table.upsert.return_value.execute.return_value.data = [{"id": 1}]
        mock_schema = Mock()
        mock_schema.table.return_value = mock_table
        mock_supabase.schema.return_value = mock_schema
        mock_create.return_value = mock_supabase

        products = [
            EnrichedProduct(
                week_date=datetime.date(2025, 1, 6),
                week_number=2,
                year=2025,
                rank=1,
                name="Test",
                description="",
                upvotes=100,
                url="https://example.com"
            )
        ]

        result = client.save_products(products)

        assert result == 1
        mock_table.upsert.assert_called_once()

    @patch('src.db.supabase_client.create_client')
    def test_week_exists(self, mock_create, client):
        """Test checking if week exists."""
        mock_supabase = Mock()
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [{"rank": 1}]
        mock_schema = Mock()
        mock_schema.table.return_value = mock_table
        mock_supabase.schema.return_value = mock_schema
        mock_create.return_value = mock_supabase

        result = client.week_exists(datetime.date(2025, 1, 6))

        assert result is True

    @patch('src.db.supabase_client.create_client')
    def test_week_not_exists(self, mock_create, client):
        """Test checking if week does not exist."""
        mock_supabase = Mock()
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        mock_schema = Mock()
        mock_schema.table.return_value = mock_table
        mock_supabase.schema.return_value = mock_schema
        mock_create.return_value = mock_supabase

        result = client.week_exists(datetime.date(2025, 1, 6))

        assert result is False
