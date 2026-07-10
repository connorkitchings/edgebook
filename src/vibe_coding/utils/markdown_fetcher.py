"""Markdown URL fetcher with markdown.new integration.

This module provides a utility for fetching web content and converting it to
clean Markdown using markdown.new's Cloudflare-based conversion pipeline.

Features:
- 3-tier fallback: native Accept header → Workers AI → Browser Rendering
- Configurable conversion methods and options
- Retry logic with exponential backoff
- Comprehensive error handling
- Token count extraction from response headers

Example:
    >>> from vibe_coding.utils.markdown_fetcher import (
    ...     fetch_markdown,
    ...     MarkdownFetcherConfig,
    ... )
    >>> config = MarkdownFetcherConfig(method="auto", retain_images=True)
    >>> result = fetch_markdown("https://example.com", config)
    >>> print(result.content)
    >>> print(f"Tokens: {result.metadata.token_count}")
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Literal

import requests


class MarkdownFetchError(Exception):
    """Base exception for markdown fetching errors."""

    pass


class MarkdownTimeoutError(MarkdownFetchError):
    """Raised when a fetch request times out."""

    pass


class MarkdownRateLimitError(MarkdownFetchError):
    """Raised when markdown.new rate limit is exceeded."""

    pass


class MarkdownValidationError(MarkdownFetchError):
    """Raised when URL or configuration validation fails."""

    pass


@dataclass
class MarkdownMetadata:
    """Metadata from markdown fetch response."""

    token_count: int | None
    method_used: Literal["native", "ai", "browser"]
    status_code: int
    response_time_ms: float


@dataclass
class MarkdownResult:
    """Result from markdown fetch operation."""

    content: str
    metadata: MarkdownMetadata


@dataclass
class MarkdownFetcherConfig:
    """Configuration for markdown fetching operations.

    Attributes:
        method: Conversion method to use. "auto" tries all tiers in order.
        retain_images: Whether to keep images in the output.
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retry attempts for failed requests.
        backoff_factor: Exponential backoff multiplier for retries.
    """

    method: Literal["auto", "ai", "browser"] = "auto"
    retain_images: bool = False
    timeout: int = 30
    max_retries: int = 3
    backoff_factor: float = 2.0


def _validate_url(url: str) -> None:
    """Validate that a URL is properly formatted and uses a supported scheme.

    Args:
        url: URL to validate.

    Raises:
        MarkdownValidationError: If URL is invalid or uses unsupported scheme.
    """
    if not url or not isinstance(url, str):
        raise MarkdownValidationError("URL must be a non-empty string")

    url = url.strip()
    if not url:
        raise MarkdownValidationError("URL cannot be empty or whitespace only")

    unsupported_schemes = ("file://", "ftp://", "javascript:", "data:")
    if url.startswith(unsupported_schemes):
        scheme = url.split("://")[0] if "://" in url else url.split(":")[0]
        raise MarkdownValidationError(f"Unsupported URL scheme: {scheme}")

    if not url.startswith(("http://", "https://")):
        raise MarkdownValidationError("URL must use http:// or https:// scheme")


def _extract_token_count(headers: Any) -> int | None:
    """Extract token count from x-markdown-tokens header.

    Args:
        headers: Response headers dictionary.

    Returns:
        Token count as integer, or None if header not present or invalid.
    """
    for key in ["x-markdown-tokens", "X-Markdown-Tokens", "X-markdown-tokens"]:
        token_header = headers.get(key)
        if token_header:
            break
    else:
        token_header = None

    if not token_header:
        return None

    try:
        return int(token_header)
    except (ValueError, TypeError):
        return None


def _fetch_with_accept_header(
    url: str,
    config: MarkdownFetcherConfig,
    session: requests.Session,
) -> MarkdownResult | None:
    """Attempt fetch using native Accept: text/markdown header.

    This is the first tier in the fallback chain. It tries to fetch the URL
    with an Accept header requesting markdown content directly from servers
    that support Cloudflare Markdown for Agents.

    Args:
        url: URL to fetch.
        config: Fetcher configuration.
        session: Requests session to use.

    Returns:
        MarkdownResult if successful, None if markdown not available.

    Raises:
        MarkdownFetchError: For HTTP errors or other fetch issues.
    """
    try:
        start_time = time.time()
        response = session.get(
            url,
            headers={"Accept": "text/markdown"},
            timeout=config.timeout,
        )
        response_time_ms = (time.time() - start_time) * 1000

        if response.status_code == 429:
            raise MarkdownRateLimitError("Rate limit exceeded on native fetch")

        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "text/markdown" not in content_type.lower():
            return None

        token_count = _extract_token_count(response.headers)

        return MarkdownResult(
            content=response.text,
            metadata=MarkdownMetadata(
                token_count=token_count,
                method_used="native",
                status_code=response.status_code,
                response_time_ms=response_time_ms,
            ),
        )
    except requests.Timeout as e:
        raise MarkdownTimeoutError(f"Native fetch timeout: {e}") from e
    except requests.RequestException as e:
        raise MarkdownFetchError(f"Native fetch failed: {e}") from e


def _fetch_with_workers_ai(
    url: str,
    config: MarkdownFetcherConfig,
    session: requests.Session,
) -> MarkdownResult:
    """Fetch using markdown.new Workers AI conversion.

    This is the second tier in the fallback chain. It POSTs the URL to
    markdown.new which uses Cloudflare Workers AI to convert HTML to markdown.

    Args:
        url: URL to fetch and convert.
        config: Fetcher configuration.
        session: Requests session to use.

    Returns:
        MarkdownResult with converted content.

    Raises:
        MarkdownFetchError: For HTTP errors or other fetch issues.
    """
    try:
        start_time = time.time()
        response = session.post(
            "https://markdown.new/",
            json={"url": url, "method": "ai", "retain_images": config.retain_images},
            headers={"Content-Type": "application/json"},
            timeout=config.timeout,
        )
        response_time_ms = (time.time() - start_time) * 1000

        if response.status_code == 429:
            raise MarkdownRateLimitError("Rate limit exceeded on Workers AI")

        response.raise_for_status()

        token_count = _extract_token_count(response.headers)

        return MarkdownResult(
            content=response.text,
            metadata=MarkdownMetadata(
                token_count=token_count,
                method_used="ai",
                status_code=response.status_code,
                response_time_ms=response_time_ms,
            ),
        )
    except requests.Timeout as e:
        raise MarkdownTimeoutError(f"Workers AI timeout: {e}") from e
    except requests.RequestException as e:
        raise MarkdownFetchError(f"Workers AI failed: {e}") from e


def _fetch_with_browser_rendering(
    url: str,
    config: MarkdownFetcherConfig,
    session: requests.Session,
) -> MarkdownResult:
    """Fetch using markdown.new browser rendering.

    This is the third tier in the fallback chain. It POSTs the URL to
    markdown.new which uses Cloudflare Browser Rendering API for JS-heavy pages.

    Args:
        url: URL to fetch and convert.
        config: Fetcher configuration.
        session: Requests session to use.

    Returns:
        MarkdownResult with rendered and converted content.

    Raises:
        MarkdownFetchError: For HTTP errors or other fetch issues.
    """
    browser_timeout = max(config.timeout, 60)

    try:
        start_time = time.time()
        response = session.post(
            "https://markdown.new/",
            json={
                "url": url,
                "method": "browser",
                "retain_images": config.retain_images,
            },
            headers={"Content-Type": "application/json"},
            timeout=browser_timeout,
        )
        response_time_ms = (time.time() - start_time) * 1000

        if response.status_code == 429:
            raise MarkdownRateLimitError("Rate limit exceeded on browser rendering")

        response.raise_for_status()

        token_count = _extract_token_count(response.headers)

        return MarkdownResult(
            content=response.text,
            metadata=MarkdownMetadata(
                token_count=token_count,
                method_used="browser",
                status_code=response.status_code,
                response_time_ms=response_time_ms,
            ),
        )
    except requests.Timeout as e:
        raise MarkdownTimeoutError(f"Browser rendering timeout: {e}") from e
    except requests.RequestException as e:
        raise MarkdownFetchError(f"Browser rendering failed: {e}") from e


def _retry_with_backoff(
    func,
    url: str,
    config: MarkdownFetcherConfig,
    session: requests.Session,
) -> MarkdownResult:
    """Execute a fetch function with retry and exponential backoff.

    Args:
        func: Fetch function to execute.
        url: URL to fetch.
        config: Fetcher configuration.
        session: Requests session to use.

    Returns:
        MarkdownResult from successful fetch.

    Raises:
        MarkdownFetchError: If all retries are exhausted.
    """
    last_exception = None

    for attempt in range(config.max_retries):
        try:
            return func(url, config, session)
        except MarkdownRateLimitError as e:
            last_exception = e
            backoff = config.backoff_factor**attempt
            time.sleep(backoff)
        except (MarkdownTimeoutError, MarkdownFetchError):
            if attempt == config.max_retries - 1:
                raise
            backoff = config.backoff_factor**attempt
            time.sleep(backoff)

    raise MarkdownFetchError(
        f"All {config.max_retries} retries exhausted. Last error: {last_exception}"
    ) from last_exception


def fetch_markdown(
    url: str,
    config: MarkdownFetcherConfig | None = None,
) -> MarkdownResult:
    """Fetch URL and convert to Markdown using markdown.new.

    This function implements a 3-tier fallback strategy:
    1. Try native Accept: text/markdown header (fastest)
    2. Fallback to Workers AI conversion
    3. Final fallback to Browser Rendering (for JS-heavy pages)

    Args:
        url: URL to fetch and convert.
        config: Optional configuration. Uses defaults if not provided.

    Returns:
        MarkdownResult with content and metadata.

    Raises:
        MarkdownValidationError: If URL is invalid.
        MarkdownFetchError: If all fetch attempts fail.
        MarkdownTimeoutError: If all attempts timeout.

    Example:
        >>> config = MarkdownFetcherConfig(method="auto", retain_images=True)
        >>> result = fetch_markdown("https://example.com", config)
        >>> print(result.content)
    """
    if config is None:
        config = MarkdownFetcherConfig()

    _validate_url(url)

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (compatible; VibeCoding/1.0; +https://github.com/connorkitchings/Vibe-Coding)"
        }
    )

    try:
        if config.method == "auto":
            result = _retry_with_backoff(
                _fetch_with_accept_header, url, config, session
            )
            if result is not None:
                return result

            result = _retry_with_backoff(_fetch_with_workers_ai, url, config, session)
            return result

        elif config.method == "ai":
            return _retry_with_backoff(_fetch_with_workers_ai, url, config, session)

        elif config.method == "browser":
            return _retry_with_backoff(
                _fetch_with_browser_rendering, url, config, session
            )

        else:
            raise MarkdownValidationError(f"Invalid method: {config.method}")

    finally:
        session.close()
