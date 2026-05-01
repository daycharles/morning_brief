"""Shared HTTP client utility for the Morning Brief system.

Enforces HTTPS, 10-second timeouts, and 2-retry exponential backoff.
"""
import logging
import time

import requests

logger = logging.getLogger(__name__)

_RETRY_DELAYS = (1, 2)  # seconds to sleep before retry 1 and retry 2


def get(
    url: str,
    *,
    headers: dict = None,
    params: dict = None,
    timeout: int = 10,
) -> dict:
    """Perform an HTTPS GET request with retry logic.

    Args:
        url: Full HTTPS URL to request. Raises ValueError for http:// URLs.
        headers: Optional HTTP headers to include in the request.
        params: Optional query parameters dict.
        timeout: Request timeout in seconds (default: 10).

    Returns:
        Parsed JSON response as a dict.

    Raises:
        ValueError: If url does not start with 'https://'.
        requests.HTTPError: On non-2xx response after exhausting retries,
            or immediately on HTTP 429 (rate limit).
        requests.ConnectionError: If connection fails after exhausting retries.
        requests.Timeout: If request times out after exhausting retries.
    """
    if not url.startswith("https://"):
        raise ValueError(
            f"HTTPS enforcement: URL must start with 'https://', got: {url!r}"
        )

    session = requests.Session()
    last_exception = None

    for attempt in range(3):  # attempt 0, 1, 2 (2 retries after initial)
        try:
            response = session.get(
                url, headers=headers, params=params, timeout=timeout
            )

            # HTTP 429 — rate limited: non-retryable
            if response.status_code == 429:
                logger.warning("Rate limit hit for %s", url)
                response.raise_for_status()

            # HTTP 5xx — server error: retryable
            if response.status_code >= 500:
                error = requests.HTTPError(
                    f"Server error {response.status_code}", response=response
                )
                raise error

            # All other non-2xx: raise immediately (4xx etc)
            response.raise_for_status()

            return response.json()

        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as exc:
            # Don't retry 429 or 4xx errors
            if isinstance(exc, requests.HTTPError):
                if exc.response is not None and exc.response.status_code == 429:
                    raise
                if exc.response is not None and exc.response.status_code < 500:
                    raise

            last_exception = exc
            if attempt < 2:
                delay = _RETRY_DELAYS[attempt]
                logger.warning(
                    "Retry %d/2 for %s: %s — sleeping %ds",
                    attempt + 1,
                    url,
                    exc,
                    delay,
                )
                time.sleep(delay)

    raise last_exception
