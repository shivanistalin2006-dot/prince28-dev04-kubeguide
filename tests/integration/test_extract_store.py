"""Integration test for metadata extraction persistence and pending selection in PostgreSQL."""

import json
import uuid

import pytest
from sqlalchemy import delete, select

from kubeguide.config import Settings
from kubeguide.db.models import Document, Page
from kubeguide.db.session import make_engine, make_sessionmaker
from kubeguide.llm.doc_meta import DocMeta
from kubeguide.llm.extract import pending, run
from kubeguide.llm.gateway import FakeLLM, LLMGateway


@pytest.fixture
def settings(database_url):
    return Settings(app_env="ci", database_url=database_url, _env_file=None)


@pytest.mark.asyncio
async def test_extract_store_roundtrip_and_resumability(settings):
    engine = make_engine(settings)
    session_factory = make_sessionmaker(engine)
    ext_id = f"test-extract-{uuid.uuid4().hex[:8]}"

    valid_json = json.dumps(
        {
            "doc_kind": "concept",
            "year": 2025,
            "language": "en",
            "summary": "Explains Kubernetes Pods and container restart policies.",
            "topics": ["pods", "containers"],
            "section": "concepts",
            "k8s_versions": ["1.30"],
            "object_kinds": ["pod"],
            "error_codes": [],
        }
    )

    try:
        async with session_factory() as session:
            doc = Document(
                external_id=ext_id,
                title="Test Pod Lifecycle",
                doc_type="text",
                sha256="a" * 64,
                metadata_={"parser": "markdown", "pages": 2, "tables": 0},
            )
            session.add(doc)
            await session.flush()
            session.add(
                Page(
                    document_id=doc.id,
                    page_no=1,
                    text=(
                        "Updated in 2025 for Kubernetes 1.30. "
                        "A Pod is the smallest deployable unit."
                    ),
                )
            )
            await session.commit()

        gw = LLMGateway(
            primary=FakeLLM(name="gemini", model="gemini-3.8-flash", responses=[valid_json]),
            fallback=FakeLLM(name="groq"),
        )
        summary = await run(
            session_factory,
            gw,
            "Extract metadata",
            1,
            DocMeta,
            limit=1000,
            rpm=0,
        )
        assert summary["success"] >= 1

        async with session_factory() as session:
            saved = await session.scalar(select(Document).where(Document.external_id == ext_id))
            assert saved is not None
            assert saved.metadata_["parser"] == "markdown"
            assert saved.metadata_["doc_kind"] == "concept"
            assert saved.metadata_["extract"]["prompt"] == "extract_v1"

            # Must not reappear in pending for extract_v1
            rem = await pending(session, "extract_v1")
            assert all(d.external_id != ext_id for d in rem)

            # Should appear in pending for extract_v2
            rem_v2 = await pending(session, "extract_v2")
            assert any(d.external_id == ext_id for d in rem_v2)
    finally:
        async with session_factory() as session:
            await session.execute(delete(Document).where(Document.external_id == ext_id))
            await session.commit()
        await engine.dispose()
