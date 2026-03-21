"""Thin Supabase client for ai_scanner schema."""

from __future__ import annotations

from supabase import create_client, Client

from src.config import SUPABASE_URL, SUPABASE_SERVICE_KEY, SCHEMA


_client: Client | None = None


def get_client() -> Client:
    """Get or create Supabase client."""
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _client


def table(name: str):
    """Access a table in the ai_scanner schema."""
    return get_client().schema(SCHEMA).table(name)


def models():
    return table("models")


def picks():
    return table("picks")


def projects():
    return table("projects")
