"""Unit tests for content normalization and deduplication helpers."""

from kubeguide.ingest.dedup import (
    compute_content_hash,
    is_content_duplicate,
    normalize_document_text,
)


def test_normalize_document_text_line_endings() -> None:
    raw = "Line 1\r\nLine 2\rLine 3\n"
    normalized = normalize_document_text(raw)
    assert "\r" not in normalized
    assert normalized == "Line 1\nLine 2\nLine 3"


def test_normalize_document_text_collapses_excess_whitespace() -> None:
    raw = "Header   with    many   spaces\n\n\n\nBody paragraph."
    normalized = normalize_document_text(raw)
    assert normalized == "Header with many spaces\n\nBody paragraph."


def test_compute_content_hash_identical_across_whitespace_differences() -> None:
    text_a = "Kubernetes Pod Lifecycle\r\n\r\nDescribes pod states."
    text_b = "Kubernetes   Pod  Lifecycle\n\n\n\nDescribes  pod  states."

    hash_a = compute_content_hash(text_a)
    hash_b = compute_content_hash(text_b)

    assert hash_a == hash_b
    assert len(hash_a) == 64


def test_is_content_duplicate() -> None:
    seen: set[str] = set()
    text = "Deployment rolling update strategy."

    assert is_content_duplicate(text, seen) is False
    assert is_content_duplicate(text, seen) is True
    assert len(seen) == 1
