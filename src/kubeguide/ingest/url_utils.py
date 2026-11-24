"""URL validation and sanitization utilities for corpus ingestion."""

from urllib.parse import urlparse, urlunparse


def is_valid_http_url(url: str) -> bool:
    """Check whether a URL is a valid HTTP or HTTPS address with a host."""
    try:
        parsed = urlparse(url.strip())
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except (ValueError, AttributeError):
        return False


def extract_domain(url: str) -> str:
    """Extract lower-cased network domain hostname from URL."""
    parsed = urlparse(url.strip())
    return parsed.hostname.lower() if parsed.hostname else ""


def sanitize_url_for_manifest(url: str) -> str:
    """Sanitize URL by stripping query parameters and hash fragments."""
    parsed = urlparse(url.strip())
    path = parsed.path
    # Standardize empty path to /
    if not path:
        path = "/"
    sanitized = parsed._replace(params="", query="", fragment="", path=path)
    return urlunparse(sanitized)
