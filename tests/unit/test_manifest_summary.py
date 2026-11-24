"""Unit tests for manifest summary script."""

import json
from pathlib import Path

from scripts.manifest_summary import summarize_manifest


def test_summarize_manifest_missing_file(tmp_path: Path) -> None:
    non_existent = tmp_path / "missing.jsonl"
    stats = summarize_manifest(non_existent)

    assert stats["total_files"] == 0
    assert stats["total_bytes"] == 0
    assert stats["total_pages"] == 0
    assert stats["sources"] == {}


def test_summarize_manifest_valid_records(tmp_path: Path) -> None:
    manifest_file = tmp_path / "test_manifest.jsonl"
    records = [
        {
            "rel_path": "k8s/doc1.md",
            "source": "k8s-docs",
            "bytes": 2048,
            "pages": 2,
        },
        {
            "rel_path": "k8s/doc2.md",
            "source": "k8s-docs",
            "bytes": 4096,
            "pages": 4,
        },
        {
            "rel_path": "web/page1.html",
            "source": "kubernetes-io",
            "bytes": 1024,
            "pages": 1,
        },
    ]

    with manifest_file.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")

    stats = summarize_manifest(manifest_file)

    assert stats["total_files"] == 3
    assert stats["total_bytes"] == 7168
    assert stats["total_pages"] == 7
    sources = stats["sources"]
    assert isinstance(sources, dict)
    assert sources["k8s-docs"]["files"] == 2
    assert sources["k8s-docs"]["bytes"] == 6144
    assert sources["k8s-docs"]["pages"] == 6
    assert sources["kubernetes-io"]["files"] == 1
