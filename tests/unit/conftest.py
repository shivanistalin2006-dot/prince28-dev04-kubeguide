import pytest
from fastapi.testclient import TestClient

from kubeguide.api.deps import check_db, get_gateway, get_repo, get_usage_repo
from kubeguide.api.main import create_app
from kubeguide.config import Settings
from kubeguide.llm.gateway import FakeLLM, LLMGateway

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
        _env_file=None,
    )


@pytest.fixture
def db_state():
    return {"up": True}


@pytest.fixture
def client(settings, db_state, fake_gateway):
    app = create_app(settings)
    app.dependency_overrides[get_repo] = lambda: FakeRepo(SAMPLE)
    app.dependency_overrides[check_db] = lambda: db_state["up"]
    app.dependency_overrides[get_gateway] = lambda: fake_gateway
    app.dependency_overrides[get_usage_repo] = lambda: FakeUsageRepo()
    with TestClient(app) as c:
        yield c
