"""Unit tests for scripts/db_stats.py."""

from scripts.db_stats import format_stats_report


def test_format_stats_report_with_clean_data() -> None:
    stats = {
        "total_docs": 422,
        "doc_types": [("markdown", 412), ("html", 10)],
        "licences": [("CC BY 4.0", 422)],
        "total_pages": 1710,
        "total_failures": 0,
        "failure_reasons": [],
    }

    report = format_stats_report(stats)
    assert "Total documents: 422" in report
    assert "Total pages:     1710" in report
    assert "markdown: 412 records" in report
    assert "html: 10 records" in report
    assert "Dead-letter parse failures: 0" in report


def test_format_stats_report_with_failures() -> None:
    stats = {
        "total_docs": 100,
        "doc_types": [("pdf", 100)],
        "licences": [("Apache-2.0", 100)],
        "total_pages": 300,
        "total_failures": 2,
        "failure_reasons": [("no_text_layer", 2)],
    }

    report = format_stats_report(stats)
    assert "Dead-letter parse failures: 2" in report
    assert "Failures by reason:" in report
    assert "no_text_layer: 2 records" in report
