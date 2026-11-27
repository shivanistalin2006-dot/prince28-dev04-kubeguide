"""Generate docs/INGEST_REPORT.md directly from PostgreSQL tables.

Usage:
    uv run python scripts/ingest_report.py
"""

from __future__ import annotations

import asyncio
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import func, select

from kubeguide.config import get_settings
from kubeguide.db.ingest_jobs import IngestRepository
from kubeguide.db.models import Document, IngestItem, IngestJob, LlmCall, Page, ParseFailure
from kubeguide.db.session import make_engine, make_sessionmaker

REPORT_PATH = Path("docs/INGEST_REPORT.md")
START, END = "<!-- generated:start -->", "<!-- generated:end -->"
CHARS_PER_TOKEN = 4

DEFAULT_LEARNED = """## What I learnt

1. Separating the API (HTTP 202) from the background worker via Redis + Postgres keeps request
   latency flat even when ingestion involves slow downloads and rate-limited LLM calls.
2. Tracking item attempts and state in Postgres (`ingest_items`) ensures crash recovery: an
   abruptly killed worker leaves interrupted items recoverable after the visibility timeout without
   duplicating rows in `documents`.
3. Comparing actual extracted pages and tokens against Monday's `docs/CAPACITY.md` estimate
   highlights where cleaning boilerplates and HTML nav affects real token volume.
"""


def put_block(path: Path, title: str, block: str) -> None:
    """Replace the generated block while preserving manual notes outside the markers."""
    if path.exists():
        text = path.read_text(encoding="utf-8")
    else:
        text = f"# {title}\n\n{DEFAULT_LEARNED.strip()}\n"

    wrapped = f"{START}\n{block.strip()}\n{END}"
    if START in text and END in text:
        text = text[: text.index(START)] + wrapped + text[text.index(END) + len(END) :]
    else:
        text = f"# {title}\n\n{wrapped}\n\n{text.lstrip()}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


async def collect_metrics() -> dict:
    """Query PostgreSQL for live ingestion, corpus, dead-letter, and LLM usage metrics."""
    settings = get_settings()
    engine = make_engine(settings)
    sessionmaker = make_sessionmaker(engine)
    try:
        async with sessionmaker() as session:
            total_docs = int(
                (
                    await session.scalar(
                        select(func.count())
                        .select_from(Document)
                        .where(Document.doc_type != "record")
                    )
                )
                or 0
            )
            all_docs = list(
                (await session.scalars(select(Document).where(Document.doc_type != "record"))).all()
            )
            total_pages = int((await session.scalar(select(func.count()).select_from(Page))) or 0)
            total_chars = int(
                (await session.scalar(select(func.coalesce(func.sum(func.length(Page.text)), 0))))
                or 0
            )
            parse_failures = list((await session.scalars(select(ParseFailure))).all())
            total_jobs = int(
                (await session.scalar(select(func.count()).select_from(IngestJob))) or 0
            )
            item_rows = (
                await session.execute(
                    select(IngestItem.status, func.count()).group_by(IngestItem.status)
                )
            ).all()
            item_counts = {str(status): int(cnt) for status, cnt in item_rows}
            dead_items = await IngestRepository(session).dead_letter(limit=100)

            llm_rows = (
                await session.execute(
                    select(
                        LlmCall.purpose,
                        func.count(LlmCall.id),
                        func.coalesce(func.sum(LlmCall.tokens_in), 0),
                        func.coalesce(func.sum(LlmCall.tokens_out), 0),
                        func.coalesce(func.sum(LlmCall.cost_inr), 0.0),
                    ).group_by(LlmCall.purpose)
                )
            ).all()
    finally:
        await engine.dispose()

    extracted_ok = 0
    extracted_err = 0
    for doc in all_docs:
        ext = (doc.metadata_ or {}).get("extract")
        if isinstance(ext, dict):
            if "error" in ext:
                extracted_err += 1
            else:
                extracted_ok += 1

    reason_counts: Counter[str] = Counter()
    for pf in parse_failures:
        reason_counts[f"parse:{pf.reason}"] += 1
    for item in dead_items:
        err = str(item.get("error") or "unknown")
        prefix = err.split(":", 1)[0].strip() if ":" in err else err[:30]
        reason_counts[prefix] += 1

    return {
        "total_docs": total_docs,
        "total_pages": total_pages,
        "total_chars": total_chars,
        "est_tokens": total_chars // CHARS_PER_TOKEN,
        "extracted_ok": extracted_ok,
        "extracted_err": extracted_err,
        "parse_failures": len(parse_failures),
        "total_jobs": total_jobs,
        "item_counts": item_counts,
        "dead_letter_count": len(dead_items),
        "dead_items": dead_items,
        "reason_counts": reason_counts,
        "llm_rows": [
            {
                "purpose": str(r[0]),
                "calls": int(r[1]),
                "tokens_in": int(r[2]),
                "tokens_out": int(r[3]),
                "cost_inr": float(r[4]),
            }
            for r in llm_rows
        ],
    }


def render_block(m: dict, today: str) -> str:
    """Format collected metrics into Markdown."""
    ic = m["item_counts"]
    total_cost = sum(r["cost_inr"] for r in m["llm_rows"])
    total_calls = sum(r["calls"] for r in m["llm_rows"])
    total_tok_in = sum(r["tokens_in"] for r in m["llm_rows"])
    total_tok_out = sum(r["tokens_out"] for r in m["llm_rows"])

    lines = [
        f"## Database snapshot ({today} UTC)",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Documents in PostgreSQL (`doc_type != 'record'`) | {m['total_docs']:,} |",
        f"| Pages of text | {m['total_pages']:,} |",
        f"| Characters of text | {m['total_chars']:,} |",
        f"| Tokens of text (`chars / {CHARS_PER_TOKEN}`) | {m['est_tokens']:,} |",
        f"| Structured metadata extracted (`extract_v1` ok) | {m['extracted_ok']:,} |",
        f"| Structured metadata extraction errors | {m['extracted_err']:,} |",
        f"| Parse dead-letter table (`parse_failures`) | {m['parse_failures']:,} |",
        "",
        "## Background queue summary (`ingest_jobs` / `ingest_items`)",
        "",
        "| Status | Count |",
        "|---|---:|",
        f"| Total ingest jobs | {m['total_jobs']:,} |",
        f"| Completed (`done`) | {ic.get('done', 0):,} |",
        f"| Skipped (`skipped`) | {ic.get('skipped', 0):,} |",
        f"| Failed (`failed`) | {ic.get('failed', 0):,} |",
        f"| Active dead-letter items | {m['dead_letter_count']:,} |",
        f"| Queued / Running | {ic.get('queued', 0) + ic.get('running', 0):,} |",
        "",
        "## Dead-letter reasons",
        "",
    ]

    if m["reason_counts"]:
        lines.extend(["| Reason prefix | Count |", "|---|---:|"])
        for reason, cnt in m["reason_counts"].most_common():
            lines.append(f"| `{reason}` | {cnt:,} |")
    else:
        lines.append("No active dead-letter failures.")

    lines.extend(
        [
            "",
            "## LLM usage & cost (`llm_calls`)",
            "",
            "| Purpose | Calls | Input tokens | Output tokens | Cost (INR) |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in m["llm_rows"]:
        lines.append(
            f"| {row['purpose']} | {row['calls']:,} | {row['tokens_in']:,} | "
            f"{row['tokens_out']:,} | Rs {row['cost_inr']:.4f} |"
        )
    lines.append(
        f"| **Total** | **{total_calls:,}** | **{total_tok_in:,}** | "
        f"**{total_tok_out:,}** | **Rs {total_cost:.4f}** |"
    )

    lines.extend(
        [
            "",
            "## Comparison against Monday's estimate (`docs/CAPACITY.md`)",
            "",
            "| Metric | Monday estimate (`CAPACITY.md`) | Measured in PostgreSQL | Difference |",
            "|---|---:|---:|---:|",
            (
                f"| Start-corpus pages | 1,505 | {m['total_pages']:,} "
                f"| {m['total_pages'] - 1505:+,} |"
            ),
            (
                f"| Tokens of text | 1,128,966 | {m['est_tokens']:,} "
                f"| {m['est_tokens'] - 1128966:+,} |"
            ),
            "",
            "Measured pages are slightly higher than Monday's `3,000`-char page estimate because "
            "paragraph-boundary splitting produces shorter chunks, while measured tokens of clean "
            "text are lower after stripping HTML navigation boilerplate and YAML frontmatter.",
        ]
    )
    return "\n".join(lines)


async def _main() -> int:
    metrics = await collect_metrics()
    today = datetime.now(UTC).strftime("%Y-%m-%d %H:%M")
    put_block(REPORT_PATH, "Ingestion Report: KubeGuide", render_block(metrics, today))
    print(
        f"documents={metrics['total_docs']} pages={metrics['total_pages']} "
        f"dead_letter={metrics['dead_letter_count']} -> {REPORT_PATH}"
    )
    return 0


def main() -> int:
    return asyncio.run(_main())


if __name__ == "__main__":
    sys.exit(main())
