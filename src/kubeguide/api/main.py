"""FastAPI application factory and lifecycle management."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from kubeguide.api.errors import register_error_handlers
from kubeguide.api.middleware import register_middleware
from kubeguide.api.routes import documents, health
from kubeguide.config import Settings, get_settings
from kubeguide.db.session import make_engine, make_sessionmaker
from kubeguide.logging_setup import setup_logging


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
        yield
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

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    return app
