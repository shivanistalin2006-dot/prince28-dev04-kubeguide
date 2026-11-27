"""FastAPI dependency injection providers."""

import json
import secrets
from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from kubeguide.config import Settings, get_settings
from kubeguide.db.ingest_jobs import IngestRepository
from kubeguide.db.llm_calls import LlmUsageRepository
from kubeguide.db.repository import DocumentRepository
from kubeguide.llm.gateway import LLMGateway, build_gateway
from kubeguide.workers.queue import JobQueue


def get_app_settings(request: Request) -> Settings:
    """Dependency to retrieve application settings."""
    if hasattr(request.app.state, "settings") and request.app.state.settings is not None:
        return request.app.state.settings
    return get_settings()


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    """Dependency providing a database session per request."""
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        yield session


def get_repo(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentRepository:
    """Dependency providing a DocumentRepository instance."""
    return DocumentRepository(session)


def get_usage_repo(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> LlmUsageRepository:
    """Dependency providing an LlmUsageRepository instance."""
    return LlmUsageRepository(session)


def get_ingest_repo(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> IngestRepository:
    """Dependency providing an IngestRepository instance."""
    return IngestRepository(session)


def get_gateway(request: Request) -> LLMGateway:
    """Dependency providing an LLMGateway instance."""
    gateway = getattr(request.app.state, "gateway", None)
    if gateway is None:
        settings = get_app_settings(request)
        gateway = build_gateway(settings)
    return gateway


def get_queue(request: Request) -> JobQueue:
    """Dependency providing the Redis-backed JobQueue instance."""
    queue = getattr(request.app.state, "queue", None)
    if queue is None:
        settings = get_app_settings(request)
        queue = JobQueue(settings.redis_url)
    return queue


def get_manifest(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> list[dict[str, Any]]:
    """Read deduplicated manifest records (newest line per URL) from `settings.manifest_file`."""
    path = settings.manifest_file
    if not path.is_file():
        return []
    latest: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        key = record.get("url") or record.get("path") or record.get("sha256")
        if key:
            latest[str(key)] = record
    return list(latest.values())


def require_admin(
    settings: Annotated[Settings, Depends(get_app_settings)],
    x_admin_token: Annotated[str | None, Header(alias="X-Admin-Token")] = None,
) -> None:
    """Validate `X-Admin-Token` against configured `ADMIN_TOKEN`."""
    if not settings.admin_token:
        raise HTTPException(
            status_code=403,
            detail="Set ADMIN_TOKEN to allow ingestion here.",
        )
    if not x_admin_token or not secrets.compare_digest(x_admin_token, settings.admin_token):
        raise HTTPException(
            status_code=401,
            detail="Missing or wrong X-Admin-Token header.",
        )


GatewayDep = Annotated[LLMGateway, Depends(get_gateway)]
UsageDep = Annotated[LlmUsageRepository, Depends(get_usage_repo)]
IngestRepoDep = Annotated[IngestRepository, Depends(get_ingest_repo)]
QueueDep = Annotated[JobQueue, Depends(get_queue)]
ManifestDep = Annotated[list[dict[str, Any]], Depends(get_manifest)]


async def check_db(request: Request) -> bool:
    """Check database readiness."""
    engine = getattr(request.app.state, "engine", None)
    if not engine:
        return False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
