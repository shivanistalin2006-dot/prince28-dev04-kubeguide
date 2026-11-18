"""Verify database connectivity."""

import asyncio

from sqlalchemy import text

from kubeguide.config import get_settings
from kubeguide.db.session import make_engine


async def main() -> None:
    settings = get_settings()
    engine = make_engine(settings)
    async with engine.connect() as conn:
        version = (await conn.execute(text("SELECT version()"))).scalar()
        current_db = (await conn.execute(text("SELECT current_database()"))).scalar()
        print(f"Connected to database '{current_db}' {version}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
