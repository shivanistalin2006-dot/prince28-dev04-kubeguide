"""Unit tests for the background worker planning, pacing, downloading, and retry logic."""

from __future__ import annotations

import hashlib

import httpx
import pytest
from arq.constants import in_progress_key_prefix, job_key_prefix, result_key_prefix

from kubeguide.config import Settings
from kubeguide.workers.ingest import Pace, Permanent, get_file, plan, raw_url
from kubeguide.workers.main import (
    WorkerSettings,
    create_embedded_worker,
    requeue_unfinished,
    shutdown,
    startup,
)


def test_plan_filters_downloaded_source_duplicates_and_limit():
    records = [
        {"url": "u1", "source": "s1", "sha256": "a" * 64, "status": "failed"},
        {"url": "u2", "source": "s2", "sha256": "b" * 64, "status": "downloaded"},
        {"url": "u3", "source": "s1", "sha256": "c" * 64, "status": "downloaded"},
        {"url": "u4", "source": "s1", "sha256": "c" * 64, "status": "downloaded"},  # dup hash
        {"url": "u5", "source": "s1", "sha256": "d" * 64, "status": "downloaded"},  # done
        {"url": "u6", "source": "s1", "sha256": "e" * 64, "status": "downloaded"},
        {"url": "u7", "source": "s1", "sha256": "f" * 64, "status": "downloaded"},
    ]
    todo = plan(records, {"d" * 64}, source="s1", limit=2)
    assert [r["url"] for r in todo] == ["u3", "u6"]


def test_raw_url_pins_github_git_commit():
    rec = {
        "url": "https://github.com/kubernetes/website/blob/HEAD/content/en/docs/pods.md",
        "via": "git",
        "commit": "deadbeef1234",  # pragma: allowlist secret
    }
    assert (
        raw_url(rec)
        == "https://raw.githubusercontent.com/kubernetes/website/deadbeef1234/content/en/docs/pods.md"
    )
    http_rec = {"url": "https://kubernetes.io/docs/pods/", "via": "http"}
    assert raw_url(http_rec) == "https://kubernetes.io/docs/pods/"


@pytest.mark.asyncio
async def test_pace_enforces_shared_interval():
    now = 100.0
    slept: list[float] = []

    def clock() -> float:
        return now

    async def fake_sleep(delay: float) -> None:
        nonlocal now
        slept.append(delay)
        now += delay

    pace = Pace(12.0, clock=clock, sleep=fake_sleep)  # 5.0s gap
    await pace.wait()
    await pace.wait()
    await pace.wait()

    assert slept == [5.0, 5.0]


@pytest.mark.asyncio
async def test_get_file_uses_local_disk_when_present(tmp_path):
    target = tmp_path / "doc.md"
    target.write_text("# Pod\nHello", encoding="utf-8")
    rec = {"path": str(target), "url": "https://example.com/doc.md", "source": "s1"}

    async with httpx.AsyncClient() as client:
        out = await get_file(rec, tmp_path / "dl", client)
    assert out == target


@pytest.mark.asyncio
async def test_get_file_manual_missing_from_disk_is_permanent(tmp_path):
    rec = {
        "path": str(tmp_path / "missing.pdf"),
        "url": "https://example.com/missing.pdf",
        "source": "manual-src",
        "via": "manual",
    }
    async with httpx.AsyncClient() as client:
        with pytest.raises(Permanent, match="downloaded by hand"):
            await get_file(rec, tmp_path / "dl", client)


@pytest.mark.asyncio
async def test_get_file_downloads_from_exact_git_commit(tmp_path):
    body = b"# Pods\nKubernetes Pods"
    seen_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        return httpx.Response(200, content=body, headers={"Content-Type": "text/markdown"})

    async def no_sleep(_: float) -> None:
        return None

    rec = {
        "path": str(tmp_path / "not_here.md"),
        "url": "https://github.com/kubernetes/website/blob/HEAD/content/en/docs/pods.md",
        "via": "git",
        "commit": "bc2d2df8e3c4",  # pragma: allowlist secret
        "source": "k8s-docs",
        "licence": "CC BY 4.0",
        "sha256": hashlib.sha256(body).hexdigest(),
    }
    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        downloaded = await get_file(rec, tmp_path / "dl", client, sleep=no_sleep)

    assert downloaded.read_bytes() == body
    assert (
        "https://raw.githubusercontent.com/kubernetes/website/bc2d2df8e3c4/content/en/docs/pods.md"
        in seen_urls
    )


@pytest.mark.asyncio
async def test_get_file_distinguishes_permanent_404_and_retryable_503(tmp_path):
    def make_transport(status_code: int) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/robots.txt":
                return httpx.Response(200, text="User-agent: *\nAllow: /\n")
            return httpx.Response(status_code, text="error")

        return httpx.MockTransport(handler)

    async def no_sleep(_: float) -> None:
        return None

    rec = {
        "path": str(tmp_path / "missing.md"),
        "url": "https://example.com/missing.md",
        "via": "http",
        "source": "example",
        "licence": "CC BY 4.0",
    }

    async with httpx.AsyncClient(transport=make_transport(404)) as client_404:
        with pytest.raises(Permanent, match="download failed"):
            await get_file(rec, tmp_path / "dl1", client_404, sleep=no_sleep)

    async with httpx.AsyncClient(transport=make_transport(503)) as client_503:
        with pytest.raises(RuntimeError, match="download failed"):
            await get_file(rec, tmp_path / "dl2", client_503, sleep=no_sleep)


class _FakeArqRedis:
    """Minimal in-memory ARQ Redis stub reproducing enqueue_job key blocking semantics."""

    def __init__(self, initial_keys: set[str] | None = None) -> None:
        self.keys: set[str] = set(initial_keys or ())
        self.enqueued: list[tuple[str, int, str]] = []

    async def exists(self, *names: str) -> int:
        return sum(1 for name in names if name in self.keys)

    async def delete(self, *names: str) -> int:
        removed = 0
        for name in names:
            if name in self.keys:
                self.keys.remove(name)
                removed += 1
        return removed

    async def enqueue_job(
        self,
        function: str,
        item_id: int,
        *,
        _job_id: str,
    ) -> str | None:
        job_key = job_key_prefix + _job_id
        result_key = result_key_prefix + _job_id
        if job_key in self.keys or result_key in self.keys:
            return None
        self.keys.add(job_key)
        self.enqueued.append((function, item_id, _job_id))
        return _job_id


def test_worker_settings_disables_stale_result_retention():
    assert WorkerSettings.keep_result == 0
    s = Settings(
        app_env="ci",
        database_url="postgresql://localhost:5432/unused",
        _env_file=None,
    )
    worker = create_embedded_worker(s)
    assert worker.keep_result_s == 0
    assert worker.keep_result_forever is False


@pytest.mark.asyncio
async def test_requeue_unfinished_clears_only_stale_result_key():
    redis = _FakeArqRedis(
        initial_keys={
            f"{result_key_prefix}ingest:38",  # stale result blocking recovery
            f"{result_key_prefix}ingest:99",  # unrelated job result
            f"{job_key_prefix}ingest:40",  # genuinely still queued
            f"{result_key_prefix}ingest:41",  # active in-progress item
            f"{in_progress_key_prefix}ingest:41",
        }
    )

    requeued = await requeue_unfinished(redis, [38, 40, 41, 42])

    assert requeued == 2
    assert redis.enqueued == [
        ("ingest_document", 38, "ingest:38"),
        ("ingest_document", 42, "ingest:42"),
    ]
    assert f"{result_key_prefix}ingest:38" not in redis.keys
    assert f"{job_key_prefix}ingest:38" in redis.keys
    # Unrelated, queued, and in-progress keys remain untouched
    assert f"{result_key_prefix}ingest:99" in redis.keys
    assert f"{job_key_prefix}ingest:40" in redis.keys
    assert f"{result_key_prefix}ingest:41" in redis.keys
    assert f"{in_progress_key_prefix}ingest:41" in redis.keys


@pytest.mark.asyncio
async def test_startup_requeues_unfinished_item_with_stale_result(monkeypatch):
    class _FakeEngine:
        def __init__(self) -> None:
            self.disposed = False

        async def dispose(self) -> None:
            self.disposed = True

    class _FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args) -> None:
            return None

    class _FakeRepo:
        def __init__(self, session) -> None:
            self.session = session

        async def unfinished_items(self, timeout_seconds: int) -> list[int]:
            assert timeout_seconds == 60
            return [38]

    fake_engine = _FakeEngine()
    monkeypatch.setattr("kubeguide.workers.main.make_engine", lambda s: fake_engine)
    monkeypatch.setattr("kubeguide.workers.main.make_sessionmaker", lambda e: _FakeSession)
    monkeypatch.setattr("kubeguide.workers.main.IngestRepository", _FakeRepo)

    redis = _FakeArqRedis(initial_keys={f"{result_key_prefix}ingest:38"})
    settings = Settings(
        app_env="ci",
        database_url="postgresql://localhost:5432/unused",
        ingest_job_timeout=60,
        _env_file=None,
    )
    ctx = {"settings": settings, "embedded": True, "redis": redis}

    await startup(ctx)
    try:
        assert redis.enqueued == [("ingest_document", 38, "ingest:38")]
        assert f"{result_key_prefix}ingest:38" not in redis.keys
    finally:
        await shutdown(ctx)

    assert fake_engine.disposed is True
