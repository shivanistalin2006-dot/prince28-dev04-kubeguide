"""FastAPI dependency injection providers."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from kubeguide.config import Settings, get_settings
from kubeguide.db.llm_calls import LlmUsageRepository
from kubeguide.db.repository import DocumentRepository
from kubeguide.llm.gateway import LLMGateway, build_gateway


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


def get_gateway(request: Request) -> LLMGateway:
    """Dependency providing an LLMGateway instance."""
    gateway = getattr(request.app.state, "gateway", None)
    if gateway is None:
        settings = get_app_settings(request)
        gateway = build_gateway(settings)
    return gateway


GatewayDep = Annotated[LLMGateway, Depends(get_gateway)]
UsageDep = Annotated[LlmUsageRepository, Depends(get_usage_repo)]


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
