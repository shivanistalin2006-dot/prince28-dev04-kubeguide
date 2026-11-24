"""Unit tests for scripts/parse_corpus.py argument parsing."""

from pathlib import Path

from scripts.parse_corpus import build_arg_parser


def test_build_arg_parser_defaults() -> None:
    parser = build_arg_parser()
    args = parser.parse_args([])
    assert args.limit is None
    assert args.retry_failed is False
    assert args.force is False
    assert args.ocr is None
    assert args.pdf_parser == "pymupdf"
    assert args.show_failures is False
    assert args.manifest == Path("data/manifest.jsonl")


def test_build_arg_parser_custom_flags() -> None:
    parser = build_arg_parser()
    args = parser.parse_args(
        [
            "--limit",
            "50",
            "--retry-failed",
            "--force",
            "--ocr",
            "fra",
            "--pdf-parser",
            "pypdf",
            "--show-failures",
            "--manifest",
            "data/custom_manifest.jsonl",
        ]
    )
    assert args.limit == 50
    assert args.retry_failed is True
    assert args.force is True
    assert args.ocr == "fra"
    assert args.pdf_parser == "pypdf"
    assert args.show_failures is True
    assert args.manifest == Path("data/custom_manifest.jsonl")
