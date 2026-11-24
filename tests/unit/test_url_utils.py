"""Unit tests for URL validation and normalization utilities."""

from kubeguide.ingest.url_utils import (
    extract_domain,
    is_valid_http_url,
    sanitize_url_for_manifest,
)


def test_is_valid_http_url() -> None:
    assert is_valid_http_url("https://kubernetes.io/docs/concepts/") is True
    assert is_valid_http_url("http://localhost:8000/health") is True
    assert is_valid_http_url("ftp://ftp.example.com/file.txt") is False
    assert is_valid_http_url("not a url") is False
    assert is_valid_http_url("") is False


def test_extract_domain() -> None:
    assert extract_domain("https://Kubernetes.IO/docs/") == "kubernetes.io"
    assert extract_domain("http://api.staging.cluster.local:8080/v1") == "api.staging.cluster.local"
    assert extract_domain("invalid-url") == ""


def test_sanitize_url_for_manifest() -> None:
    url_with_params = "https://kubernetes.io/docs/concepts/workloads/?ref=docs&user=sre#lifecycle"
    sanitized = sanitize_url_for_manifest(url_with_params)

    assert sanitized == "https://kubernetes.io/docs/concepts/workloads/"
    assert "?" not in sanitized
    assert "#" not in sanitized


def test_sanitize_url_root_fallback() -> None:
    url = "https://kubernetes.io"
    assert sanitize_url_for_manifest(url) == "https://kubernetes.io/"
