"""
Vercel serverless entry point for US Hotel Scraper API.

This is a minimal API-only version for Vercel deployment.
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import os

# Force Supabase mode on Vercel
os.environ.setdefault('DB_MODE', 'supabase')

from config.settings import get_settings
from core.database import get_database

app = FastAPI(
    title="US Hotel Scraper API",
    description="API for AA Advantage Hotel deals across the US",
    version="1.0.0",
)

# Enable CORS for static dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "US Hotel Scraper API"}


@app.get("/api/deals")
async def api_deals(
    min_yield: float = Query(default=10.0, ge=0),
    min_stars: int = Query(default=1, ge=1, le=5),
    max_stars: int = Query(default=5, ge=1, le=5),
    city_id: Optional[int] = None,
    city_ids: Optional[str] = None,
    exclude_cities: bool = Query(default=False),
    check_in_start: Optional[str] = None,
    check_in_end: Optional[str] = None,
    sort: str = Query(default="yield_ratio"),
    limit: int = Query(default=100, ge=1, le=500),
):
    """Get hotel deals with filters.

    city_ids: Comma-separated list of city IDs (e.g., "1,2,3")
    exclude_cities: If true, exclude the city_ids; if false, include only those cities
    """
    try:
        db = get_database()

        # Parse comma-separated city_ids
        city_id_list: Optional[List[int]] = None
        if city_ids:
            try:
                city_id_list = [int(x.strip()) for x in city_ids.split(",") if x.strip()]
            except ValueError:
                city_id_list = None

        deals = db.get_top_deals(
            limit=limit,
            min_yield=min_yield,
            min_stars=min_stars,
            max_stars=max_stars,
            city_id=city_id,
            city_ids=city_id_list,
            exclude_cities=exclude_cities,
            check_in_start=check_in_start,
            check_in_end=check_in_end,
            order_by=sort,
        )

        return {
            "deals": deals,
            "count": len(deals),
            "filters": {
                "min_yield": min_yield,
                "min_stars": min_stars,
                "max_stars": max_stars,
                "city_id": city_id,
                "city_ids": city_ids,
                "exclude_cities": exclude_cities,
                "sort": sort,
                "limit": limit,
            },
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


@app.get("/api/cities")
async def api_cities():
    """Get all active cities."""
    db = get_database()
    cities = db.get_active_cities()
    return {"cities": cities, "count": len(cities)}


@app.get("/api/stats")
async def api_stats():
    """Get database statistics."""
    try:
        db = get_database()
        stats = db.get_stats()
        latest_run = db.get_latest_scrape_run()
        return {
            "stats": stats,
            "latest_run": latest_run,
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


@app.get("/api/debug")
async def api_debug():
    """Debug endpoint to check environment."""
    import os
    from config.settings import get_settings
    settings = get_settings()
    return {
        "db_mode": settings.db_mode,
        "supabase_url_set": bool(settings.supabase_url),
        "supabase_key_set": bool(settings.supabase_key),
        "env_db_mode": os.environ.get("DB_MODE", "not_set"),
        "env_supabase_url": bool(os.environ.get("SUPABASE_URL")),
    }
