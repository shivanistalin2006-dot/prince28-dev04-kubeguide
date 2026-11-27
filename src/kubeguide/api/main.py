"""FastAPI application factory and lifecycle management."""

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from kubeguide.api.errors import register_error_handlers
from kubeguide.api.middleware import register_middleware
from kubeguide.api.routes import chat, documents, health, ingest
from kubeguide.config import Settings, get_settings
from kubeguide.db.llm_calls import record_llm_call
from kubeguide.db.session import make_engine, make_sessionmaker
from kubeguide.llm.gateway import build_gateway
from kubeguide.llm.prompts import load as load_prompt
from kubeguide.llm.prompts import versions as prompt_versions
from kubeguide.logging_setup import setup_logging
from kubeguide.workers.main import create_embedded_worker
from kubeguide.workers.queue import JobQueue

logger = logging.getLogger("kubeguide.api")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure the FastAPI application instance."""
    if settings is None:
        settings = get_settings()

    setup_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.settings = settings
        engine = make_engine(settings)
        session_factory = make_sessionmaker(engine)
        app.state.engine = engine
        app.state.session_factory = session_factory

        # Load system prompt
        prompts_dir = Path(settings.prompts_dir)
        prompt_file = prompts_dir / "chat_system_v1.md"
        if prompt_file.exists():
            app.state.system_prompt = prompt_file.read_text(encoding="utf-8")
        else:
            app.state.system_prompt = (
                "You are KubeGuide, an assistant for Kubernetes SREs. "
                "If you are not sure, say 'I am not sure' instead of guessing."
            )

        # Load newest question-classification prompt for /v1/chat routing (if present)
        if prompt_versions(prompts_dir, "classify"):
            cls_ver, cls_prompt = load_prompt(prompts_dir, "classify")
            app.state.classify_version = cls_ver
            app.state.classify_prompt = cls_prompt
        else:
            app.state.classify_version = None
            app.state.classify_prompt = None

        # Configure LLM gateway with DB call recorder
        async def recorder(data: dict[str, Any]) -> None:
            async with session_factory() as session:
                await record_llm_call(session, data)

        app.state.gateway = build_gateway(settings, recorder=recorder)
        queue = JobQueue(settings.redis_url)
        app.state.queue = queue

        embedded_worker = None
        worker_task: asyncio.Task[None] | None = None
        if settings.worker_in_api:
            embedded_worker = create_embedded_worker(settings)

            async def _run_embedded() -> None:
                try:
                    await embedded_worker.async_run()
                except asyncio.CancelledError:
                    raise
                except Exception as exc:  # noqa: BLE001
                    logger.warning("embedded worker stopped: %s", exc)

            worker_task = asyncio.create_task(_run_embedded())

        try:
            yield
        finally:
            if embedded_worker is not None:
                with contextlib.suppress(Exception):
                    await embedded_worker.close()
            if worker_task is not None and not worker_task.done():
                worker_task.cancel()
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await worker_task
            await queue.close()
            await engine.dispose()

    app = FastAPI(
        title=settings.app_name,
        description="Kubernetes troubleshooting documentation and assistant service.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.state.settings = settings

    register_middleware(app)
    register_error_handlers(app)

    app.include_router(health.router)
    app.include_router(documents.router)
    app.include_router(chat.router)
    app.include_router(ingest.router)

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    return app
