"""
Async HTTP client with retry logic for US Hotel Scraper.

Provides a consistent interface for all HTTP operations.
"""

import asyncio
import logging
import random
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

import httpx

from .exceptions import (
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
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
}


async def random_delay(min_sec: float = 0.5, max_sec: float = 1.5):
    """Add random async delay for rate limiting."""
    delay = random.uniform(min_sec, max_sec)
    await asyncio.sleep(delay)


async def fetch_json(
    url: str,
    *,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
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
        params: Query parameters
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
                    params=params,
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
                    raise HttpClientError(
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )

        except (RateLimitError, ServerError) as e:
            if attempt < max_retries:
                delay = retry_delay * (2 ** attempt)
                if isinstance(e, RateLimitError) and e.retry_after:
                    delay = max(delay, e.retry_after)
                logger.warning(f"Retrying in {delay:.1f}s after: {e}")
                await asyncio.sleep(delay)
            else:
                raise

        except httpx.TimeoutException:
            if attempt < max_retries:
                delay = retry_delay * (2 ** attempt)
                logger.warning(f"Timeout, retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
            else:
                raise RetryableError(f"Timeout after {max_retries} retries")

        except httpx.RequestError as e:
            if attempt < max_retries:
                delay = retry_delay * (2 ** attempt)
                logger.warning(f"Request error, retrying in {delay:.1f}s: {e}")
                await asyncio.sleep(delay)
            else:
                raise HttpClientError(f"Request failed: {e}")

    raise RetryableError("Max retries exceeded")


@asynccontextmanager
async def create_client(
    *,
    timeout: float = DEFAULT_TIMEOUT,
    headers: Optional[Dict[str, str]] = None,
):
    """
    Create an async HTTP client context manager.

    Use this when you need to make multiple requests with the same session.

    Args:
        timeout: Request timeout in seconds
        headers: Additional headers to include

    Yields:
        httpx.AsyncClient instance
    """
    merged_headers = {**DEFAULT_HEADERS, **(headers or {})}

    async with httpx.AsyncClient(
        timeout=timeout,
        headers=merged_headers,
        follow_redirects=True,
    ) as client:
        yield client


async def fetch_with_client(
    client: httpx.AsyncClient,
    url: str,
    *,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: float = DEFAULT_RETRY_DELAY,
) -> Optional[Dict[str, Any]]:
    """
    Fetch JSON using an existing client with retry logic.

    Returns None on failure instead of raising.

    Args:
        client: Existing httpx.AsyncClient
        url: URL to fetch
        method: HTTP method
        params: Query parameters
        max_retries: Maximum retries
        retry_delay: Base delay between retries

    Returns:
        Parsed JSON or None on failure
    """
    for attempt in range(max_retries + 1):
        try:
            response = await client.request(method=method, url=url, params=params)

            if response.status_code == 200:
                return response.json()

            elif response.status_code == 429:
                if attempt < max_retries:
                    delay = retry_delay * (2 ** attempt)
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        delay = max(delay, int(retry_after))
                    logger.warning(f"Rate limited, retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Rate limited after {max_retries} retries")
                    return None

            elif response.status_code >= 500:
                if attempt < max_retries:
                    delay = retry_delay * (2 ** attempt)
                    logger.warning(f"Server error {response.status_code}, retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Server error after {max_retries} retries")
                    return None

            else:
                logger.debug(f"Request failed: {response.status_code}")
                return None

        except httpx.TimeoutException:
            if attempt < max_retries:
                delay = retry_delay * (2 ** attempt)
                logger.warning(f"Timeout, retrying in {delay:.1f}s")
                await asyncio.sleep(delay)
            else:
                logger.error(f"Timeout after {max_retries} retries")
                return None

        except httpx.RequestError as e:
            if attempt < max_retries:
                delay = retry_delay * (2 ** attempt)
                logger.warning(f"Request error: {e}, retrying in {delay:.1f}s")
                await asyncio.sleep(delay)
            else:
                logger.error(f"Request error after {max_retries} retries: {e}")
                return None

    return None
