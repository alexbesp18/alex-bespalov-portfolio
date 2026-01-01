"""HTTP utilities with retry logic for web scraping."""

import logging
import urllib.request
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Common browser User-Agent for scraping
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=60))
def fetch_html(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: int = 20,
) -> str:
    """
    Fetch HTML content from URL with retry logic.

    Args:
        url: URL to fetch
        headers: Optional headers dict (defaults to browser User-Agent)
        timeout: Request timeout in seconds

    Returns:
        HTML content as string

    Raises:
        URLError: After 3 failed attempts
    """
    request_headers = {"User-Agent": DEFAULT_USER_AGENT}
    if headers:
        request_headers.update(headers)

    req = urllib.request.Request(url, headers=request_headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        content: bytes = response.read()
        return content.decode("utf-8")


def build_headers(**kwargs: Any) -> dict[str, str]:
    """
    Build request headers with defaults.

    Args:
        **kwargs: Header key-value pairs (underscores become hyphens)

    Returns:
        Headers dict with User-Agent default

    Example:
        build_headers(accept="text/html", cache_control="no-cache")
        # Returns: {"User-Agent": "...", "Accept": "text/html", "Cache-Control": "no-cache"}
    """
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    for key, value in kwargs.items():
        # Convert snake_case to Header-Case
        header_key = key.replace("_", "-").title()
        headers[header_key] = str(value)
    return headers
