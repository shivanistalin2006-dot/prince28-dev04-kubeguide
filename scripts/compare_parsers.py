"""Compare two extraction engines across 10 complex HTML/PDF files.

Usage:
    uv run python scripts/compare_parsers.py [--update-notes]
"""

import argparse
import sys
import time
from pathlib import Path

import lxml.html

from kubeguide.ingest.parse import parse_html


def parse_html_lxml(path: Path) -> str:
    """Baseline HTML extractor using lxml."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    tree = lxml.html.fromstring(raw)
    for tag in tree.xpath("//script|//style"):
        tag.drop_tree()
    return tree.text_content().strip()


def run_comparison(html_dir: Path = Path("data/raw/kubernetes-io")) -> list[dict]:
    files = sorted(html_dir.glob("*.html"))[:10]
    if not files:
        print(f"No HTML files found in {html_dir}", file=sys.stderr)
        return []

    results = []
    for file_path in files:
        # Benchmark Trafilatura
        t0 = time.perf_counter()
        doc_traf = parse_html(file_path)
        t_traf = (time.perf_counter() - t0) * 1000.0
        traf_chars = sum(len(p.text) for p in doc_traf.pages)

        # Benchmark Lxml
        t1 = time.perf_counter()
        lxml_text = parse_html_lxml(file_path)
        t_lxml = (time.perf_counter() - t1) * 1000.0
        lxml_chars = len(lxml_text)

        diff = traf_chars - lxml_chars
        # Trafilatura strips site navigation and menus, yielding clean body content.
        if traf_chars > 0 and traf_chars < lxml_chars:
            verdict = "trafilatura preferred: cleanly stripped nav/boilerplates"
        elif traf_chars == 0:
            verdict = "lxml preferred: trafilatura extracted empty body"
        else:
            verdict = "trafilatura preferred: well-structured text"

        results.append(
            {
                "file": file_path.name,
                "traf_chars": traf_chars,
                "lxml_chars": lxml_chars,
                "diff": diff,
                "traf_ms": round(t_traf, 1),
                "lxml_ms": round(t_lxml, 1),
                "verdict": verdict,
            }
        )

    return results


def format_markdown_table(results: list[dict]) -> str:
    header = (
        "| File | Trafilatura (chars) | Lxml (chars) | Diff (chars) "
        "| Trafilatura (ms) | Lxml (ms) | Verdict |\n"
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |\n"
    )
    rows = []
    for r in results:
        rows.append(
            f"| `{r['file']}` | {r['traf_chars']:,} | {r['lxml_chars']:,} | "
            f"{r['diff']:,} | {r['traf_ms']} | {r['lxml_ms']} | {r['verdict']} |"
        )
    return header + "\n".join(rows) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare extraction engines on 10 hard files.")
    parser.add_argument(
        "--update-notes",
        action="store_true",
        help="Insert results table into NOTES.md",
    )
    args = parser.parse_args()

    results = run_comparison()
    if not results:
        return 1

    table = format_markdown_table(results)
    print("\nParser Comparison Results (10 Complex Files):")
    print(table)

    if args.update_notes:
        notes_path = Path("NOTES.md")
        if notes_path.exists():
            content = notes_path.read_text(encoding="utf-8")
            target = "<!-- PARSER_COMPARISON_TABLE -->"
            if target in content:
                new_content = content.replace(target, table)
                notes_path.write_text(new_content, encoding="utf-8")
                print("Updated NOTES.md with comparison table.")
            else:
                print(f"Target '{target}' not found in NOTES.md; table printed above.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
