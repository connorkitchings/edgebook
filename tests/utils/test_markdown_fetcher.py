"""Tests for markdown_fetcher module."""

from unittest.mock import Mock, patch

import pytest
import requests

from vibe_coding.utils.markdown_fetcher import (
    MarkdownFetcherConfig,
    MarkdownFetchError,
    MarkdownMetadata,
    MarkdownRateLimitError,
    MarkdownResult,
    MarkdownTimeoutError,
    MarkdownValidationError,
    _extract_token_count,
    _fetch_with_accept_header,
    _fetch_with_browser_rendering,
    _fetch_with_workers_ai,
    _retry_with_backoff,
    _validate_url,
    fetch_markdown,
)


class TestMarkdownFetcherConfig:
    """Tests for MarkdownFetcherConfig dataclass."""

    def test_default_config(self):
        config = MarkdownFetcherConfig()
        assert config.method == "auto"
        assert config.retain_images is False
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.backoff_factor == 2.0

    def test_custom_config(self):
        config = MarkdownFetcherConfig(
            method="ai",
            retain_images=True,
            timeout=60,
            max_retries=5,
            backoff_factor=3.0,
        )
        assert config.method == "ai"
        assert config.retain_images is True
        assert config.timeout == 60
        assert config.max_retries == 5
        assert config.backoff_factor == 3.0


class TestMarkdownMetadata:
    """Tests for MarkdownMetadata dataclass."""

    def test_metadata_creation(self):
        metadata = MarkdownMetadata(
            token_count=1000,
            method_used="native",
            status_code=200,
            response_time_ms=150.5,
        )
        assert metadata.token_count == 1000
        assert metadata.method_used == "native"
        assert metadata.status_code == 200
        assert metadata.response_time_ms == 150.5

    def test_metadata_none_token_count(self):
        metadata = MarkdownMetadata(
            token_count=None,
            method_used="ai",
            status_code=200,
            response_time_ms=200.0,
        )
        assert metadata.token_count is None


class TestMarkdownResult:
    """Tests for MarkdownResult dataclass."""

    def test_result_creation(self):
        metadata = MarkdownMetadata(
            token_count=500,
            method_used="browser",
            status_code=200,
            response_time_ms=300.0,
        )
        result = MarkdownResult(content="# Test", metadata=metadata)
        assert result.content == "# Test"
        assert result.metadata.token_count == 500


class TestValidateUrl:
    """Tests for _validate_url function."""

    def test_valid_http_url(self):
        _validate_url("http://example.com")

    def test_valid_https_url(self):
        _validate_url("https://example.com")

    def test_valid_url_with_path(self):
        _validate_url("https://example.com/path/to/page")

    def test_valid_url_with_query_params(self):
        _validate_url("https://example.com?key=value&other=test")

    def test_valid_url_with_fragment(self):
        _validate_url("https://example.com#section")

    def test_empty_url_raises_error(self):
        with pytest.raises(MarkdownValidationError, match="must be a non-empty string"):
            _validate_url("")

    def test_whitespace_only_url_raises_error(self):
        with pytest.raises(MarkdownValidationError, match="cannot be empty"):
            _validate_url("   ")

    def test_non_string_url_raises_error(self):
        with pytest.raises(MarkdownValidationError, match="must be a non-empty string"):
            _validate_url(None)  # type: ignore[arg-type]

    def test_invalid_scheme_raises_error(self):
        with pytest.raises(
            MarkdownValidationError, match="Unsupported URL scheme: ftp"
        ):
            _validate_url("ftp://example.com")

    def test_file_scheme_raises_error(self):
        with pytest.raises(MarkdownValidationError, match="Unsupported URL scheme"):
            _validate_url("file:///path/to/file")

    def test_javascript_scheme_raises_error(self):
        with pytest.raises(MarkdownValidationError, match="Unsupported URL scheme"):
            _validate_url("javascript:void(0)")

    def test_data_scheme_raises_error(self):
        with pytest.raises(MarkdownValidationError, match="Unsupported URL scheme"):
            _validate_url("data:text/plain,test")


class TestExtractTokenCount:
    """Tests for _extract_token_count function."""

    def test_extract_token_count_present(self):
        headers = {"x-markdown-tokens": "1234"}
        assert _extract_token_count(headers) == 1234

    def test_extract_token_count_case_insensitive(self):
        headers = {"X-Markdown-Tokens": "5678"}
        assert _extract_token_count(headers) == 5678

    def test_extract_token_count_missing(self):
        headers = {"content-type": "text/markdown"}
        assert _extract_token_count(headers) is None

    def test_extract_token_count_invalid_value(self):
        headers = {"x-markdown-tokens": "not-a-number"}
        assert _extract_token_count(headers) is None

    def test_extract_token_count_empty_string(self):
        headers = {"x-markdown-tokens": ""}
        assert _extract_token_count(headers) is None


class TestFetchWithAcceptHeader:
    """Tests for _fetch_with_accept_header function."""

    @patch("vibe_coding.utils.markdown_fetcher.time.time")
    def test_successful_native_fetch(self, mock_time):
        mock_time.side_effect = [0.0, 0.1]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            "content-type": "text/markdown; charset=utf-8",
            "x-markdown-tokens": "1000",
        }
        mock_response.text = "# Test Content"
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.get.return_value = mock_response

        config = MarkdownFetcherConfig()
        result = _fetch_with_accept_header("https://example.com", config, mock_session)

        assert result is not None
        assert result.content == "# Test Content"
        assert result.metadata.token_count == 1000
        assert result.metadata.method_used == "native"
        assert result.metadata.status_code == 200
        assert result.metadata.response_time_ms == 100.0

        mock_session.get.assert_called_once_with(
            "https://example.com",
            headers={"Accept": "text/markdown"},
            timeout=30,
        )

    @patch("vibe_coding.utils.markdown_fetcher.time.time")
    def test_returns_none_when_not_markdown(self, mock_time):
        mock_time.side_effect = [0.0, 0.1]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.get.return_value = mock_response

        config = MarkdownFetcherConfig()
        result = _fetch_with_accept_header("https://example.com", config, mock_session)

        assert result is None

    def test_timeout_raises_error(self):
        mock_session = Mock()
        mock_session.get.side_effect = requests.Timeout()

        config = MarkdownFetcherConfig()
        with pytest.raises(MarkdownTimeoutError, match="Native fetch timeout"):
            _fetch_with_accept_header("https://example.com", config, mock_session)

    def test_http_error_raises_fetch_error(self):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

        mock_session = Mock()
        mock_session.get.return_value = mock_response

        config = MarkdownFetcherConfig()
        with pytest.raises(MarkdownFetchError, match="Native fetch failed"):
            _fetch_with_accept_header("https://example.com", config, mock_session)

    @patch("vibe_coding.utils.markdown_fetcher.time.time")
    def test_rate_limit_error(self, mock_time):
        mock_time.side_effect = [0.0, 0.1]

        mock_response = Mock()
        mock_response.status_code = 429

        mock_session = Mock()
        mock_session.get.return_value = mock_response

        config = MarkdownFetcherConfig()
        with pytest.raises(MarkdownRateLimitError):
            _fetch_with_accept_header("https://example.com", config, mock_session)


class TestFetchWithWorkersAI:
    """Tests for _fetch_with_workers_ai function."""

    @patch("vibe_coding.utils.markdown_fetcher.time.time")
    def test_successful_workers_ai_fetch(self, mock_time):
        mock_time.side_effect = [0.0, 0.2]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            "content-type": "text/markdown; charset=utf-8",
            "x-markdown-tokens": "2500",
        }
        mock_response.text = "# Converted Content"
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.post.return_value = mock_response

        config = MarkdownFetcherConfig(method="ai")
        result = _fetch_with_workers_ai("https://example.com", config, mock_session)

        assert result.content == "# Converted Content"
        assert result.metadata.token_count == 2500
        assert result.metadata.method_used == "ai"
        assert result.metadata.status_code == 200
        assert result.metadata.response_time_ms == 200.0

        mock_session.post.assert_called_once_with(
            "https://markdown.new/",
            json={
                "url": "https://example.com",
                "method": "ai",
                "retain_images": False,
            },
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

    @patch("vibe_coding.utils.markdown_fetcher.time.time")
    def test_workers_ai_with_retain_images(self, mock_time):
        mock_time.side_effect = [0.0, 0.2]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            "content-type": "text/markdown; charset=utf-8",
        }
        mock_response.text = "# Content with Images"
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.post.return_value = mock_response

        config = MarkdownFetcherConfig(method="ai", retain_images=True)
        result = _fetch_with_workers_ai("https://example.com", config, mock_session)

        assert result is not None
        mock_session.post.assert_called_once()
        call_kwargs = mock_session.post.call_args[1]
        assert call_kwargs["json"]["retain_images"] is True

    def test_workers_ai_timeout_raises_error(self):
        mock_session = Mock()
        mock_session.post.side_effect = requests.Timeout()

        config = MarkdownFetcherConfig(method="ai")
        with pytest.raises(MarkdownTimeoutError, match="Workers AI timeout"):
            _fetch_with_workers_ai("https://example.com", config, mock_session)

    @patch("vibe_coding.utils.markdown_fetcher.time.time")
    def test_workers_ai_rate_limit_error(self, mock_time):
        mock_time.side_effect = [0.0, 0.2]

        mock_response = Mock()
        mock_response.status_code = 429

        mock_session = Mock()
        mock_session.post.return_value = mock_response

        config = MarkdownFetcherConfig(method="ai")
        with pytest.raises(MarkdownRateLimitError):
            _fetch_with_workers_ai("https://example.com", config, mock_session)


class TestFetchWithBrowserRendering:
    """Tests for _fetch_with_browser_rendering function."""

    @patch("vibe_coding.utils.markdown_fetcher.time.time")
    def test_successful_browser_rendering_fetch(self, mock_time):
        mock_time.side_effect = [0.0, 1.5]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            "content-type": "text/markdown; charset=utf-8",
            "x-markdown-tokens": "3000",
        }
        mock_response.text = "# Rendered Content"
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.post.return_value = mock_response

        config = MarkdownFetcherConfig(method="browser")
        result = _fetch_with_browser_rendering(
            "https://example.com", config, mock_session
        )

        assert result.content == "# Rendered Content"
        assert result.metadata.token_count == 3000
        assert result.metadata.method_used == "browser"
        assert result.metadata.status_code == 200
        assert result.metadata.response_time_ms == 1500.0

        mock_session.post.assert_called_once_with(
            "https://markdown.new/",
            json={
                "url": "https://example.com",
                "method": "browser",
                "retain_images": False,
            },
            headers={"Content-Type": "application/json"},
            timeout=60,
        )

    def test_browser_rendering_timeout_minimum(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/markdown; charset=utf-8"}
        mock_response.text = "# Content"
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.post.return_value = mock_response

        config = MarkdownFetcherConfig(timeout=30)
        _fetch_with_browser_rendering("https://example.com", config, mock_session)

        mock_session.post.assert_called_once_with(
            "https://markdown.new/",
            json={
                "url": "https://example.com",
                "method": "browser",
                "retain_images": False,
            },
            headers={"Content-Type": "application/json"},
            timeout=60,
        )

    def test_browser_rendering_timeout_raises_error(self):
        mock_session = Mock()
        mock_session.post.side_effect = requests.Timeout()

        config = MarkdownFetcherConfig(method="browser")
        with pytest.raises(MarkdownTimeoutError, match="Browser rendering timeout"):
            _fetch_with_browser_rendering("https://example.com", config, mock_session)


class TestRetryWithBackoff:
    """Tests for _retry_with_backoff function."""

    @patch("vibe_coding.utils.markdown_fetcher.time.sleep")
    def test_successful_on_first_attempt(self, mock_sleep):
        mock_func = Mock()
        mock_result = Mock()
        mock_func.return_value = mock_result

        config = MarkdownFetcherConfig(max_retries=3)
        result = _retry_with_backoff(mock_func, "https://example.com", config, Mock())

        assert result == mock_result
        mock_sleep.assert_not_called()
        assert mock_func.call_count == 1

    @patch("vibe_coding.utils.markdown_fetcher.time.sleep")
    def test_retry_on_rate_limit(self, mock_sleep):
        mock_func = Mock()
        mock_result = Mock()

        mock_func.side_effect = [
            MarkdownRateLimitError("Rate limited"),
            MarkdownRateLimitError("Rate limited again"),
            mock_result,
        ]

        config = MarkdownFetcherConfig(max_retries=3, backoff_factor=2.0)
        result = _retry_with_backoff(mock_func, "https://example.com", config, Mock())

        assert result == mock_result
        assert mock_func.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("vibe_coding.utils.markdown_fetcher.time.sleep")
    def test_exhausted_retries_raises_error(self, mock_sleep):
        mock_func = Mock()
        mock_func.side_effect = MarkdownRateLimitError("Always rate limited")

        config = MarkdownFetcherConfig(max_retries=2, backoff_factor=2.0)

        with pytest.raises(MarkdownFetchError, match="All 2 retries exhausted"):
            _retry_with_backoff(mock_func, "https://example.com", config, Mock())

        assert mock_func.call_count == 2
        assert mock_sleep.call_count == 2

    @patch("vibe_coding.utils.markdown_fetcher.time.sleep")
    def test_retry_on_timeout(self, mock_sleep):
        mock_func = Mock()
        mock_result = Mock()

        mock_func.side_effect = [
            MarkdownTimeoutError("Timeout"),
            mock_result,
        ]

        config = MarkdownFetcherConfig(max_retries=3, backoff_factor=2.0)
        result = _retry_with_backoff(mock_func, "https://example.com", config, Mock())

        assert result == mock_result
        assert mock_func.call_count == 2
        assert mock_sleep.call_count == 1


class TestFetchMarkdown:
    """Tests for fetch_markdown function (integration tests)."""

    @patch("vibe_coding.utils.markdown_fetcher._fetch_with_accept_header")
    @patch("vibe_coding.utils.markdown_fetcher._fetch_with_workers_ai")
    def test_auto_method_successful_native(self, mock_workers_ai, mock_native):
        mock_result = MarkdownResult(
            content="# Native",
            metadata=MarkdownMetadata(
                token_count=100,
                method_used="native",
                status_code=200,
                response_time_ms=50,
            ),
        )
        mock_native.return_value = mock_result

        result = fetch_markdown("https://example.com")

        assert result.content == "# Native"
        mock_native.assert_called_once()
        mock_workers_ai.assert_not_called()

    @patch("vibe_coding.utils.markdown_fetcher._fetch_with_accept_header")
    @patch("vibe_coding.utils.markdown_fetcher._fetch_with_workers_ai")
    def test_auto_method_fallback_to_workers_ai(self, mock_workers_ai, mock_native):
        mock_native.return_value = None

        mock_result = MarkdownResult(
            content="# AI",
            metadata=MarkdownMetadata(
                token_count=200, method_used="ai", status_code=200, response_time_ms=100
            ),
        )
        mock_workers_ai.return_value = mock_result

        result = fetch_markdown("https://example.com")

        assert result.content == "# AI"
        assert result.metadata.method_used == "ai"

    @patch("vibe_coding.utils.markdown_fetcher._fetch_with_workers_ai")
    def test_ai_method(self, mock_workers_ai):
        mock_result = MarkdownResult(
            content="# AI",
            metadata=MarkdownMetadata(
                token_count=300, method_used="ai", status_code=200, response_time_ms=150
            ),
        )
        mock_workers_ai.return_value = mock_result

        config = MarkdownFetcherConfig(method="ai")
        result = fetch_markdown("https://example.com", config)

        assert result.content == "# AI"
        assert result.metadata.method_used == "ai"

    @patch("vibe_coding.utils.markdown_fetcher._fetch_with_browser_rendering")
    def test_browser_method(self, mock_browser):
        mock_result = MarkdownResult(
            content="# Browser",
            metadata=MarkdownMetadata(
                token_count=400,
                method_used="browser",
                status_code=200,
                response_time_ms=200,
            ),
        )
        mock_browser.return_value = mock_result

        config = MarkdownFetcherConfig(method="browser")
        result = fetch_markdown("https://example.com", config)

        assert result.content == "# Browser"
        assert result.metadata.method_used == "browser"

    def test_invalid_url_raises_error(self):
        with pytest.raises(
            MarkdownValidationError, match="Unsupported URL scheme: ftp"
        ):
            fetch_markdown("ftp://example.com")

    def test_empty_url_raises_error(self):
        with pytest.raises(MarkdownValidationError, match="must be a non-empty string"):
            fetch_markdown("")

    @patch("vibe_coding.utils.markdown_fetcher._fetch_with_workers_ai")
    def test_custom_config(self, mock_workers_ai):
        mock_result = MarkdownResult(
            content="# Custom",
            metadata=MarkdownMetadata(
                token_count=500, method_used="ai", status_code=200, response_time_ms=250
            ),
        )
        mock_workers_ai.return_value = mock_result

        config = MarkdownFetcherConfig(method="ai", retain_images=True, timeout=60)
        result = fetch_markdown("https://example.com", config)

        assert result is not None
        mock_workers_ai.assert_called_once()
        call_args = mock_workers_ai.call_args[0]
        assert call_args[1].retain_images is True
        assert call_args[1].timeout == 60

    @patch("vibe_coding.utils.markdown_fetcher._fetch_with_accept_header")
    @patch("vibe_coding.utils.markdown_fetcher._fetch_with_workers_ai")
    def test_session_cleanup(self, mock_workers_ai, mock_accept):
        mock_result = MarkdownResult(
            content="# Test",
            metadata=MarkdownMetadata(
                token_count=100, method_used="ai", status_code=200, response_time_ms=50
            ),
        )
        mock_accept.return_value = None
        mock_workers_ai.return_value = mock_result

        result = fetch_markdown("https://example.com")

        assert result is not None
        assert result.content == "# Test"

    @patch("vibe_coding.utils.markdown_fetcher._fetch_with_accept_header")
    @patch("vibe_coding.utils.markdown_fetcher._fetch_with_workers_ai")
    def test_session_closed_on_error(self, mock_workers_ai, mock_accept):
        mock_session = Mock()
        mock_session.close = Mock()

        mock_accept.return_value = None
        mock_workers_ai.side_effect = MarkdownFetchError("Test error")

        with patch("requests.Session", return_value=mock_session):
            with pytest.raises(MarkdownFetchError):
                fetch_markdown("https://example.com")

        mock_session.close.assert_called_once()
