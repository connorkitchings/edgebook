# Markdown Fetcher Tool

The Markdown Fetcher is a utility for fetching web content and converting it to clean Markdown using [markdown.new](https://markdown.new/). This is particularly useful for AI agents that need structured data from web pages.

## Overview

The markdown_fetcher module provides a 3-tier fallback strategy for converting web content to Markdown:

1. **Tier 1 - Native Method**: Tries to fetch with `Accept: text/markdown` header (fastest)
2. **Tier 2 - Workers AI**: Uses Cloudflare Workers AI for HTML-to-Markdown conversion
3. **Tier 3 - Browser Rendering**: Uses Cloudflare Browser Rendering for JS-heavy pages

This approach provides up to **80% token reduction** compared to raw HTML.

## Installation

The markdown_fetcher is included in the Vibe Coding Template. Ensure dependencies are installed:

```bash
uv sync
```

The tool requires `requests>=2.31.0` which is already included in the template dependencies.

## Usage

### Basic Usage

```python
from vibe_coding.utils.markdown_fetcher import fetch_markdown

result = fetch_markdown("https://example.com")
print(result.content)
print(f"Tokens: {result.metadata.token_count}")
print(f"Method: {result.metadata.method_used}")
```

### Custom Configuration

```python
from vibe_coding.utils.markdown_fetcher import fetch_markdown, MarkdownFetcherConfig

config = MarkdownFetcherConfig(
    method="ai",           # Use only Workers AI
    retain_images=True,     # Keep images in output
    timeout=60,            # 60 second timeout
    max_retries=5,        # Retry up to 5 times
    backoff_factor=3.0,    # Exponential backoff multiplier
)

result = fetch_markdown("https://example.com", config)
```

### Configuration Options

| Parameter | Type | Default | Description |
|-----------|-------|----------|-------------|
| `method` | `"auto"`, `"ai"`, `"browser"` | `"auto"` | Conversion method to use. `"auto"` tries all tiers. |
| `retain_images` | bool | `False` | Whether to include images in the output. |
| `timeout` | int | `30` | Request timeout in seconds. Browser rendering uses minimum 60s. |
| `max_retries` | int | `3` | Maximum number of retry attempts for failed requests. |
| `backoff_factor` | float | `2.0` | Exponential backoff multiplier for retries. |

### Method Selection

- **`auto`** (default): Tries all three tiers in order
  - Best for general use
  - Fastest possible with fallbacks
  - Automatic handling of different page types

- **`ai`**: Only uses Workers AI
  - Good when you know the site doesn't support native markdown
  - Faster than browser rendering
  - May not work with heavily JavaScript-based pages

- **`browser`**: Only uses Browser Rendering
  - Best for JS-heavy single-page applications
  - Slowest but most reliable for complex pages
  - Minimum 60-second timeout

## Error Handling

The tool provides specific exception types for different failure scenarios:

```python
from vibe_coding.utils.markdown_fetcher import (
    fetch_markdown,
    MarkdownFetchError,
    MarkdownTimeoutError,
    MarkdownRateLimitError,
    MarkdownValidationError,
)

try:
    result = fetch_markdown("https://example.com")
except MarkdownValidationError as e:
    print(f"Invalid URL: {e}")
except MarkdownTimeoutError as e:
    print(f"Request timed out: {e}")
except MarkdownRateLimitError as e:
    print(f"Rate limit exceeded: {e}")
except MarkdownFetchError as e:
    print(f"Fetch failed: {e}")
```

### Exception Types

| Exception | When Raised | Typical Cause |
|------------|--------------|----------------|
| `MarkdownValidationError` | URL is malformed or uses unsupported scheme | Invalid URL, file://, javascript:, data: |
| `MarkdownTimeoutError` | Request exceeds timeout | Slow server, large page, network issues |
| `MarkdownRateLimitError` | markdown.new rate limit exceeded | Too many requests in short period |
| `MarkdownFetchError` | All retries exhausted | Persistent network/server errors |

## Examples

### Example 1: Fetch a Blog Post

```python
from vibe_coding.utils.markdown_fetcher import fetch_markdown

url = "https://blog.example.com/post/interesting-article"
result = fetch_markdown(url)

print(f"Content ({result.metadata.token_count} tokens):")
print(result.content[:500] + "...")
```

### Example 2: Fetch Documentation with Images

```python
from vibe_coding.utils.markdown_fetcher import fetch_markdown, MarkdownFetcherConfig

config = MarkdownFetcherConfig(retain_images=True)
result = fetch_markdown("https://docs.example.com", config)

print(f"Fetched using {result.metadata.method_used} method")
print(f"Response time: {result.metadata.response_time_ms:.0f}ms")
```

### Example 3: Retry Aggressive Retry for Unstable Sites

```python
from vibe_coding.utils.markdown_fetcher import fetch_markdown, MarkdownFetcherConfig

config = MarkdownFetcherConfig(
    max_retries=10,        # Try up to 10 times
    backoff_factor=1.5,      # Slower backoff
    timeout=90,              # Longer timeout
)

result = fetch_markdown("https://unstable.example.com", config)
```

### Example 4: Browser Rendering for SPA

```python
from vibe_coding.utils.markdown_fetcher import fetch_markdown, MarkdownFetcherConfig

config = MarkdownFetcherConfig(
    method="browser",     # Force browser rendering
    timeout=120,           # 2 minute timeout for complex pages
)

result = fetch_markdown("https://react-app.example.com", config)
```

## Advanced Usage

### Accessing Metadata

```python
result = fetch_markdown("https://example.com")

metadata = result.metadata
print(f"Tokens: {metadata.token_count}")
print(f"Method: {metadata.method_used}")
print(f"Status: {metadata.status_code}")
print(f"Response time: {metadata.response_time_ms:.0f}ms")
```

### Custom Retry Strategy

For rate-limited APIs or unstable sites, configure aggressive retry:

```python
config = MarkdownFetcherConfig(
    max_retries=5,        # More retries
    backoff_factor=4.0,      # Faster backoff growth
)

result = fetch_markdown("https://rate-limited.com", config)
```

## Performance Considerations

### Token Efficiency

- **Native markdown**: Fastest, no conversion needed
- **Workers AI**: ~100-200ms additional latency
- **Browser Rendering**: ~1-3s additional latency

Choose the method that balances speed and accuracy for your use case.

### Timeout Guidelines

| Page Type | Recommended Method | Timeout |
|------------|-------------------|----------|
| Static HTML | `auto` or `ai` | 30s |
| Dynamic with some JS | `auto` | 45s |
| Heavy SPA/React/Vue | `browser` | 90-120s |

## Troubleshooting

### "Rate limit exceeded" errors

**Problem**: Receiving `MarkdownRateLimitError`

**Solutions**:
1. Increase `backoff_factor` for longer delays between retries
2. Add delays between fetches in your application
3. Implement request queuing or caching

### Timeout errors

**Problem**: `MarkdownTimeoutError` on complex pages

**Solutions**:
1. Increase `timeout` value (especially for `browser` method)
2. Switch to `browser` method for JS-heavy pages
3. Check network connectivity

### SSL/Certificate errors

**Problem**: SSL verification failures

**Solutions**:
1. The tool uses system certificates - ensure they're up to date
2. For development only, you can disable verification (not recommended for production)

### Empty or incorrect content

**Problem**: Content doesn't match expected page

**Solutions**:
1. Check if the page requires JavaScript - use `method="browser"`
2. Verify the URL is correct and publicly accessible
3. Check `result.metadata.method_used` to see which tier succeeded

## Testing

The module includes comprehensive tests with 95% coverage:

```bash
# Run all markdown fetcher tests
uv run pytest tests/utils/test_markdown_fetcher.py -v

# Run with coverage
uv run pytest tests/utils/test_markdown_fetcher.py --cov=vibe_coding.utils.markdown_fetcher
```

## Architecture Decision

See [ADR-001: Markdown.new Integration](../architecture/adr/001-markdown-new-integration.md) for the decision to use markdown.new as an external-only dependency.

## Related Tools

- **Web Scraping**: For more complex scraping needs, consider `scrapy` or `beautifulsoup4`
- **HTML Parsing**: The tool handles HTML-to-Markdown conversion automatically
- **Caching**: Consider adding local caching for frequently accessed URLs

## Limitations

1. **External Dependency**: Requires internet connectivity to markdown.new
2. **Rate Limits**: markdown.new may rate limit excessive requests
3. **JavaScript**: Only `browser` method fully handles client-side rendering
4. **Authentication**: Does not currently support authenticated requests
5. **Cookies/Sessions**: Does not maintain session state across requests

## Future Enhancements

Potential improvements for future versions:

- [ ] Local fallback using `html2text` or similar
- [ ] Request caching to avoid repeated fetches
- [ ] Support for authenticated requests
- [ ] Session management for cookie-based auth
- [ ] Batch fetching multiple URLs
- [ ] Custom headers support for API keys

## References

- [markdown.new Documentation](https://markdown.new/)
- [Cloudflare Workers AI](https://developers.cloudflare.com/workers-ai/)
- [Cloudflare Browser Rendering](https://developers.cloudflare.com/browser-rendering/)

---

**Last Updated**: 2026-02-15
**Version**: 1.0.0
