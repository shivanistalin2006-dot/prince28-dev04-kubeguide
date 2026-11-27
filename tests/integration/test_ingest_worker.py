"""Integration tests for the ingestion worker, persistence, idempotency, and crash recovery."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from arq import Retry
from sqlalchemy import delete, func, select

from kubeguide.config import Settings
from kubeguide.db.ingest_jobs import IngestRepository
from kubeguide.db.models import Document, IngestItem, IngestJob, ParseFailure
from kubeguide.db.session import make_engine, make_sessionmaker
from kubeguide.llm.doc_meta import DocMeta
from kubeguide.llm.gateway import FakeLLM, LLMGateway
from kubeguide.workers.ingest import Pace, ingest_document


@pytest.fixture
def settings(database_url: str) -> Settings:
    return Settings(
        app_env="ci",
        database_url=database_url,
        ingest_max_tries=3,
        ingest_job_timeout=60,
        _env_file=None,
    )


def _valid_meta_json() -> str:
    return json.dumps(
        {
            "doc_kind": "concept",
            "year": 2025,
            "language": "en",
            "summary": "Explains Kubernetes Pods and container lifecycle.",
            "topics": ["pods", "lifecycle"],
            "section": "concepts",
            "k8s_versions": ["1.30"],
            "object_kinds": ["pod"],
            "error_codes": [],
        }
    )


@pytest.mark.asyncio
async def test_worker_ingests_parses_extracts_and_is_idempotent(settings: Settings, tmp_path):
    engine = make_engine(settings)
    sessionmaker = make_sessionmaker(engine)

    doc_file = tmp_path / "pod.md"
    content = "# Pod Overview\n\nUpdated in 2025 for Kubernetes 1.30.\nA Pod runs containers."
    doc_file.write_text(content, encoding="utf-8")
    sha = hashlib.sha256(doc_file.read_bytes()).hexdigest()

    rec = {
        "url": "https://kubernetes.io/docs/concepts/workloads/pods/",
        "source": "kubernetes-io",
        "licence": "CC BY 4.0",
        "title": "Pod Overview",
        "via": "http",
        "path": str(doc_file),
        "sha256": sha,
        "status": "downloaded",
    }

    gw = LLMGateway(
        primary=FakeLLM(name="gemini", model="gemini-3.8-flash", responses=[_valid_meta_json()]),
        fallback=FakeLLM(name="groq"),
    )
    ctx = {
        "settings": settings,
        "sessionmaker": sessionmaker,
        "http": httpx.AsyncClient(),
        "pace": Pace(0),
        "gateway": gw,
        "extract": {
            "version": "extract_v1",
            "prompt": "Extract metadata",
            "schema": DocMeta,
            "chars": 6000,
        },
    }

    try:
        async with sessionmaker() as session:
            repo = IngestRepository(session)
            job_id, item_ids = await repo.create([rec])

        status1 = await ingest_document(ctx, item_ids[0])
        assert status1 == "done"

        async with sessionmaker() as session:
            doc_count = await session.scalar(
                select(func.count()).select_from(Document).where(Document.sha256 == sha)
            )
            assert doc_count == 1
            stored = await session.scalar(select(Document).where(Document.sha256 == sha))
            assert stored is not None
            assert stored.metadata_["doc_kind"] == "concept"
            assert stored.metadata_["extract"]["prompt"] == "extract_v1"

            # Second job with same content hash must skip without duplicating Document
            repo = IngestRepository(session)
            assert sha in await repo.known_ids()
            _, item_ids2 = await repo.create([rec])

        status2 = await ingest_document(ctx, item_ids2[0])
        assert status2 == "skipped"

        async with sessionmaker() as session:
            doc_count_after = await session.scalar(
                select(func.count()).select_from(Document).where(Document.sha256 == sha)
            )
            assert doc_count_after == 1
    finally:
        await ctx["http"].aclose()
        async with sessionmaker() as session:
            await session.execute(delete(Document).where(Document.sha256 == sha))
            await session.execute(delete(IngestJob))
            await session.commit()
        await engine.dispose()


@pytest.mark.asyncio
async def test_worker_permanent_parse_failure_and_retryable_recovery(settings: Settings, tmp_path):
    engine = make_engine(settings)
    sessionmaker = make_sessionmaker(engine)

    empty_file = tmp_path / "empty.md"
    empty_file.write_text("   \n", encoding="utf-8")
    empty_sha = hashlib.sha256(empty_file.read_bytes()).hexdigest()

    permanent_rec = {
        "url": "https://example.com/empty.md",
        "source": "example",
        "licence": "CC BY 4.0",
        "via": "http",
        "path": str(empty_file),
        "sha256": empty_sha,
        "status": "downloaded",
    }
    transient_rec = {
        "url": "https://example.com/flaky.md",
        "source": "example",
        "licence": "CC BY 4.0",
        "via": "http",
        "path": str(tmp_path / "missing_flaky.md"),
        "sha256": "e" * 64,
        "status": "downloaded",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        return httpx.Response(503, text="upstream busy")

    ctx = {
        "settings": settings,
        "sessionmaker": sessionmaker,
        "http": httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        "pace": Pace(0),
        "gateway": LLMGateway(primary=FakeLLM(), fallback=FakeLLM()),
        "extract": None,
    }

    try:
        async with sessionmaker() as session:
            repo = IngestRepository(session)
            _, ids = await repo.create([permanent_rec, transient_rec])

        # Permanent error goes straight to failed without Retry
        res_perm = await ingest_document(ctx, ids[0])
        assert res_perm == "failed"

        # Retryable error raises Retry twice, then gives up on 3rd attempt
        with pytest.raises(Retry):
            await ingest_document(ctx, ids[1])
        with pytest.raises(Retry):
            await ingest_document(ctx, ids[1])
        res_final = await ingest_document(ctx, ids[1])
        assert res_final == "failed"

        async with sessionmaker() as session:
            item_perm = await session.get(IngestItem, ids[0])
            item_trans = await session.get(IngestItem, ids[1])
            assert item_perm is not None and item_perm.attempts == 1
            assert item_perm.error.startswith("parse:")
            assert item_trans is not None and item_trans.attempts == 3
            assert item_trans.error.startswith("gave up after 3 tries:")
    finally:
        await ctx["http"].aclose()
        async with sessionmaker() as session:
            await session.execute(delete(ParseFailure).where(ParseFailure.sha256 == empty_sha))
            await session.execute(delete(IngestJob))
            await session.commit()
        await engine.dispose()


@pytest.mark.asyncio
async def test_worker_recovers_abandoned_running_items_and_persists_attempts(
    settings: Settings, tmp_path
):
    engine = make_engine(settings)
    sessionmaker = make_sessionmaker(engine)

    doc_file = tmp_path / "recover.md"
    doc_file.write_text("# Recovery\n\nContent survives crash.", encoding="utf-8")
    sha = hashlib.sha256(doc_file.read_bytes()).hexdigest()

    rec = {
        "url": "https://example.com/recover.md",
        "source": "example",
        "licence": "CC BY 4.0",
        "via": "http",
        "path": str(doc_file),
        "sha256": sha,
        "status": "downloaded",
    }

    ctx = {
        "settings": settings,
        "sessionmaker": sessionmaker,
        "http": httpx.AsyncClient(),
        "pace": Pace(0),
        "gateway": LLMGateway(primary=FakeLLM(), fallback=FakeLLM()),
        "extract": None,
    }

    try:
        async with sessionmaker() as session:
            repo = IngestRepository(session)
            _, ids = await repo.create([rec])
            # Simulate worker dying mid-item: status='running', attempts=1, old updated_at
            item = await session.get(IngestItem, ids[0])
            assert item is not None
            item.status = "running"
            item.attempts = 1
            item.updated_at = datetime.now(UTC) - timedelta(seconds=120)
            await session.commit()

            recovered = await repo.unfinished_items(timeout_seconds=60)
            assert ids[0] in recovered

            item_after = await session.get(IngestItem, ids[0])
            assert item_after is not None and item_after.status == "queued"

        final_status = await ingest_document(ctx, ids[0])
        assert final_status == "done"

        async with sessionmaker() as session:
            item_done = await session.get(IngestItem, ids[0])
            assert item_done is not None
            assert item_done.attempts == 2
            assert item_done.status == "done"
    finally:
        await ctx["http"].aclose()
        async with sessionmaker() as session:
            await session.execute(delete(Document).where(Document.sha256 == sha))
            await session.execute(delete(IngestJob))
            await session.commit()
        await engine.dispose()
