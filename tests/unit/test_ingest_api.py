"""Unit tests for POST /v1/ingest, GET /v1/ingest/{job_id}, and GET /v1/ingest/dead-letter."""

from __future__ import annotations

from fastapi.testclient import TestClient

from kubeguide.api.deps import get_ingest_repo, get_manifest, get_queue
from kubeguide.api.main import create_app
from kubeguide.config import Settings
from tests.unit.conftest import FakeIngestRepo, FakeQueue


def test_ingest_post_requires_admin_token(client: TestClient):
    r_missing = client.post("/v1/ingest", json={"limit": 5})
    assert r_missing.status_code == 401

    r_wrong = client.post(
        "/v1/ingest",
        json={"limit": 5},
        headers={"X-Admin-Token": "wrong-token"},
    )
    assert r_wrong.status_code == 401


def test_ingest_post_returns_403_when_admin_token_unconfigured():
    s = Settings(
        app_env="ci",
        database_url="postgresql://localhost:5432/unused",
        admin_token="",
        _env_file=None,
    )
    app = create_app(s)
    app.dependency_overrides[get_ingest_repo] = lambda: FakeIngestRepo()
    app.dependency_overrides[get_queue] = lambda: FakeQueue()
    app.dependency_overrides[get_manifest] = lambda: []
    with TestClient(app) as c:
        r = c.post("/v1/ingest", json={"limit": 5}, headers={"X-Admin-Token": "anything"})
        assert r.status_code == 403


def test_ingest_post_accepts_202_and_progress_returns_counts(
    client: TestClient,
    fake_ingest_repo: FakeIngestRepo,
    fake_queue: FakeQueue,
):
    r = client.post(
        "/v1/ingest",
        json={"limit": 10},
        headers={"X-Admin-Token": "test-admin-token"},
    )
    assert r.status_code == 202
    body = r.json()
    assert body["queued"] == 2
    assert body["job_id"]
    assert body["status_url"] == f"/v1/ingest/{body['job_id']}"
    assert len(fake_queue.enqueued) == 2

    # Progress endpoint must not require X-Admin-Token
    prog = client.get(body["status_url"])
    assert prog.status_code == 200
    pbody = prog.json()
    assert pbody["job_id"] == body["job_id"]
    assert pbody["queued"] == 2
    assert pbody["running"] == 0
    assert pbody["done"] == 0
    assert pbody["failed"] == 0
    assert pbody["finished"] is False


def test_ingest_post_nothing_to_do_returns_200(
    client: TestClient,
    fake_ingest_repo: FakeIngestRepo,
    fake_queue: FakeQueue,
):
    fake_ingest_repo.known.update({"a" * 64, "b" * 64})
    r = client.post(
        "/v1/ingest",
        json={"limit": 10},
        headers={"X-Admin-Token": "test-admin-token"},
    )
    assert r.status_code == 200
    assert r.json()["job_id"] is None
    assert r.json()["queued"] == 0
    assert fake_queue.enqueued == []


def test_ingest_post_redis_unavailable_returns_503(
    client: TestClient,
    fake_ingest_repo: FakeIngestRepo,
    fake_queue: FakeQueue,
):
    fake_queue.fail = True
    r = client.post(
        "/v1/ingest",
        json={"limit": 10},
        headers={"X-Admin-Token": "test-admin-token"},
    )
    assert r.status_code == 503
    assert "Redis" in r.json()["detail"]
    # Job must be cleaned up when Redis enqueue fails
    assert fake_ingest_repo.jobs == {}


def test_ingest_progress_unknown_job_is_404(client: TestClient):
    r = client.get("/v1/ingest/nonexistent-job-id")
    assert r.status_code == 404
    assert r.headers["content-type"] == "application/problem+json"


def test_ingest_dead_letter_returns_failed_items_and_retry_failed_queues(
    client: TestClient,
    fake_ingest_repo: FakeIngestRepo,
    fake_queue: FakeQueue,
):
    fake_ingest_repo.dead.append(
        {
            "item_id": 99,
            "job_id": "job-1",
            "status": "failed",
            "attempts": 3,
            "error": "parse: no_text_layer",
            "path": "data/raw/x/scan.pdf",
            "url": "https://example.com/scan.pdf",
            "source": "x",
            "sha256": "c" * 64,
            "record": {
                "path": "data/raw/x/scan.pdf",
                "url": "https://example.com/scan.pdf",
                "source": "x",
                "sha256": "c" * 64,
                "status": "downloaded",
            },
        }
    )

    # Dead-letter GET does not require admin token
    dl = client.get("/v1/ingest/dead-letter")
    assert dl.status_code == 200
    assert dl.json()["count"] == 1
    assert dl.json()["items"][0]["error"] == "parse: no_text_layer"

    # retry_failed queues dead-letter items
    r = client.post(
        "/v1/ingest",
        json={"limit": 10, "retry_failed": True},
        headers={"X-Admin-Token": "test-admin-token"},
    )
    assert r.status_code == 202
    assert r.json()["queued"] == 1
    assert len(fake_queue.enqueued) == 1


def test_ingest_source_filter(client: TestClient):
    r = client.post(
        "/v1/ingest",
        json={"limit": 10, "source": "kubernetes-io"},
        headers={"X-Admin-Token": "test-admin-token"},
    )
    assert r.status_code == 202
    assert r.json()["queued"] == 1


def test_worker_in_api_flag_controls_embedded_worker(monkeypatch):
    started = {"called": False}

    class DummyWorker:
        async def async_run(self):
            started["called"] = True

        async def close(self):
            return None

    monkeypatch.setattr("kubeguide.api.main.create_embedded_worker", lambda s: DummyWorker())

    s_off = Settings(
        app_env="ci",
        database_url="postgresql://localhost:5432/unused",
        worker_in_api=False,
        _env_file=None,
    )
    with TestClient(create_app(s_off)):
        pass
    assert started["called"] is False

    s_on = Settings(
        app_env="ci",
        database_url="postgresql://localhost:5432/unused",
        worker_in_api=True,
        _env_file=None,
    )
    with TestClient(create_app(s_on)):
        pass
    assert started["called"] is True
