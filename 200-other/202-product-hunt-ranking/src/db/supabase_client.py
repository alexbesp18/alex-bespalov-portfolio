"""Supabase client for Product Hunt data storage."""

import logging
from datetime import date
from typing import Any

from supabase import Client, create_client

from src.db.models import EnrichedProduct, PHWeeklyInsights

logger = logging.getLogger(__name__)


class PHSupabaseClient:
    """
    Supabase client for Product Hunt data.

    Tables:
    - ph_products: Weekly product rankings with AI enrichment
    - ph_weekly_insights: AI-generated weekly analysis
    """

    def __init__(self, url: str, key: str):
        """
        Initialize Supabase client.

        Args:
            url: Supabase project URL
            key: Supabase service role key
        """
        self.url = url
        self.key = key
        self._client: Client | None = None

    @property
    def client(self) -> Client:
        """Lazy-load Supabase client."""
        if self._client is None:
            self._client = create_client(self.url, self.key)
        return self._client

    def save_products(self, products: list[EnrichedProduct]) -> int:
        """
        Save enriched products to Supabase.
        Uses upsert to handle re-runs.

        Args:
            products: List of enriched products

        Returns:
            Number of products saved
        """
        if not products:
            logger.warning("No products to save")
            return 0

        rows = [p.to_db_dict() for p in products]

        try:
            result = (
                self.client.schema("product_hunt")
                .table("products")
                .upsert(rows, on_conflict="week_date,rank")
                .execute()
            )

            count = len(result.data) if result.data else 0
            logger.info(f"Saved {count} products to Supabase")
            return count

        except Exception as e:
            logger.error(f"Failed to save products: {e}", exc_info=True)
            raise

    def save_insights(self, insights: PHWeeklyInsights) -> bool:
        """
        Save weekly insights to Supabase.
        Uses upsert to handle re-runs.

        Args:
            insights: Weekly insights object

        Returns:
            True if successful
        """
        try:
            self.client.schema("product_hunt").table("weekly_insights").upsert(
                insights.to_db_dict(), on_conflict="week_date"
            ).execute()

            logger.info(f"Saved insights for week {insights.week_date}")
            return True

        except Exception as e:
            logger.error(f"Failed to save insights: {e}", exc_info=True)
            raise

    def get_products_for_week(self, week_date: date) -> list[dict[str, Any]]:
        """
        Retrieve products for a specific week.

        Args:
            week_date: The week's date (Monday)

        Returns:
            List of product records
        """
        try:
            result = (
                self.client.schema("product_hunt")
                .table("products")
                .select("*")
                .eq("week_date", week_date.isoformat())
                .order("rank")
                .execute()
            )

            return result.data or []

        except Exception as e:
            logger.error(f"Failed to get products for {week_date}: {e}")
            return []

    def get_insights_for_week(self, week_date: date) -> dict[str, Any] | None:
        """
        Retrieve insights for a specific week.

        Args:
            week_date: The week's date

        Returns:
            Insights record or None
        """
        try:
            result = (
                self.client.schema("product_hunt")
                .table("weekly_insights")
                .select("*")
                .eq("week_date", week_date.isoformat())
                .single()
                .execute()
            )

            data: dict[str, Any] | None = result.data
            return data

        except Exception as e:
            logger.debug(f"No insights for {week_date}: {e}")
            return None

    def week_exists(self, week_date: date) -> bool:
        """
        Check if data exists for a given week.

        Args:
            week_date: The week's date

        Returns:
            True if products exist for this week
        """
        try:
            result = (
                self.client.schema("product_hunt")
                .table("products")
                .select("rank")
                .eq("week_date", week_date.isoformat())
                .limit(1)
                .execute()
            )

            return bool(result.data)

        except Exception as e:
            logger.error(f"Failed to check week existence: {e}")
            return False
