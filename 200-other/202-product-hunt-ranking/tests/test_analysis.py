"""Tests for Grok AI analysis module."""

import datetime
import json
from unittest.mock import Mock, patch

import pytest

from src.analysis.grok_analyzer import PHGrokAnalyzer
from src.analysis.prompts import (
    BATCH_CATEGORIZATION_PROMPT,
    PRODUCT_CATEGORIZATION_PROMPT,
    WEEKLY_INSIGHTS_PROMPT,
)
from src.db.models import EnrichedProduct, GrokEnrichment
from src.models import Product


class TestPHGrokAnalyzer:
    """Test suite for Grok analyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return PHGrokAnalyzer(api_key="test-key", verbose=False)

    @pytest.fixture
    def sample_product(self):
        """Create sample product."""
        return Product(
            rank=1,
            name="AI Assistant",
            description="An AI-powered productivity tool",
            url="https://producthunt.com/posts/ai-assistant",
            upvotes=500,
        )

    def test_init(self, analyzer):
        """Test analyzer initialization."""
        assert analyzer.api_key == "test-key"
        assert analyzer.model == "grok-4-1-fast-reasoning"
        assert analyzer.base_url == "https://api.x.ai/v1/chat/completions"

    @patch("src.analysis.grok_analyzer.requests.post")
    def test_call_api_success(self, mock_post, analyzer):
        """Test successful API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"category": "AI"}'}}]
        }
        mock_post.return_value = mock_response

        result = analyzer._call_api("test prompt")

        assert result == '{"category": "AI"}'
        mock_post.assert_called_once()

    @patch("src.analysis.grok_analyzer.requests.post")
    def test_call_api_rate_limited(self, mock_post, analyzer):
        """Test API rate limiting handling."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_post.return_value = mock_response

        result = analyzer._call_api("test prompt")

        assert result is None

    @patch("src.analysis.grok_analyzer.requests.post")
    def test_call_api_error(self, mock_post, analyzer):
        """Test API error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        result = analyzer._call_api("test prompt")

        assert result is None

    @patch("src.analysis.grok_analyzer.requests.post")
    def test_call_api_strips_markdown(self, mock_post, analyzer):
        """Test that markdown code blocks are stripped."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '```json\n{"category": "AI"}\n```'}}]
        }
        mock_post.return_value = mock_response

        result = analyzer._call_api("test prompt")

        assert result == '{"category": "AI"}'

    @patch.object(PHGrokAnalyzer, "_call_api")
    def test_categorize_product(self, mock_api, analyzer, sample_product):
        """Test product categorization."""
        mock_api.return_value = json.dumps(
            {
                "category": "AI",
                "subcategory": "AI Assistant",
                "target_audience": "Developers",
                "pricing_model": "Freemium",
                "tech_stack": ["AI/ML", "Python"],
                "innovation_score": 8,
                "market_fit_score": 7,
            }
        )

        result = analyzer.categorize_product(sample_product)

        assert isinstance(result, GrokEnrichment)
        assert result.category == "AI"
        assert result.innovation_score == 8

    @patch.object(PHGrokAnalyzer, "_call_api")
    def test_categorize_product_api_failure(self, mock_api, analyzer, sample_product):
        """Test product categorization when API fails."""
        mock_api.return_value = None

        result = analyzer.categorize_product(sample_product)

        assert isinstance(result, GrokEnrichment)
        assert result.category is None

    @patch.object(PHGrokAnalyzer, "_call_api")
    def test_enrich_products_batch(self, mock_api, analyzer, sample_product):
        """Test batch product enrichment."""
        mock_api.return_value = json.dumps(
            [
                {
                    "rank": 1,
                    "category": "AI",
                    "subcategory": "AI Assistant",
                    "target_audience": "Developers",
                    "pricing_model": "Freemium",
                    "tech_stack": ["AI/ML"],
                    "innovation_score": 8,
                    "market_fit_score": 7,
                }
            ]
        )

        products = [sample_product]
        week_date = datetime.date(2025, 1, 6)

        result = analyzer.enrich_products_batch(
            products=products, week_date=week_date, week_number=2, year=2025
        )

        assert len(result) == 1
        assert isinstance(result[0], EnrichedProduct)
        assert result[0].category == "AI"

    @patch.object(PHGrokAnalyzer, "_call_api")
    def test_enrich_products_batch_fallback(self, mock_api, analyzer, sample_product):
        """Test batch enrichment fallback when API fails."""
        mock_api.return_value = None

        products = [sample_product]
        week_date = datetime.date(2025, 1, 6)

        result = analyzer.enrich_products_batch(
            products=products, week_date=week_date, week_number=2, year=2025
        )

        # Should return products without enrichment
        assert len(result) == 1
        assert result[0].name == sample_product.name
        assert result[0].category is None

    @patch.object(PHGrokAnalyzer, "_call_api")
    def test_generate_weekly_insights(self, mock_api, analyzer):
        """Test weekly insights generation."""
        mock_api.return_value = json.dumps(
            {
                "top_trends": ["AI dominance", "Developer tools rise"],
                "notable_launches": "Several AI products launched this week.",
                "category_breakdown": {"AI": 5, "SaaS": 3},
                "sentiment": "Bullish",
                "key_observation": "AI products continue to dominate.",
            }
        )

        products = [
            EnrichedProduct(
                week_date=datetime.date(2025, 1, 6),
                week_number=2,
                year=2025,
                rank=1,
                name="Test Product",
                description="Test",
                upvotes=100,
                url="https://example.com",
                category="AI",
            )
        ]

        result = analyzer.generate_weekly_insights(
            products=products,
            week_date=datetime.date(2025, 1, 6),
            week_number=2,
            year=2025,
        )

        assert result.sentiment == "Bullish"
        assert len(result.top_trends) == 2


class TestPrompts:
    """Test prompt templates."""

    def test_product_categorization_prompt_format(self):
        """Test that product categorization prompt formats correctly."""
        formatted = PRODUCT_CATEGORIZATION_PROMPT.format(
            name="Test Product",
            description="A test description",
            url="https://example.com",
            upvotes=100,
        )

        assert "Test Product" in formatted
        assert "A test description" in formatted
        assert "100" in formatted

    def test_batch_categorization_prompt_format(self):
        """Test that batch categorization prompt formats correctly."""
        formatted = BATCH_CATEGORIZATION_PROMPT.format(
            count=3, products_list="[1] Product 1\n[2] Product 2"
        )

        assert "3" in formatted
        assert "Product 1" in formatted

    def test_weekly_insights_prompt_format(self):
        """Test that weekly insights prompt formats correctly."""
        formatted = WEEKLY_INSIGHTS_PROMPT.format(
            week_number=10, year=2025, products_json='[{"name": "Test"}]'
        )

        assert "Week 10" in formatted
        assert "2025" in formatted
