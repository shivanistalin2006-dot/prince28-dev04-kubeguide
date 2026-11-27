"""One job = one document: get the file, parse it, store it, extract metadata.

A job can run twice (the worker died, or a retry). That is safe, because every stage
checks what is already in the database: a document is identified by its content hash.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import logging
import re
import tempfile
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import httpx
from arq import Retry
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kubeguide.db.models import Document, IngestItem
from kubeguide.ingest.fetch import RETRYABLE, HostGate, Robots, Source, fetch_one
from kubeguide.ingest.parse import ParseError, parse_file
from kubeguide.ingest.store import record_parse_failure, store_parsed_doc
from kubeguide.llm.extract import document_text, extract, save

logger = logging.getLogger("kubeguide.worker")
GITHUB_BLOB = re.compile(r"^https://github\.com/([^/]+/[^/]+)/blob/[^/]+/(.+)$")


class Permanent(Exception):
    """This document will never work, however often we try: no retry, straight to dead-letter."""


def document_id(sha256: str) -> str:
    """Stable content-hash identifier for deduplicating manifest records."""
    return sha256.strip().lower()


def plan(
    records: list[dict[str, Any]],
    done_ids: set[str],
    *,
    source: str = "",
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Return manifest records that still need ingestion: downloaded, matching source, not done."""
    todo: list[dict[str, Any]] = []
    seen = {document_id(d) for d in done_ids if d}
    for record in records:
        if record.get("status") != "downloaded":
            continue
        if source and record.get("source") != source:
            continue
        sha = record.get("sha256", "")
        if not sha:
            continue
        doc_id = document_id(sha)
        if doc_id in seen:
            continue
        seen.add(doc_id)
        todo.append(record)
    return todo[:limit] if limit else todo


def raw_url(record: dict[str, Any]) -> str:
    """Resolve the raw download URL, pinning GitHub blob URLs to the manifest's commit."""
    url = record.get("url", "")
    match = GITHUB_BLOB.match(url)
    if record.get("via") == "git" and match and record.get("commit"):
        return f"https://raw.githubusercontent.com/{match[1]}/{record['commit']}/{match[2]}"
    return url


def sha256_of(path: Path) -> str:
    """Compute the SHA-256 hex digest of a file on disk."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


class Pace:
    """At most `per_minute` model calls a minute, shared across concurrent worker tasks."""

    def __init__(
        self,
        per_minute: float,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[Any]] = asyncio.sleep,
    ) -> None:
        self._gap = 60.0 / per_minute if per_minute > 0 else 0.0
        self._clock = clock
        self._sleep = sleep
        self._next = 0.0
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        if self._gap <= 0:
            return
        async with self._lock:
            now = self._clock()
            delay = max(0.0, self._next - now)
            self._next = max(now, self._next) + self._gap
        if delay > 0:
            await self._sleep(delay)


async def get_file(
    record: dict[str, Any],
    folder: Path,
    client: httpx.AsyncClient,
    sleep: Callable[[float], Awaitable[Any]] = asyncio.sleep,
) -> Path:
    """Return local file if present on disk; otherwise download it politely into `folder`."""
    rel = record.get("path", "")
    if rel:
        local_path = Path(rel)
        if local_path.is_file():
            return local_path

    if record.get("via") == "manual":
        raise Permanent("downloaded by hand: this file exists only on the laptop that has it")

    url = raw_url(record)
    source = Source(
        url=url,
        source=record.get("source", "unknown"),
        licence=record.get("licence") or "unknown",
        title=record.get("title", ""),
    )
    result = await fetch_one(
        client,
        source,
        root=folder,
        raw_dir=folder / "raw",
        robots=Robots(client),
        gate=HostGate(0.5, sleep),
        slots=asyncio.Semaphore(1),
        max_attempts=2,
        sleep=sleep,
    )
    if result["status"] == "downloaded":
        return folder / result["path"]

    problem = f"download {result['status']}: {result.get('error', '')}"
    if result["status"] == "blocked" or result.get("http_status") not in (None, *RETRYABLE):
        raise Permanent(problem)
    raise RuntimeError(problem)


async def process(ctx: dict[str, Any], session: AsyncSession, item: IngestItem) -> tuple[str, int]:
    """Process one IngestItem end-to-end. Returns (status, pages)."""
    record = dict(item.record)
    with tempfile.TemporaryDirectory() as folder:
        path = await get_file(record, Path(folder), ctx["http"])
        expected_sha = str(record.get("sha256") or "").strip().lower()
        actual_sha = await asyncio.to_thread(sha256_of, path)
        if expected_sha and actual_sha != expected_sha and record.get("via") == "git":
            raise Permanent(
                f"sha256 mismatch for git commit {record.get('commit', '')}: "
                f"expected {expected_sha[:12]}, got {actual_sha[:12]}"
            )
        record["sha256"] = actual_sha

        document = await session.scalar(
            select(Document).where(Document.sha256 == actual_sha, Document.doc_type != "record")
        )
        status = "skipped"
        rel_path = record.get("path") or actual_sha[:12]

        if document is None:
            try:
                parsed = await asyncio.to_thread(parse_file, path)
            except ParseError as error:
                await record_parse_failure(
                    session,
                    error,
                    rel_path=rel_path,
                    sha256=actual_sha,
                    source_url=record.get("url"),
                )
                raise Permanent(f"parse: {error.reason}") from error

            document = await store_parsed_doc(
                session,
                parsed,
                rel_path=rel_path,
                sha256=actual_sha,
                source_url=record.get("url"),
                licence=record.get("licence"),
            )
            status = "done"

        pages = int((document.metadata_ or {}).get("pages", 0))
        task = ctx.get("extract")
        note = (document.metadata_ or {}).get("extract") or {}
        if task and (note.get("prompt") != task["version"] or "error" in note):
            await ctx["pace"].wait()
            text = await document_text(session, document.id, max_chars=task["chars"])
            result = await extract(
                ctx["gateway"],
                task["prompt"],
                task["version"],
                text,
                task["schema"],
            )
            await save(session, document, result, task["version"])
            if result.record is None:
                last_err = result.errors[-1] if result.errors else "unknown extraction error"
                raise Permanent(f"extract: {last_err[:200]}")
            status = "done"

        return status, pages


async def ingest_document(ctx: dict[str, Any], item_id: int) -> str:
    """ARQ task entrypoint for one queued IngestItem. Tracks attempts in Postgres."""
    max_tries = int(ctx["settings"].ingest_max_tries)
    async with ctx["sessionmaker"]() as session:
        item = await session.get(IngestItem, item_id)
        if item is None or item.status not in ("queued", "running"):
            return "ignored"

        if item.attempts >= max_tries:
            item.status = "failed"
            item.error = f"gave up: started {item.attempts} times and never finished"
            await session.commit()
            return "failed"

        item.status = "running"
        item.attempts += 1
        attempt = item.attempts
        await session.commit()

        try:
            new_status, pages = await process(ctx, session, item)
            item = await session.get(IngestItem, item_id)
            if item is not None:
                item.status = new_status
                item.pages = pages
                item.error = ""
                await session.commit()
        except Permanent as error:
            with contextlib.suppress(Exception):
                await session.rollback()
            async with ctx["sessionmaker"]() as err_session:
                err_item = await err_session.get(IngestItem, item_id)
                if err_item is not None:
                    err_item.status = "failed"
                    err_item.error = str(error)[:500]
                    await err_session.commit()
            logger.info("item %s failed", item_id)
            return "failed"
        except Exception as error:  # noqa: BLE001
            with contextlib.suppress(Exception):
                await session.rollback()
            reason = f"{type(error).__name__}: {error}"[:500]
            async with ctx["sessionmaker"]() as err_session:
                err_item = await err_session.get(IngestItem, item_id)
                if err_item is not None:
                    if attempt >= max_tries:
                        err_item.status = "failed"
                        err_item.error = f"gave up after {attempt} tries: {reason}"[:500]
                    else:
                        err_item.status = "queued"
                        err_item.error = f"try {attempt} failed: {reason}"[:500]
                    await err_session.commit()
            if attempt < max_tries:
                logger.warning("item %s will be retried: %s", item_id, reason)
                raise Retry(defer=attempt * 30) from error
            logger.info("item %s failed", item_id)
            return "failed"

        final_status = item.status if item is not None else "ignored"
        logger.info("item %s %s", item_id, final_status)
        return final_status
