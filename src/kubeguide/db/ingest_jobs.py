"""Database operations for ingestion jobs, items, and dead-letter queries."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from kubeguide.db.models import Document, IngestItem, IngestJob, ParseFailure


def _item_key(item: IngestItem) -> str:
    rec = item.record or {}
    return str(rec.get("sha256") or rec.get("path") or f"item:{item.id}")


def _item_summary(item: IngestItem) -> dict[str, Any]:
    rec = item.record or {}
    return {
        "id": item.id,
        "status": item.status,
        "attempts": item.attempts,
        "pages": item.pages,
        "error": item.error,
        "path": rec.get("path", ""),
        "source": rec.get("source", ""),
        "title": rec.get("title", ""),
        "url": rec.get("url", ""),
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


class IngestRepository:
    """Repository managing ingest_jobs and ingest_items."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def known_ids(self) -> set[str]:
        """Return SHA-256 hashes of documents already stored or known unparseable."""
        doc_hashes = set(
            (
                await self.session.scalars(
                    select(Document.sha256).where(Document.doc_type != "record")
                )
            ).all()
        )
        fail_hashes = set((await self.session.scalars(select(ParseFailure.sha256))).all())
        return {h for h in (doc_hashes | fail_hashes) if h}

    async def create(self, records: list[dict[str, Any]]) -> tuple[str, list[int]]:
        """Persist a new IngestJob and its queued IngestItem rows."""
        job_id = uuid.uuid4().hex
        job = IngestJob(id=job_id, requested=len(records))
        self.session.add(job)
        await self.session.flush()

        items = [IngestItem(job_id=job_id, record=dict(rec)) for rec in records]
        self.session.add_all(items)
        await self.session.commit()
        return job_id, [item.id for item in items]

    async def delete_job(self, job_id: str) -> None:
        """Remove a job when queueing to Redis failed immediately after creation."""
        await self.session.execute(delete(IngestJob).where(IngestJob.id == job_id))
        await self.session.commit()

    async def progress(self, job_id: str) -> dict[str, Any] | None:
        """Return status counts and safe item details for a job, or None if not found."""
        job = await self.session.get(IngestJob, job_id)
        if job is None:
            return None

        items = list(
            (
                await self.session.scalars(
                    select(IngestItem).where(IngestItem.job_id == job_id).order_by(IngestItem.id)
                )
            ).all()
        )

        counts = {"queued": 0, "running": 0, "done": 0, "skipped": 0, "failed": 0}
        total_pages = 0
        for item in items:
            if item.status in counts:
                counts[item.status] += 1
            total_pages += int(item.pages or 0)

        return {
            "job_id": job.id,
            "requested": job.requested,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            **counts,
            "pages": total_pages,
            "finished": counts["queued"] == 0 and counts["running"] == 0,
            "items": [_item_summary(item) for item in items],
        }

    async def _latest_failed_items(self) -> list[IngestItem]:
        """Return newest IngestItem per document where the latest status is 'failed'."""
        rows = list(
            (await self.session.scalars(select(IngestItem).order_by(IngestItem.id.desc()))).all()
        )
        seen: set[str] = set()
        failed: list[IngestItem] = []
        for item in rows:
            key = _item_key(item)
            if key in seen:
                continue
            seen.add(key)
            if item.status == "failed":
                failed.append(item)
        return failed

    async def dead_letter(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return currently failed items and their error reasons."""
        failed = (await self._latest_failed_items())[:limit]
        out: list[dict[str, Any]] = []
        for item in failed:
            rec = item.record or {}
            out.append(
                {
                    "item_id": item.id,
                    "job_id": item.job_id,
                    "status": item.status,
                    "attempts": item.attempts,
                    "error": item.error,
                    "path": rec.get("path", ""),
                    "url": rec.get("url", ""),
                    "source": rec.get("source", ""),
                    "sha256": rec.get("sha256", ""),
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                }
            )
        return out

    async def failed_records(self) -> list[dict[str, Any]]:
        """Return manifest record payloads for active dead-letter items."""
        return [dict(item.record) for item in await self._latest_failed_items()]

    async def unfinished_items(self, timeout_seconds: int) -> list[int]:
        """Recover abandoned running items and return all queued item IDs to re-enqueue."""
        cutoff = datetime.now(UTC) - timedelta(seconds=timeout_seconds)
        stmt = (
            select(IngestItem)
            .where(
                or_(
                    IngestItem.status == "queued",
                    (IngestItem.status == "running") & (IngestItem.updated_at < cutoff),
                )
            )
            .order_by(IngestItem.id)
        )
        items = list((await self.session.scalars(stmt)).all())
        changed = False
        for item in items:
            if item.status == "running":
                item.status = "queued"
                changed = True
        if changed:
            await self.session.commit()
        return [item.id for item in items]
