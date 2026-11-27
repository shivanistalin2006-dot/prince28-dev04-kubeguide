import uuid

import pytest
from fastapi.testclient import TestClient

from kubeguide.api.deps import (
    check_db,
    get_gateway,
    get_ingest_repo,
    get_manifest,
    get_queue,
    get_repo,
    get_usage_repo,
)
from kubeguide.api.main import create_app
from kubeguide.config import Settings
from kubeguide.llm.gateway import FakeLLM, LLMGateway
from kubeguide.workers.queue import QueueUnavailableError

# Tiny fake records: unit tests never touch a real database or your data file.
SAMPLE = [
    {
        "id": "001",
        "title": "Alpha guideline",
        "year": 2023,
        "kind": "guideline",
        "pages": [
            {"page_no": 1, "text": "Alpha page 1 content", "headings": ["Introduction"]},
            {"page_no": 2, "text": "Alpha page 2 content", "headings": ["Details"]},
        ],
    },
    {"id": "002", "title": "Beta circular", "year": 2024, "kind": "circular", "pages": []},
    {"id": "003", "title": "Gamma notice", "year": 2025, "kind": "circular", "pages": []},
]


class FakeRepo:
    """Behaves like DocumentRepository, but keeps rows in a Python list."""

    def __init__(self, rows):
        self.rows = rows

    async def list(self, *, q, filters, limit, offset):
        rows = [
            r
            for r in self.rows
            if (not q or q.lower() in str(r).lower())
            and all(str(r.get(k)) == v for k, v in filters.items())
        ]
        return len(rows), rows[offset : offset + limit]

    async def get(self, external_id):
        return next((r for r in self.rows if r["id"] == external_id), None)

    async def get_pages(self, external_id, page_no=None):
        doc = next((r for r in self.rows if r["id"] == external_id), None)
        if not doc:
            return False, None
        pages = doc.get("pages", [])
        if page_no is not None:
            page = next((p for p in pages if p["page_no"] == page_no), None)
            if not page:
                return True, None
            return True, {
                "document_id": external_id,
                "page_no": page["page_no"],
                "text": page["text"],
                "headings": page["headings"],
            }
        return True, pages


class FakeUsageRepo:
    """Fake usage repository for testing /v1/usage without database calls."""

    def __init__(self, days_data=None):
        self.days_data = days_data or [
            {
                "day": "2026-11-25",
                "calls": 5,
                "successful_calls": 5,
                "fallback_calls": 1,
                "tokens_in": 500,
                "tokens_out": 1200,
                "cost_inr": 0.45,
                "p50_latency_ms": 120,
                "p95_latency_ms": 350,
            }
        ]

    async def by_day(self, days=7):
        return self.days_data


class FakeIngestRepo:
    """In-memory replacement for IngestRepository in unit tests."""

    def __init__(self, known=None, dead=None):
        self.known = set(known or ())
        self.dead = list(dead or ())
        self.jobs = {}
        self.items = {}
        self._seq = 0

    async def known_ids(self):
        return set(self.known)

    async def create(self, records):
        job_id = uuid.uuid4().hex
        item_ids = []
        for rec in records:
            self._seq += 1
            item_id = self._seq
            self.items[item_id] = {
                "id": item_id,
                "status": "queued",
                "attempts": 0,
                "pages": 0,
                "error": "",
                "path": rec.get("path", ""),
                "source": rec.get("source", ""),
                "title": rec.get("title", ""),
                "url": rec.get("url", ""),
                "record": dict(rec),
            }
            item_ids.append(item_id)
        self.jobs[job_id] = {"requested": len(records), "item_ids": item_ids}
        return job_id, item_ids

    async def delete_job(self, job_id):
        job = self.jobs.pop(job_id, None)
        if job:
            for item_id in job["item_ids"]:
                self.items.pop(item_id, None)

    async def progress(self, job_id):
        job = self.jobs.get(job_id)
        if not job:
            return None
        items = [self.items[i] for i in job["item_ids"] if i in self.items]
        counts = {"queued": 0, "running": 0, "done": 0, "skipped": 0, "failed": 0}
        pages = 0
        for item in items:
            counts[item["status"]] += 1
            pages += item["pages"]
        return {
            "job_id": job_id,
            "requested": job["requested"],
            **counts,
            "pages": pages,
            "finished": counts["queued"] == 0 and counts["running"] == 0,
            "items": [{k: v for k, v in it.items() if k != "record"} for it in items],
        }

    async def dead_letter(self, limit=50):
        return self.dead[:limit]

    async def failed_records(self):
        return [dict(d["record"]) for d in self.dead if "record" in d]


class FakeQueue:
    """In-memory job queue for API unit tests."""

    def __init__(self, *, fail=False):
        self.fail = fail
        self.enqueued = []

    async def put(self, item_ids):
        if self.fail:
            raise QueueUnavailableError("Redis unavailable")
        self.enqueued.extend(item_ids)

    async def close(self):
        return None


@pytest.fixture
def fake_llm():
    return FakeLLM(
        name="gemini",
        model="gemini-3.8-flash",
        responses=["docs", "To inspect pods, run kubectl get pods -A."],
    )


@pytest.fixture
def fake_gateway(fake_llm):
    fallback = FakeLLM(
        name="groq",
        model="openai/gpt-oss-20b",
        responses=["Fallback response from Groq."],
    )
    return LLMGateway(primary=fake_llm, fallback=fallback)


@pytest.fixture
def llm(fake_llm):
    return fake_llm


@pytest.fixture
def settings():
    # _env_file=None: ignore your local .env so tests behave the same everywhere
    return Settings(
        app_env="ci",
        database_url="postgresql://localhost:5432/unused",
        admin_token="test-admin-token",
        _env_file=None,
    )


@pytest.fixture
def db_state():
    return {"up": True}


@pytest.fixture
def fake_ingest_repo():
    return FakeIngestRepo()


@pytest.fixture
def fake_queue():
    return FakeQueue()


@pytest.fixture
def fake_manifest():
    return [
        {
            "url": "https://github.com/kubernetes/website/blob/HEAD/content/en/docs/a.md",
            "source": "k8s-docs",
            "licence": "CC BY 4.0",
            "title": "A",
            "via": "git",
            "commit": "abc123",
            "path": "data/raw/k8s-docs/a.md",
            "sha256": "a" * 64,
            "status": "downloaded",
        },
        {
            "url": "https://kubernetes.io/docs/b/",
            "source": "kubernetes-io",
            "licence": "CC BY 4.0",
            "title": "B",
            "via": "http",
            "path": "data/raw/kubernetes-io/b.html",
            "sha256": "b" * 64,
            "status": "downloaded",
        },
    ]


@pytest.fixture
def client(settings, db_state, fake_gateway, fake_ingest_repo, fake_queue, fake_manifest):
    app = create_app(settings)
    app.dependency_overrides[get_repo] = lambda: FakeRepo(SAMPLE)
    app.dependency_overrides[check_db] = lambda: db_state["up"]
    app.dependency_overrides[get_gateway] = lambda: fake_gateway
    app.dependency_overrides[get_usage_repo] = lambda: FakeUsageRepo()
    app.dependency_overrides[get_ingest_repo] = lambda: fake_ingest_repo
    app.dependency_overrides[get_queue] = lambda: fake_queue
    app.dependency_overrides[get_manifest] = lambda: fake_manifest
    with TestClient(app) as c:
        yield c
