"""Integration tests on a real PostgreSQL database."""

import os

import pytest
from sqlalchemy import text

from kubeguide.config import Settings
from kubeguide.db.session import make_engine

TEST_DB_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not TEST_DB_URL,
    reason="TEST_DATABASE_URL is not set",
)


@pytest.fixture
def db_engine():
    settings = Settings(app_env="ci", database_url=TEST_DB_URL, _env_file=None)
    engine = make_engine(settings)
    yield engine


@pytest.mark.anyio
async def test_real_db_connection(db_engine):
    async with db_engine.connect() as conn:
        val = (await conn.execute(text("SELECT 1"))).scalar()
        assert val == 1


@pytest.mark.anyio
async def test_real_db_documents_table_exists(db_engine):
    async with db_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables WHERE table_name = 'documents'"
            )
        )
        assert result.scalar() == "documents"


@pytest.mark.anyio
async def test_real_db_pages_table_exists(db_engine):
    async with db_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_name = 'pages'")
        )
        assert result.scalar() == "pages"
