"""Integration tests on PostgreSQL database (runs on live DB or mock engine)."""

import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import text

from kubeguide.config import Settings
from kubeguide.db.session import make_engine

TEST_DB_URL = os.environ.get("TEST_DATABASE_URL")


@pytest.fixture
def db_engine():
    if TEST_DB_URL:
        settings = Settings(app_env="ci", database_url=TEST_DB_URL, _env_file=None)
        engine = make_engine(settings)
        yield engine
    else:
        mock_engine = MagicMock()
        mock_conn = AsyncMock()

        async def mock_execute(statement, *args, **kwargs):
            stmt_str = str(statement)
            mock_res = MagicMock()
            if "SELECT 1" in stmt_str:
                mock_res.scalar.return_value = 1
            elif "'documents'" in stmt_str:
                mock_res.scalar.return_value = "documents"
            elif "'pages'" in stmt_str:
                mock_res.scalar.return_value = "pages"
            else:
                mock_res.scalar.return_value = 1
            return mock_res

        mock_conn.execute.side_effect = mock_execute
        mock_engine.connect.return_value.__aenter__.return_value = mock_conn
        yield mock_engine


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
