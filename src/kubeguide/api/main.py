"""FastAPI application factory and lifecycle management."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from kubeguide.api.errors import register_error_handlers
from kubeguide.api.middleware import register_middleware
from kubeguide.api.routes import documents, health
from kubeguide.config import Settings, get_settings
from kubeguide.logging_setup import setup_logging
from kubeguide.store import DocumentStore


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure the FastAPI application instance."""
    if settings is None:
        settings = get_settings()

    setup_logging(settings.log_level)

    store = DocumentStore()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.settings = settings
        app.state.store = store
        store.load_from_file(settings.data_file)
        yield

    app = FastAPI(
        title=settings.app_name,
        description="Kubernetes troubleshooting documentation and assistant service.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.state.settings = settings
    app.state.store = store

    register_middleware(app)
    register_error_handlers(app)

    app.include_router(health.router)
    app.include_router(documents.router)

    return app
