import pytest
from fastapi.testclient import TestClient

from kubeguide.api.deps import check_db, get_repo
from kubeguide.api.main import create_app
from kubeguide.config import Settings

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
def client(settings, db_state):
    app = create_app(settings)
    app.dependency_overrides[get_repo] = lambda: FakeRepo(SAMPLE)
    app.dependency_overrides[check_db] = lambda: db_state["up"]
    with TestClient(app) as c:
        yield c
