"""
FastAPI web dashboard for US Hotel Scraper.

Provides a simple web UI to browse and filter hotel deals.
"""

import logging
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config.settings import get_settings
from core.database import get_database

logger = logging.getLogger(__name__)

# Paths
WEB_DIR = Path(__file__).parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

# Create directories if they don't exist
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="US Hotel Scraper",
        description="Browse AA Advantage Hotel deals across the US",
        version="1.0.0",
    )

    # Mount static files
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    # Configure templates
    templates = Jinja2Templates(directory=TEMPLATES_DIR)

    # Custom template filters
    @app.on_event("startup")
    async def add_template_filters():
        templates.env.filters['stars'] = lambda n: "★" * n + "☆" * (5 - n) if n else "Unrated"
        templates.env.filters['money'] = lambda n: f"${n:,.0f}" if n else "$0"
        templates.env.filters['number'] = lambda n: f"{n:,}" if n else "0"

    @app.get("/", response_class=HTMLResponse)
    async def index(
        request: Request,
        min_yield: float = Query(default=10.0, ge=0),
        min_stars: int = Query(default=1, ge=1, le=5),
        max_stars: int = Query(default=5, ge=1, le=5),
        city_id: Optional[int] = None,
        city_ids: Optional[str] = None,
        exclude_cities: bool = Query(default=False),
        sort: str = Query(default="yield_ratio"),
        limit: int = Query(default=100, ge=1, le=500),
    ):
        """Main page with top deals."""
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
            order_by=sort,
        )

        stats = db.get_stats()
        cities = db.get_active_cities()
        latest_run = db.get_latest_scrape_run()

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "deals": deals,
                "stats": stats,
                "cities": cities,
                "latest_run": latest_run,
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
            },
        )

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
        offset: int = Query(default=0, ge=0),
    ):
        """API endpoint for deals (JSON).

        city_ids: Comma-separated list of city IDs (e.g., "1,2,3")
        exclude_cities: If true, exclude the city_ids; if false, include only those cities
        """
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

    @app.get("/api/cities")
    async def api_cities():
        """API endpoint for cities."""
        db = get_database()
        cities = db.get_active_cities()
        return {"cities": cities, "count": len(cities)}

    @app.get("/api/stats")
    async def api_stats():
        """API endpoint for statistics."""
        db = get_database()
        stats = db.get_stats()
        latest_run = db.get_latest_scrape_run()
        return {
            "stats": stats,
            "latest_run": latest_run,
        }

    @app.get("/city/{city_id}", response_class=HTMLResponse)
    async def city_page(
        request: Request,
        city_id: int,
        min_yield: float = Query(default=5.0, ge=0),
        sort: str = Query(default="yield_ratio"),
        limit: int = Query(default=100, ge=1, le=500),
    ):
        """City-specific deals page."""
        db = get_database()

        city = db.get_city_by_id(city_id)
        if not city:
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "message": "City not found"},
                status_code=404,
            )

        deals = db.get_deals_by_city(city_id, limit=limit, min_yield=min_yield)

        return templates.TemplateResponse(
            "city.html",
            {
                "request": request,
                "city": city,
                "deals": deals,
                "filters": {
                    "min_yield": min_yield,
                    "sort": sort,
                    "limit": limit,
                },
            },
        )

    @app.get("/admin/status", response_class=HTMLResponse)
    async def admin_status(request: Request):
        """Admin status page."""
        db = get_database()

        stats = db.get_stats()
        latest_run = db.get_latest_scrape_run()

        return templates.TemplateResponse(
            "admin/status.html",
            {
                "request": request,
                "stats": stats,
                "latest_run": latest_run,
            },
        )

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "web.app:app",
        host=settings.web_host,
        port=settings.web_port,
        reload=True,
    )
