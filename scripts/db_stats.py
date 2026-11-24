"""Query and display database statistics for KubeGuide.

Usage:
    uv run python scripts/db_stats.py
"""

import asyncio
import sys
from urllib.parse import urlparse

from sqlalchemy import func, select

from kubeguide.config import get_settings
from kubeguide.db.models import Document
from kubeguide.db.session import make_engine, make_sessionmaker


async def main() -> int:
    settings = get_settings()
    parsed = urlparse(settings.database_url)
    sanitized_host = f"{parsed.hostname}:{parsed.port or 5432}{parsed.path}"

    print(f"Connecting to database at {sanitized_host} (env: {settings.app_env})...")

    engine = make_engine(settings)
    sessionmaker = make_sessionmaker(engine)

    try:
        async with sessionmaker() as session:
            count_query = select(func.count()).select_from(Document)
            total_docs = (await session.execute(count_query)).scalar_one()

            source_query = select(Document.source, func.count()).group_by(Document.source)
            sources = (await session.execute(source_query)).all()

        print(f"Total documents: {total_docs}")
        print("Breakdown by source:")
        for source, count in sources:
            print(f"  - {source}: {count} records")

    except Exception as exc:  # noqa: BLE001
        print(f"Database query error: {exc}", file=sys.stderr)
        return 1
    finally:
        await engine.dispose()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
