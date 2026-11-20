"""FastAPI dependency injection providers."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from kubeguide.config import Settings, get_settings
from kubeguide.db.repository import DocumentRepository


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
