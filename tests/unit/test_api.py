import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from kubeguide.api.deps import check_db
from kubeguide.api.main import create_app
from kubeguide.config import Settings


def test_health_is_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["app"] == "kubeguide"
    assert body["env"] == "ci"
    assert body["version"] == "dev"


def test_ready_when_database_up(client):
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"
    assert r.json()["checks"]["database"] is True


def test_ready_is_503_when_database_down(settings, db_state):
    db_state["up"] = False
    app = create_app(settings)
    app.dependency_overrides[check_db] = lambda: db_state["up"]
    with TestClient(app) as c:
        assert c.get("/health").status_code == 200
        r = c.get("/ready")
        assert r.status_code == 503
        assert r.json()["checks"]["database"] is False


def test_list_documents_paginates(client):
    r = client.get("/v1/documents", params={"limit": 2})
    body = r.json()
    assert r.status_code == 200
    assert body["total"] == 3
    assert len(body["items"]) == 2


def test_search_filters_records(client):
    r = client.get("/v1/documents", params={"q": "beta"})
    assert r.status_code == 200
    assert [d["id"] for d in r.json()["items"]] == ["002"]


def test_get_document_found(client):
    r = client.get("/v1/documents/001")
    assert r.status_code == 200
    assert r.json()["title"] == "Alpha guideline"


def test_missing_document_is_problem_details(client):
    r = client.get("/v1/documents/999")
    assert r.status_code == 404
    assert r.headers["content-type"] == "application/problem+json"
    body = r.json()
    assert body["status"] == 404
    assert body["title"] == "Not Found"
    assert body["request_id"] == r.headers["X-Request-ID"]


def test_bad_limit_is_422_problem(client):
    r = client.get("/v1/documents", params={"limit": 0})
    assert r.status_code == 422
    assert r.json()["errors"][0]["field"] == "query.limit"


def test_request_id_is_echoed(client):
    r = client.get("/health", headers={"X-Request-ID": "abc123"})
    assert r.headers["X-Request-ID"] == "abc123"


def test_app_refuses_to_start_without_app_env(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_filter_by_field(client):
    r = client.get("/v1/documents", params={"kind": "circular"})
    body = r.json()
    assert r.status_code == 200
    assert body["total"] == 2
    assert len(body["items"]) == 2
    assert all(item["kind"] == "circular" for item in body["items"])


def test_filter_by_year_integer(client):
    r = client.get("/v1/documents", params={"year": "2023"})
    body = r.json()
    assert r.status_code == 200
    assert body["total"] == 1
    assert body["items"][0]["id"] == "001"


def test_filter_echoes_applied_filters(client):
    r = client.get("/v1/documents", params={"kind": "guideline"})
    body = r.json()
    assert r.status_code == 200
    assert body["filters"] == {"kind": "guideline"}


def test_invalid_filter_name_is_400_problem(client):
    r = client.get("/v1/documents", params={"Bad-Name": "1"})
    assert r.status_code == 400
    assert r.headers["content-type"] == "application/problem+json"
    assert r.json()["status"] == 400


def test_offset_pagination(client):
    r = client.get("/v1/documents", params={"offset": 1, "limit": 2})
    body = r.json()
    assert r.status_code == 200
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["items"][0]["id"] == "002"


def test_empty_search_returns_zero_items(client):
    r = client.get("/v1/documents", params={"q": "nonexistent_query_string"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 0
    assert len(body["items"]) == 0
