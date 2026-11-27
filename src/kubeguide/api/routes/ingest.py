"""Background ingestion queue API routes: enqueue jobs, track progress, and inspect dead letters."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field

from kubeguide.api.deps import IngestRepoDep, ManifestDep, QueueDep, require_admin
from kubeguide.api.errors import NotFoundProblem
from kubeguide.workers.ingest import plan
from kubeguide.workers.queue import QueueUnavailableError

router = APIRouter(prefix="/v1/ingest", tags=["ingest"])


class IngestRequest(BaseModel):
    """Parameters for queueing a background document ingestion job."""

    limit: int = Field(default=20, ge=1, le=2000)
    source: str = Field(default="", max_length=100)
    retry_failed: bool = False


@router.post(
    "",
    status_code=202,
    dependencies=[Depends(require_admin)],
    summary="Queue background document ingestion",
)
async def start_ingest(
    body: IngestRequest,
    response: Response,
    repo: IngestRepoDep,
    queue: QueueDep,
    manifest: ManifestDep,
) -> dict[str, Any]:
    """Select eligible records, persist a job, enqueue items to Redis, and return immediately."""
    if body.retry_failed:
        records = (await repo.failed_records())[: body.limit]
    else:
        known = await repo.known_ids()
        records = plan(manifest, known, source=body.source, limit=body.limit)

    if not records:
        response.status_code = 200
        return {
            "job_id": None,
            "queued": 0,
            "detail": "Nothing to do: all of it is ingested.",
        }

    job_id, item_ids = await repo.create(records)
    try:
        await queue.put(item_ids)
    except QueueUnavailableError as exc:
        await repo.delete_job(job_id)
        raise HTTPException(
            status_code=503,
            detail="The job queue (Redis) cannot be reached.",
        ) from exc

    return {
        "job_id": job_id,
        "queued": len(item_ids),
        "status_url": f"/v1/ingest/{job_id}",
    }


@router.get("/dead-letter", summary="List permanently failed ingestion items")
async def dead_letter(
    repo: IngestRepoDep,
    limit: int = Query(default=50, ge=1, le=500),
) -> dict[str, Any]:
    """Return permanently failed ingestion items and their failure reasons."""
    items = await repo.dead_letter(limit=limit)
    return {"count": len(items), "items": items}


@router.get("/{job_id}", summary="Get ingestion job progress")
async def ingest_progress(
    job_id: str,
    request: Request,
    repo: IngestRepoDep,
) -> dict[str, Any]:
    """Return status counts and item-level progress for an ingestion job."""
    found = await repo.progress(job_id)
    if found is None:
        raise NotFoundProblem(
            detail=f"No ingest job with id '{job_id}'.",
            instance=request.url.path,
        )
    return found
