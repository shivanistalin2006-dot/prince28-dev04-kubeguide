"""Integration tests for storing parsed documents and parse failures in PostgreSQL."""

import pytest
from sqlalchemy import select

from kubeguide.config import Settings
from kubeguide.db.models import Document, Page, ParseFailure
from kubeguide.db.session import make_engine, make_sessionmaker
from kubeguide.ingest.parse import ParsedDoc, ParsedPage, ParseError
from kubeguide.ingest.store import record_parse_failure, store_parsed_doc


@pytest.fixture
def settings(database_url: str) -> Settings:
    return Settings(app_env="ci", database_url=database_url, _env_file=None)


async def test_store_parsed_doc(settings: Settings) -> None:
    engine = make_engine(settings)
    session_factory = make_sessionmaker(engine)

    doc = ParsedDoc(
        parser="pymupdf",
        kind="pdf",
        title="Pod Security Standards",
        pages=[
            ParsedPage(page_no=1, text="Overview of baseline policies", headings=[]),
            ParsedPage(
                page_no=2,
                text="Privileged containers are restricted",
                headings=["Baseline"],
            ),
        ],
    )

    async with session_factory() as session:
        stored = await store_parsed_doc(
            session,
            doc,
            rel_path="data/raw/k8s/security.pdf",
            sha256="a" * 64,
            source_url="https://kubernetes.io/docs/concepts/security/pod-security-standards/",
        )
        assert stored.id is not None

        # Verify Document row
        db_doc = (
            await session.execute(
                select(Document).where(Document.external_id == "data/raw/k8s/security.pdf")
            )
        ).scalar_one()
        assert db_doc.title == "Pod Security Standards"
        assert db_doc.doc_type == "pdf"
        assert db_doc.metadata_["parser"] == "pymupdf"
        assert db_doc.metadata_["pages"] == 2

        # Verify Page rows
        db_pages = (
            (
                await session.execute(
                    select(Page).where(Page.document_id == db_doc.id).order_by(Page.page_no)
                )
            )
            .scalars()
            .all()
        )
        assert len(db_pages) == 2
        assert db_pages[0].page_no == 1
        assert db_pages[0].headings == []
        assert db_pages[1].page_no == 2
        assert db_pages[1].headings == ["Baseline"]

    await engine.dispose()


async def test_store_parsed_doc_clears_prior_failure(settings: Settings) -> None:
    engine = make_engine(settings)
    session_factory = make_sessionmaker(engine)
    rel_path = "data/raw/k8s/corrupt_then_fixed.pdf"
    sha = "b" * 64

    async with session_factory() as session:
        # 1. Record an initial failure
        await record_parse_failure(
            session,
            ParseError("corrupt", "damaged header"),
            rel_path=rel_path,
            sha256=sha,
        )

        failure_check = (
            await session.execute(select(ParseFailure).where(ParseFailure.path == rel_path))
        ).scalar_one_or_none()
        assert failure_check is not None
        assert failure_check.reason == "corrupt"

        # 2. Later, document is successfully parsed and stored
        doc = ParsedDoc(
            parser="pymupdf",
            kind="pdf",
            title="Recovered Document",
            pages=[ParsedPage(page_no=1, text="Successfully recovered text", headings=[])],
        )
        await store_parsed_doc(session, doc, rel_path=rel_path, sha256=sha)

        # 3. Assert failure was cleared
        failure_after = (
            await session.execute(select(ParseFailure).where(ParseFailure.path == rel_path))
        ).scalar_one_or_none()
        assert failure_after is None

        # Assert document exists
        doc_after = (
            await session.execute(select(Document).where(Document.external_id == rel_path))
        ).scalar_one_or_none()
        assert doc_after is not None

    await engine.dispose()


async def test_record_parse_failure_increments_attempts(settings: Settings) -> None:
    engine = make_engine(settings)
    session_factory = make_sessionmaker(engine)
    rel_path = "data/raw/k8s/scan_only.pdf"
    sha = "c" * 64

    async with session_factory() as session:
        f1 = await record_parse_failure(
            session,
            ParseError("no_text_layer", "10 pages scanned"),
            rel_path=rel_path,
            sha256=sha,
        )
        assert f1.attempts == 1

        f2 = await record_parse_failure(
            session,
            ParseError("no_text_layer", "still no text layer"),
            rel_path=rel_path,
            sha256=sha,
        )
        assert f2.attempts == 2
        assert f2.detail == "still no text layer"

    await engine.dispose()
