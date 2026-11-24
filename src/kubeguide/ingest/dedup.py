"""Content hashing and deduplication utilities for corpus ingestion."""

import hashlib
import re

_WHITESPACE_REGEX = re.compile(r"[ \t]+")
_CONSECUTIVE_NEWLINES_REGEX = re.compile(r"\n{3,}")


def normalize_document_text(raw_text: str) -> str:
    """Normalize text by standardizing line endings and collapsing excess blank lines."""
    # Convert CRLF to LF
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse multiple consecutive inline spaces/tabs
    text = _WHITESPACE_REGEX.sub(" ", text)
    # Collapse 3 or more newlines into 2
    text = _CONSECUTIVE_NEWLINES_REGEX.sub("\n\n", text)
    return text.strip()


def compute_content_hash(text: str) -> str:
    """Calculate the SHA-256 fingerprint of normalized text content."""
    normalized = normalize_document_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def is_content_duplicate(text: str, seen_hashes: set[str]) -> bool:
    """Determine whether text has already been seen based on content hash.

    If not duplicate, adds the calculated hash into seen_hashes.
    """
    content_hash = compute_content_hash(text)
    if content_hash in seen_hashes:
        return True
    seen_hashes.add(content_hash)
    return False
