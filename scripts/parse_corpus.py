"""Parse the raw corpus into PostgreSQL documents and pages.

Usage:
    uv run python scripts/parse_corpus.py [--limit N] [--retry-failed] [--force]
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from collections import Counter
from pathlib import Path

from sqlalchemy import select

from kubeguide.config import get_settings
from kubeguide.db.models import Document, ParseFailure
from kubeguide.db.session import make_engine, make_sessionmaker
from kubeguide.ingest.parse import ParseError, parse_file, parse_pdf_ocr
from kubeguide.ingest.store import record_parse_failure, store_parsed_doc

logging.basicConfig(level=logging.WARNING)


async def main() -> int:
    parser = argparse.ArgumentParser(description="Parse raw documents into PostgreSQL.")
    parser.add_argument("--limit", type=int, default=None, help="Stop after processing N files.")
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Re-attempt files currently recorded in parse_failures.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reparse files even if already stored in documents table.",
    )
    parser.add_argument(
        "--ocr",
        nargs="?",
        const="eng",
        default=None,
        help="Use Tesseract OCR on scanned PDFs (optional language, default: eng).",
    )
    parser.add_argument(
        "--pdf-parser",
        default="pymupdf",
        choices=["pymupdf", "pypdf"],
        help="PDF parsing engine to use.",
    )
    parser.add_argument(
        "--show-failures",
        action="store_true",
        help="Display all unparseable files recorded in the dead-letter parse_failures table.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/manifest.jsonl"),
        help="Path to manifest file.",
    )
    args = parser.parse_args()

    settings = get_settings()
    engine = make_engine(settings)
    session_factory = make_sessionmaker(engine)

    if args.show_failures:
        async with session_factory() as session:
            failures = (await session.scalars(select(ParseFailure).order_by(ParseFailure.id))).all()
            if not failures:
                print("No failures recorded in dead-letter table parse_failures.")
            else:
                print(f"Total dead-letter failures recorded: {len(failures)}")
                for f in failures:
                    print(
                        f"  [{f.reason}] {f.path} (attempts: {f.attempts})\n"
                        f"    Detail: {f.detail}\n"
                    )
        await engine.dispose()
        return 0

    if not args.manifest.exists():
        print(f"Manifest not found: {args.manifest}", file=sys.stderr)
        await engine.dispose()
        return 1

    # 1. Inspect database for already parsed files and prior failures
    async with session_factory() as session:
        already_parsed = set(await session.scalars(select(Document.external_id)))
        failed_records = set(await session.scalars(select(ParseFailure.path)))

    entries: list[dict] = []
    with args.manifest.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))

    total_manifest = len(entries)
    already_count = 0
    failed_before_count = 0
    to_process: list[dict] = []

    for entry in entries:
        path_str = entry.get("path") or entry.get("rel_path", "")
        if not path_str:
            continue

        if path_str in already_parsed and not args.force:
            already_count += 1
            continue

        if path_str in failed_records and not args.retry_failed and not args.force:
            failed_before_count += 1
            continue

        to_process.append(entry)

    if args.limit:
        to_process = to_process[: args.limit]

    start_time = time.perf_counter()
    parsed_count = 0
    failed_count = 0
    total_pages = 0
    failure_reasons: Counter[str] = Counter()

    async with session_factory() as session:
        for idx, entry in enumerate(to_process, start=1):
            rel_path = entry.get("path") or entry.get("rel_path", "")
            file_path = Path(rel_path)
            sha256 = entry.get("sha256", "")
            url = entry.get("url")
            licence = entry.get("licence")

            try:
                if not file_path.exists():
                    raise ParseError("missing_file", f"File does not exist: {file_path}")

                if args.ocr and file_path.suffix.lower() == ".pdf":
                    doc = parse_pdf_ocr(file_path, language=args.ocr)
                else:
                    doc = parse_file(file_path, pdf_parser=args.pdf_parser)

                await store_parsed_doc(
                    session,
                    doc,
                    rel_path=rel_path,
                    sha256=sha256,
                    source_url=url,
                    licence=licence,
                )

                parsed_count += 1
                total_pages += len(doc.pages)

            except ParseError as err:
                failed_count += 1
                failure_reasons[err.reason] += 1
                print(f"failed  {err.reason:<16} {rel_path} ({err.detail})")
                await record_parse_failure(
                    session,
                    err,
                    rel_path=rel_path,
                    sha256=sha256,
                    source_url=url,
                )
            except Exception as exc:  # noqa: BLE001
                failed_count += 1
                failure_reasons["crash"] += 1
                print(f"failed  crash            {rel_path} ({exc})")
                await record_parse_failure(
                    session,
                    ParseError("crash", str(exc)),
                    rel_path=rel_path,
                    sha256=sha256,
                    source_url=url,
                )

            if idx % 50 == 0:
                elapsed = time.perf_counter() - start_time
                print(f"progress: {idx}/{len(to_process)} files processed ({elapsed:.1f}s)")

    duration = time.perf_counter() - start_time
    await engine.dispose()

    # Format summary output
    if parsed_count == 0 and failed_count == 0 and not to_process:
        print(
            f"files={total_manifest} already_parsed={already_count} "
            f"failed_before={failed_before_count} pages=0 seconds={duration:.1f}"
        )
    else:
        print(
            f"files={len(to_process)} failed={failed_count} parsed={parsed_count} "
            f"pages={total_pages} seconds={duration:.1f}"
        )
        if failure_reasons:
            reasons_str = " ".join(f"{k}={v}" for k, v in failure_reasons.most_common())
            print(f"failure reasons: {reasons_str}")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
