"""Database storage functions for parsed documents and parse failures."""

import logging
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from kubeguide.db.models import Document, Page, ParseFailure
from kubeguide.ingest.parse import ParsedDoc, ParseError

logger = logging.getLogger(__name__)


async def store_parsed_doc(
    session: AsyncSession,
    doc: ParsedDoc,
    *,
    rel_path: str,
    sha256: str,
    source_url: str | None = None,
    licence: str | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> Document:
    """Save a parsed document and its pages into PostgreSQL.

    Removes any prior parse_failure entry for this path if present.
    """
    # 1. Clean up any previous failure record for this path
    await session.execute(delete(ParseFailure).where(ParseFailure.path == rel_path))

    # 2. Check if document with this external_id already exists
    stmt = select(Document).where(Document.external_id == rel_path)
    existing = (await session.execute(stmt)).scalar_one_or_none()

    doc_metadata: dict[str, Any] = {
        "parser": doc.parser,
        "pages": len(doc.pages),
        "tables": sum(p.tables for p in doc.pages),
    }
    if doc.metadata:
        doc_metadata.update(doc.metadata)
    if extra_metadata:
        doc_metadata.update(extra_metadata)

    if existing is not None:
        existing.title = doc.title
        existing.doc_type = doc.kind
        existing.sha256 = sha256
        existing.source_url = source_url
        existing.licence = licence
        existing.metadata_ = doc_metadata
        # Delete existing pages to replace with freshly parsed pages
        await session.execute(delete(Page).where(Page.document_id == existing.id))
        document = existing
    else:
        document = Document(
            external_id=rel_path,
            title=doc.title,
            source_url=source_url,
            licence=licence,
            doc_type=doc.kind,
            sha256=sha256,
            metadata_=doc_metadata,
        )
        session.add(document)
        await session.flush()  # populate document.id

    for page in doc.pages:
        db_page = Page(
            document_id=document.id,
            page_no=page.page_no,
            text=page.text,
            headings=page.headings,
        )
        session.add(db_page)

    await session.commit()
    return document


async def record_parse_failure(
    session: AsyncSession,
    error: ParseError,
    *,
    rel_path: str,
    sha256: str,
    source_url: str | None = None,
) -> ParseFailure:
    """Record a parsing failure in the parse_failures dead-letter table."""
    stmt = select(ParseFailure).where(ParseFailure.path == rel_path)
    existing = (await session.execute(stmt)).scalar_one_or_none()

    if existing is not None:
        existing.sha256 = sha256
        existing.source_url = source_url
        existing.reason = error.reason
        existing.detail = error.detail
        existing.attempts += 1
        existing.updated_at = func.now()  # type: ignore[assignment]
        failure = existing
    else:
        failure = ParseFailure(
            path=rel_path,
            sha256=sha256,
            source_url=source_url,
            reason=error.reason,
            detail=error.detail,
            attempts=1,
        )
        session.add(failure)

    await session.commit()
    return failure
