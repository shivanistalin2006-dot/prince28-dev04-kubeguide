"""Query and display database statistics for KubeGuide.

Usage:
    uv run python scripts/db_stats.py
"""

import asyncio
import sys
from urllib.parse import urlparse

from sqlalchemy import func, select

from kubeguide.config import get_settings
from kubeguide.db.models import Document, Page, ParseFailure
from kubeguide.db.session import make_engine, make_sessionmaker


async def fetch_db_stats(session) -> dict:
    """Collect document, page, and dead-letter statistics."""
    total_docs = (await session.execute(select(func.count()).select_from(Document))).scalar_one()

    doc_types = (
        await session.execute(select(Document.doc_type, func.count()).group_by(Document.doc_type))
    ).all()

    licences = (
        await session.execute(select(Document.licence, func.count()).group_by(Document.licence))
    ).all()

    total_pages = (await session.execute(select(func.count()).select_from(Page))).scalar_one()

    total_failures = (
        await session.execute(select(func.count()).select_from(ParseFailure))
    ).scalar_one()

    failure_reasons = (
        await session.execute(
            select(ParseFailure.reason, func.count()).group_by(ParseFailure.reason)
        )
    ).all()

    return {
        "total_docs": total_docs,
        "doc_types": doc_types,
        "licences": licences,
        "total_pages": total_pages,
        "total_failures": total_failures,
        "failure_reasons": failure_reasons,
    }


def format_stats_report(stats: dict) -> str:
    """Format collected statistics into a readable console report."""
    lines = [
        f"Total documents: {stats['total_docs']}",
        f"Total pages:     {stats['total_pages']}",
        "Breakdown by document type:",
    ]
    for doc_type, count in stats["doc_types"]:
        lines.append(f"  - {doc_type or 'unspecified'}: {count} records")

    lines.append("Breakdown by licence:")
    for licence, count in stats["licences"]:
        lines.append(f"  - {licence or 'unspecified'}: {count} records")

    lines.append(f"Dead-letter parse failures: {stats['total_failures']}")
    if stats["failure_reasons"]:
        lines.append("Failures by reason:")
        for reason, count in stats["failure_reasons"]:
            lines.append(f"  - {reason}: {count} records")

    return "\n".join(lines)


async def main() -> int:
    settings = get_settings()
    parsed = urlparse(settings.database_url)
    sanitized_host = f"{parsed.hostname}:{parsed.port or 5432}{parsed.path}"

    print(f"Connecting to database at {sanitized_host} (env: {settings.app_env})...")

    engine = make_engine(settings)
    sessionmaker = make_sessionmaker(engine)

    try:
        async with sessionmaker() as session:
            stats = await fetch_db_stats(session)
            print(format_stats_report(stats))

    except Exception as exc:  # noqa: BLE001
        print(f"Database query error: {exc}", file=sys.stderr)
        return 1
    finally:
        await engine.dispose()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
