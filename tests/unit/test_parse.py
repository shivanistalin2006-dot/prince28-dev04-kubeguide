"""Unit tests for the corpus document parser."""

from pathlib import Path

import pymupdf
import pytest

from kubeguide.ingest.parse import (
    ParseError,
    clean_text,
    drop_repeated_lines,
    heading_title,
    headings_in,
    markup_to_markdown,
    parse_file,
    parse_html,
    parse_pdf_pymupdf,
    parse_pdf_pypdf,
    parse_text,
    split_pages,
    with_heading_paths,
)


def test_clean_text_normalizes_unicode_and_newlines() -> None:
    raw = "Here is a ﬁne doc-\nument with \x00nulls and   spaces.\n\n\n\nNext paragraph."
    cleaned = clean_text(raw)
    assert "fine" in cleaned  # ligature ﬁ replaced
    assert "document" in cleaned  # hyphenated line break joined
    assert "\x00" not in cleaned
    assert "\n\n\n" not in cleaned


def test_drop_repeated_lines_short_doc() -> None:
    pages = ["Header\nContent A\nFooter", "Header\nContent B\nFooter"]
    # < 4 pages: returned unchanged
    assert drop_repeated_lines(pages) == pages


def test_drop_repeated_lines_removes_recurring_header_footer() -> None:
    pages = [
        "Annual Report\nPage 1 of 4\nIntro text chapter one.\nDetails here.\nConfidential",
        "Annual Report\nPage 2 of 4\nSecond chapter text.\nDetails here.\nConfidential",
        "Annual Report\nPage 3 of 4\nThird chapter metrics.\nDetails here.\nConfidential",
        "Annual Report\nPage 4 of 4\nFourth chapter summary.\nDetails here.\nConfidential",
    ]
    cleaned = drop_repeated_lines(pages)
    for p in cleaned:
        assert "Annual Report" not in p
        assert "Confidential" not in p
        assert "chapter" in p


def test_heading_title_strips_anchors() -> None:
    assert heading_title("First Steps { #first-steps }") == "First Steps"
    assert heading_title("Overview {.heading-class}") == "Overview"
    assert heading_title("Simple Heading") == "Simple Heading"


def test_headings_in_ignores_code_blocks() -> None:
    text = "# Main Title\n```python\n# Inside code comment\n```\n## Subheading\n"
    found, in_code = headings_in(text)
    assert not in_code
    assert found == [(1, "Main Title"), (2, "Subheading")]


def test_with_heading_paths_tracks_hierarchy() -> None:
    texts = [
        "# Workloads\nPage 1 intro",
        "## Deployments\nDetails on deployments",
        "### Rolling Updates\nDetails on updates",
    ]
    pages = with_heading_paths(texts)
    assert len(pages) == 3
    assert pages[0].headings == []
    assert pages[1].headings == ["Workloads"]
    assert pages[2].headings == ["Workloads", "Deployments"]


def test_markup_to_markdown_adoc() -> None:
    adoc = "= Top Level\n== Second Level\nSome content"
    converted = markup_to_markdown(adoc, ".adoc")
    assert "# Top Level" in converted
    assert "## Second Level" in converted


def test_markup_to_markdown_rst() -> None:
    rst = "First Section\n=============\nContent here\n\nSecond Section\n--------------\nMore"
    converted = markup_to_markdown(rst, ".rst")
    assert "# First Section" in converted
    assert "## Second Section" in converted


def test_split_pages_splits_near_size() -> None:
    paras = ["Paragraph " + str(i) * 200 for i in range(20)]
    text = "\n\n".join(paras)
    pages = split_pages(text, size=800)
    assert len(pages) > 1
    assert all(len(p) <= 2500 for p in pages)


def test_parse_text_markdown(tmp_path: Path) -> None:
    md_file = tmp_path / "guide.md"
    md_file.write_text("# Kubernetes Guide\n\nExplains pods and services.", encoding="utf-8")
    doc = parse_text(md_file)

    assert doc.parser == "plain"
    assert doc.kind == "text"
    assert doc.title == "Kubernetes Guide"
    assert len(doc.pages) == 1
    assert "pods and services" in doc.pages[0].text


def test_parse_text_data(tmp_path: Path) -> None:
    json_file = tmp_path / "config.json"
    json_file.write_text('{"app": "kubeguide", "version": "1.0"}', encoding="utf-8")
    doc = parse_text(json_file)

    assert doc.parser == "plain"
    assert doc.kind == "data"
    assert doc.title == "config"


def test_parse_html(tmp_path: Path) -> None:
    html_file = tmp_path / "page.html"
    html_content = (
        "<!DOCTYPE html><html><head><title>Pod Lifecycle</title></head><body>"
        "<article><h1>Pod Lifecycle</h1><p>Phases: Pending, Running, Failed.</p></article>"
        "</body></html>"
    )
    html_file.write_text(html_content, encoding="utf-8")
    doc = parse_html(html_file)

    assert doc.parser == "trafilatura"
    assert doc.kind == "html"
    assert "Pod Lifecycle" in doc.title
    assert "Pending" in doc.pages[0].text


def test_parse_file_unsupported_type(tmp_path: Path) -> None:
    bin_file = tmp_path / "archive.zip"
    bin_file.write_bytes(b"PK\x03\x04")
    with pytest.raises(ParseError) as exc_info:
        parse_file(bin_file)
    assert exc_info.value.reason == "unsupported_type"


def test_parse_pdf_pymupdf_synthetic(tmp_path: Path) -> None:
    pdf_path = tmp_path / "synthetic.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Kubernetes Architecture", fontsize=24)
    page.insert_text(
        (50, 120),
        "The control plane makes decisions about the cluster. Nodes run container workloads.",
        fontsize=11,
    )
    doc.save(pdf_path)
    doc.close()

    parsed = parse_pdf_pymupdf(pdf_path)
    assert parsed.parser == "pymupdf"
    assert parsed.kind == "pdf"
    assert len(parsed.pages) == 1
    assert "Kubernetes Architecture" in parsed.pages[0].text
    assert parsed.title == "Kubernetes Architecture"


def test_parse_pdf_pypdf_synthetic(tmp_path: Path) -> None:
    pdf_path = tmp_path / "pypdf_test.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Service Mesh Overview", fontsize=18)
    page.insert_text(
        (50, 100),
        "A dedicated infrastructure layer for managing service-to-service communication.",
        fontsize=12,
    )
    doc.save(pdf_path)
    doc.close()

    parsed = parse_pdf_pypdf(pdf_path)
    assert parsed.parser == "pypdf"
    assert parsed.kind == "pdf"
    assert "Service Mesh Overview" in parsed.pages[0].text


def test_parse_pdf_scanned_pages_detection(tmp_path: Path) -> None:
    pdf_path = tmp_path / "mixed.pdf"
    doc = pymupdf.open()
    # Page 1: substantial text
    p1 = doc.new_page()
    p1.insert_text((50, 72), "Chapter 1: Storage Classes", fontsize=20)
    p1.insert_text(
        (50, 100),
        "A StorageClass provides a way for administrators to describe storage profiles.",
        fontsize=11,
    )
    # Page 2: virtually blank / scan simulation (under 50 chars)
    p2 = doc.new_page()
    p2.insert_text((50, 72), "Blank", fontsize=10)
    doc.save(pdf_path)
    doc.close()

    parsed = parse_pdf_pymupdf(pdf_path)
    assert parsed.metadata.get("scanned_pages") == [2]


def test_parse_text_extracts_frontmatter_title_and_strips_metadata(tmp_path: Path) -> None:
    md_file = tmp_path / "sample.md"
    content = (
        "---\n"
        "title: Pod Security Standards\n"
        "weight: 10\n"
        "---\n\n"
        "Pod Security Standards define different isolation levels for Pods.\n"
        "Administrators can enforce these standards cluster-wide."
    )
    md_file.write_text(content, encoding="utf-8")
    parsed = parse_file(md_file)
    assert parsed.title == "Pod Security Standards"
    assert "weight: 10" not in parsed.pages[0].text
    assert "Pod Security Standards define" in parsed.pages[0].text
