import pytest
from sqlalchemy import text

from kubeguide.config import Settings
from kubeguide.db.models import Document
from kubeguide.db.session import make_engine, make_sessionmaker

ROWS = [
    {"id": "001", "title": "Alpha", "kind": "circular", "year": 2024, "tags": ["a", "b"]},
    {"id": "002", "title": "Beta", "kind": "guideline", "year": 2025, "tags": ["b"]},
    {"id": "003", "title": "Gamma", "kind": "circular", "year": 2025, "tags": []},
]


@pytest.fixture
def settings(database_url):
    return Settings(app_env="ci", database_url=database_url, _env_file=None)


@pytest.fixture
async def seeded(settings):
    """Fresh rows for each test: delete, insert, and hand back the settings."""
    engine = make_engine(settings)
    async with make_sessionmaker(engine)() as session, session.begin():
        await session.execute(text("DELETE FROM documents"))
        for r in ROWS:
            meta = {k: v for k, v in r.items() if k not in ("id", "title")}
            session.add(
                Document(external_id=r["id"], title=r["title"], sha256=r["id"] * 21, metadata_=meta)
            )
    await engine.dispose()
    return settings


async def test_migrations_created_the_tables(settings):
    engine = make_engine(settings)
    async with engine.connect() as conn:
        tables = set(
            await conn.scalars(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
            )
        )
        version = await conn.scalar(text("SELECT version_num FROM alembic_version"))
    await engine.dispose()
    assert {"documents", "pages", "alembic_version"} <= tables
    assert version
