"""
Reusable HTTP client with retry logic for AA Points Monitor.

Provides a consistent interface for all HTTP operations across scrapers.
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from contextlib import asynccontextmanager

import httpx

from core.exceptions import (
    HttpClientError,
    RetryableError,
    RateLimitError,
    AuthenticationError,
    ServerError,
)

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 2.0

# Common headers for all requests
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
}


async def fetch_json(
    url: str,
    *,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: float = DEFAULT_RETRY_DELAY,
) -> Dict[str, Any]:
    """
    Fetch JSON data from a URL with automatic retry logic.

    Args:
        url: URL to fetch
        method: HTTP method (GET, POST, etc.)
        headers: Additional headers to include
        cookies: Cookies to include
        json_data: JSON body for POST requests
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Base delay between retries (exponential backoff)

    Returns:
        Parsed JSON response

    Raises:
        HttpClientError: On non-retryable errors
        RetryableError: After max retries exhausted
    """
    merged_headers = {**DEFAULT_HEADERS, **(headers or {})}

    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=merged_headers,
                    cookies=cookies,
                    json=json_data,
                )

                # Handle response status
                if response.status_code == 200:
                    return response.json()

                elif response.status_code == 429:
                    retry_after = response.headers.get('Retry-After')
                    raise RateLimitError(int(retry_after) if retry_after else None)

                elif response.status_code in (401, 403):
                    raise AuthenticationError(f"Auth failed: {response.status_code}")

                elif response.status_code >= 500:
                    raise ServerError(f"Server error: {response.status_code}")

                else:
                    raise HttpClientError(f"HTTP {response.status_code}: {response.text[:200]}")

        except (RateLimitError, ServerError) as e:
            if attempt < max_retries:
                delay = retry_delay * (2 ** attempt)
                if isinstance(e, RateLimitError) and e.retry_after:
                    delay = max(delay, e.retry_after)
                logger.warning(f"Retrying in {delay}s after: {e}")
                await asyncio.sleep(delay)
            else:
                raise

        except httpx.TimeoutException:
            if attempt < max_retries:
                delay = retry_delay * (2 ** attempt)
                logger.warning(f"Timeout, retrying in {delay}s...")
                await asyncio.sleep(delay)
            else:
                raise RetryableError(f"Timeout after {max_retries} retries")

        except httpx.RequestError as e:
            if attempt < max_retries:
                delay = retry_delay * (2 ** attempt)
                logger.warning(f"Request error, retrying in {delay}s: {e}")
                await asyncio.sleep(delay)
            else:
                raise HttpClientError(f"Request failed: {e}")

    raise RetryableError("Max retries exceeded")


@asynccontextmanager
async def create_client(
    *,
    timeout: float = DEFAULT_TIMEOUT,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
):
    """
    Create an async HTTP client context manager.

    Use this when you need to make multiple requests with the same session.

    Args:
        timeout: Request timeout in seconds
        headers: Additional headers to include
        cookies: Cookies to include

    Yields:
        httpx.AsyncClient instance

    Example:
        async with create_client(headers={'X-Custom': 'value'}) as client:
            response = await client.get(url1)
            response = await client.get(url2)
    """
    merged_headers = {**DEFAULT_HEADERS, **(headers or {})}

    async with httpx.AsyncClient(
        timeout=timeout,
        headers=merged_headers,
        cookies=cookies,
    ) as client:
        yield client


def create_sync_client(
    *,
    timeout: float = DEFAULT_TIMEOUT,
    headers: Optional[Dict[str, str]] = None,
) -> httpx.Client:
    """
    Create a synchronous HTTP client.

    Use for simple sync operations like the hotels scraper.

    Args:
        timeout: Request timeout in seconds
        headers: Additional headers to include

    Returns:
        httpx.Client instance (caller must close)
    """
    merged_headers = {**DEFAULT_HEADERS, **(headers or {})}
    return httpx.Client(timeout=timeout, headers=merged_headers)
