"""Unit tests for RequestContextMiddleware."""

from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from kubeguide.api.middleware import register_middleware


def test_middleware_generates_request_id_and_timing() -> None:
    app = FastAPI()
    register_middleware(app)

    @app.get("/test")
    def endpoint() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) == 16
    assert "X-Process-Time" in response.headers
    assert response.headers["X-Process-Time"].endswith("ms")


def test_middleware_preserves_valid_request_id() -> None:
    app = FastAPI()
    register_middleware(app)

    @app.get("/test")
    def endpoint() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app)
    custom_id = "req-custom-trace-1234"
    response = client.get("/test", headers={"X-Request-ID": custom_id})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id


def test_middleware_replaces_invalid_request_id() -> None:
    app = FastAPI()
    register_middleware(app)

    @app.get("/test")
    def endpoint() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app)
    # Header containing invalid characters (spaces / injection)
    response = client.get("/test", headers={"X-Request-ID": "bad id with spaces!!!"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != "bad id with spaces!!!"
    assert len(response.headers["X-Request-ID"]) == 16


def test_middleware_catches_unhandled_exception() -> None:
    app = FastAPI()
    register_middleware(app)

    @app.get("/crash")
    def crash_endpoint() -> Response:
        msg = "database dropped connection"
        raise RuntimeError(msg)

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/crash")

    assert response.status_code == 500
    body = response.json()
    assert body["title"] == "Internal Server Error"
    assert "X-Request-ID" in response.headers
