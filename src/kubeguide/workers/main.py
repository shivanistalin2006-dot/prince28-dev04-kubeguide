"""ARQ worker entrypoint, lifecycle hooks, and optional embedded worker builder."""

from __future__ import annotations

import logging
from typing import Any

from arq.connections import RedisSettings
from arq.constants import in_progress_key_prefix, result_key_prefix
from arq.worker import Worker
from pydantic import ValidationError

from kubeguide.config import Settings, get_settings
from kubeguide.db.ingest_jobs import IngestRepository
from kubeguide.db.llm_calls import record_llm_call
from kubeguide.db.session import make_engine, make_sessionmaker
from kubeguide.ingest.fetch import make_client
from kubeguide.llm.doc_meta import DocMeta
from kubeguide.llm.gateway import build_gateway
from kubeguide.llm.prompts import load as load_prompt
from kubeguide.llm.prompts import versions as prompt_versions
from kubeguide.logging_setup import setup_logging
from kubeguide.workers.ingest import Pace, ingest_document
from kubeguide.workers.queue import make_redis_settings

logger = logging.getLogger("kubeguide.worker")


def _safe_settings() -> Settings | None:
    """Load Settings if environment is configured; returns None during partial test imports."""
    try:
        return get_settings()
    except ValidationError:
        return None


async def requeue_unfinished(redis: Any, item_ids: list[int]) -> int:
    """Re-enqueue unfinished DB items, clearing stale ARQ result keys if needed."""
    requeued = 0
    for item_id in item_ids:
        job_id = f"ingest:{item_id}"
        job = await redis.enqueue_job("ingest_document", item_id, _job_id=job_id)
        if job is None:
            result_key = result_key_prefix + job_id
            in_progress_key = in_progress_key_prefix + job_id
            if await redis.exists(result_key) and not await redis.exists(in_progress_key):
                await redis.delete(result_key)
                job = await redis.enqueue_job("ingest_document", item_id, _job_id=job_id)
        if job is not None:
            requeued += 1
    return requeued


async def startup(ctx: dict[str, Any]) -> None:
    """Initialize DB, LLM gateway, HTTP client, rate limiter, and requeue unfinished items."""
    settings: Settings = ctx.get("settings") or get_settings()
    if not ctx.get("embedded"):
        setup_logging(settings.log_level)

    engine = make_engine(settings)
    sessionmaker = make_sessionmaker(engine)
    ctx["settings"] = settings
    ctx["engine"] = engine
    ctx["sessionmaker"] = sessionmaker
    ctx["http"] = make_client()
    ctx["pace"] = Pace(settings.ingest_rpm)

    async def recorder(data: dict[str, Any]) -> None:
        async with sessionmaker() as session:
            await record_llm_call(session, data)

    ctx["gateway"] = build_gateway(settings, recorder=recorder)

    if prompt_versions(settings.prompts_dir, "extract"):
        ver, prompt_text = load_prompt(settings.prompts_dir, "extract")
        ctx["extract"] = {
            "version": f"extract_v{ver}",
            "prompt": prompt_text,
            "schema": DocMeta,
            "chars": 6000,
        }
    else:
        ctx["extract"] = None

    requeued = 0
    redis = ctx.get("redis")
    async with sessionmaker() as session:
        item_ids = await IngestRepository(session).unfinished_items(settings.ingest_job_timeout)
    if redis is not None:
        requeued = await requeue_unfinished(redis, item_ids)

    logger.info("worker ready, %d unfinished item(s) put back in the queue", requeued)


async def shutdown(ctx: dict[str, Any]) -> None:
    """Dispose HTTP client and database engine when the worker exits."""
    http = ctx.get("http")
    if http is not None:
        await http.aclose()
    engine = ctx.get("engine")
    if engine is not None:
        await engine.dispose()


def create_embedded_worker(settings: Settings) -> Worker:
    """Build an in-process ARQ Worker for single-container hosts (WORKER_IN_API=true)."""
    return Worker(
        functions=[ingest_document],
        on_startup=startup,
        on_shutdown=shutdown,
        redis_settings=make_redis_settings(settings.redis_url, fast_fail=True),
        max_jobs=settings.ingest_concurrency,
        job_timeout=settings.ingest_job_timeout,
        keep_result=0,
        max_tries=settings.ingest_max_tries + 2,
        handle_signals=False,
        ctx={"settings": settings, "embedded": True},
    )


_INITIAL = _safe_settings()


class WorkerSettings:
    """ARQ CLI configuration: `arq kubeguide.workers.main.WorkerSettings`."""

    functions = [ingest_document]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = (
        make_redis_settings(_INITIAL.redis_url) if _INITIAL is not None else RedisSettings()
    )
    max_jobs = _INITIAL.ingest_concurrency if _INITIAL is not None else 2
    job_timeout = _INITIAL.ingest_job_timeout if _INITIAL is not None else 60
    keep_result = 0
    max_tries = (_INITIAL.ingest_max_tries + 2) if _INITIAL is not None else 5
