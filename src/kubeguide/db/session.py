"""Database engine and session factory setup."""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from kubeguide.config import Settings


def make_engine(settings: Settings) -> AsyncEngine:
    """Build an AsyncEngine configured for Postgres/asyncpg."""
    connect_args = {}
    if "asyncpg" in settings.database_url:
        connect_args["statement_cache_size"] = 0

    return create_async_engine(
        settings.database_url,
        echo=False,
        future=True,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


def make_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Build an async session factory bound to the given engine."""
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
