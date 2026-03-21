"""CLI entry point. Usage: python cli.py"""

import logging
import sys

from config import get_settings
from pipeline import run_snapshot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> int:
    settings = get_settings()
    if not settings.has_supabase:
        logger.error("SUPABASE_URL and SUPABASE_SERVICE_KEY required")
        return 1

    logger.info("Running daily LEAPS snapshot...")
    persisted = run_snapshot(settings)
    logger.info("Done: %d prices persisted", persisted)
    return 0 if persisted > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
