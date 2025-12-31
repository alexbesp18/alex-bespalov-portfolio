"""Grok AI analyzer for Product Hunt products."""

import json
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List

from src.models import Product
from src.db.models import EnrichedProduct, PHWeeklyInsights, GrokEnrichment
from src.analysis.prompts import (
    PRODUCT_CATEGORIZATION_PROMPT,
    WEEKLY_INSIGHTS_PROMPT,
    BATCH_CATEGORIZATION_PROMPT,
)

logger = logging.getLogger(__name__)


class PHGrokAnalyzer:
    """
    Grok AI analyzer for Product Hunt products.

    Capabilities:
    - Categorize products by type, audience, pricing
    - Extract metadata (tech stack, target audience)
    - Generate weekly insights and trends
    """

    def __init__(
        self,
        api_key: str,
        model: str = "grok-4-1-fast-reasoning",
        max_tokens: int = 2000,
        verbose: bool = False
    ):
        """
        Initialize Grok analyzer.

        Args:
            api_key: xAI API key
            model: Model to use (default: grok-4-1-fast-reasoning)
            max_tokens: Max response tokens
            verbose: Print progress
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.base_url = "https://api.x.ai/v1/chat/completions"
        self.verbose = verbose

    def _call_api(
        self,
        prompt: str,
        temperature: float = 0.3,
        json_response: bool = True,
        timeout: int = 60
    ) -> Optional[str]:
        """
        Make API call to Grok.

        Returns:
            Response content string, or None on error
        """
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": self.max_tokens,
            }

            if json_response:
                payload["response_format"] = {"type": "json_object"}

            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=timeout
            )

            if response.status_code == 429:
                logger.warning("Rate limited by Grok API")
                return None

            if response.status_code != 200:
                logger.error(f"Grok API error: {response.status_code} - {response.text}")
                return None

            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            # Strip markdown code blocks if present
            if content.startswith("```"):
                lines = content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                content = "\n".join(lines)

            return str(content) if content else None

        except requests.exceptions.Timeout:
            logger.error("Grok API request timeout")
            return None
        except Exception as e:
            logger.error(f"Grok API error: {e}", exc_info=True)
            return None

    def categorize_product(self, product: Product) -> GrokEnrichment:
        """
        Categorize a single product using Grok.

        Args:
            product: Product to categorize

        Returns:
            GrokEnrichment with category, scores, etc.
        """
        if self.verbose:
            logger.info(f"Categorizing: {product.name}")

        prompt = PRODUCT_CATEGORIZATION_PROMPT.format(
            name=product.name,
            description=product.description,
            url=product.url,
            upvotes=product.upvotes
        )

        content = self._call_api(prompt)

        if not content:
            return GrokEnrichment()

        try:
            data = json.loads(content)
            return GrokEnrichment(
                category=data.get("category"),
                subcategory=data.get("subcategory"),
                target_audience=data.get("target_audience"),
                tech_stack=data.get("tech_stack"),
                pricing_model=data.get("pricing_model"),
                innovation_score=data.get("innovation_score"),
                market_fit_score=data.get("market_fit_score"),
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Grok response: {e}")
            return GrokEnrichment()

    def enrich_products_batch(
        self,
        products: List[Product],
        week_date: Any,
        week_number: int,
        year: int
    ) -> List[EnrichedProduct]:
        """
        Enrich multiple products in a single API call (more efficient).

        Args:
            products: List of products to enrich
            week_date: Date of the week
            week_number: ISO week number
            year: Year

        Returns:
            List of enriched products
        """
        if self.verbose:
            logger.info(f"Batch categorizing {len(products)} products...")

        # Format products for prompt
        products_list = "\n\n".join([
            f"[{i+1}] {p.name}\nDescription: {p.description}\nURL: {p.url}\nUpvotes: {p.upvotes}"
            for i, p in enumerate(products)
        ])

        prompt = BATCH_CATEGORIZATION_PROMPT.format(
            count=len(products),
            products_list=products_list
        )

        content = self._call_api(prompt, timeout=120)

        enriched = []
        now = datetime.utcnow()

        if content:
            try:
                results = json.loads(content)
                if isinstance(results, list) and len(results) == len(products):
                    for product, enrichment in zip(products, results):
                        enriched.append(EnrichedProduct(
                            week_date=week_date,
                            week_number=week_number,
                            year=year,
                            rank=product.rank,
                            name=product.name,
                            description=product.description,
                            upvotes=product.upvotes,
                            url=str(product.url),
                            category=enrichment.get("category"),
                            subcategory=enrichment.get("subcategory"),
                            target_audience=enrichment.get("target_audience"),
                            tech_stack=enrichment.get("tech_stack"),
                            pricing_model=enrichment.get("pricing_model"),
                            innovation_score=enrichment.get("innovation_score"),
                            market_fit_score=enrichment.get("market_fit_score"),
                            analyzed_at=now,
                        ))
                    if self.verbose:
                        logger.info(f"Successfully enriched {len(enriched)} products")
                    return enriched
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse batch response: {e}")

        # Fallback: create enriched products without AI data
        logger.warning("Batch enrichment failed, saving raw products")
        for product in products:
            enriched.append(EnrichedProduct(
                week_date=week_date,
                week_number=week_number,
                year=year,
                rank=product.rank,
                name=product.name,
                description=product.description,
                upvotes=product.upvotes,
                url=str(product.url),
            ))

        return enriched

    def generate_weekly_insights(
        self,
        products: List[EnrichedProduct],
        week_date: Any,
        week_number: int,
        year: int
    ) -> PHWeeklyInsights:
        """
        Generate AI insights for the week's products.

        Args:
            products: List of enriched products
            week_date: Date of the week
            week_number: ISO week number
            year: Year

        Returns:
            PHWeeklyInsights object
        """
        if self.verbose:
            logger.info(f"Generating insights for Week {week_number}, {year}...")

        # Format products as JSON for the prompt
        products_data = [
            {
                "rank": p.rank,
                "name": p.name,
                "description": p.description,
                "upvotes": p.upvotes,
                "category": p.category,
                "subcategory": p.subcategory,
            }
            for p in products
        ]

        prompt = WEEKLY_INSIGHTS_PROMPT.format(
            week_number=week_number,
            year=year,
            products_json=json.dumps(products_data, indent=2)
        )

        content = self._call_api(prompt, timeout=90)

        # Calculate avg upvotes
        avg_upvotes = sum(p.upvotes for p in products) / len(products) if products else 0

        # Build category breakdown from enriched data
        category_breakdown: Dict[str, int] = {}
        for p in products:
            if p.category:
                category_breakdown[p.category] = category_breakdown.get(p.category, 0) + 1

        if content:
            try:
                data = json.loads(content)
                return PHWeeklyInsights(
                    week_date=week_date,
                    year=year,
                    week_number=week_number,
                    top_trends=data.get("top_trends", []),
                    notable_launches=data.get("notable_launches", ""),
                    category_breakdown=data.get("category_breakdown", category_breakdown),
                    avg_upvotes=avg_upvotes,
                    sentiment=data.get("sentiment", "Neutral"),
                    full_analysis=json.dumps(data),
                )
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse insights response: {e}")

        # Return basic insights without AI analysis
        return PHWeeklyInsights(
            week_date=week_date,
            year=year,
            week_number=week_number,
            category_breakdown=category_breakdown,
            avg_upvotes=avg_upvotes,
            sentiment="Neutral",
            full_analysis="AI analysis unavailable",
        )
