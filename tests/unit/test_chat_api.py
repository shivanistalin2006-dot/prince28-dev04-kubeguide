"""Unit tests for /v1/chat streaming, /v1/usage accounting, and system prompt guardrails."""

from pathlib import Path

from fastapi.testclient import TestClient

from kubeguide.api.deps import get_gateway
from kubeguide.api.main import create_app
from kubeguide.llm.gateway import FakeLLM, LLMGateway, ProviderError


def test_system_prompt_contains_guardrails():
    prompt_path = Path("prompts/chat_system_v1.md")
    assert prompt_path.exists(), "prompts/chat_system_v1.md must exist"
    content = prompt_path.read_text(encoding="utf-8")
    err_msg = "Prompt must instruct model to say 'I am not sure' instead of guessing"
    assert "I am not sure" in content, err_msg


def test_chat_non_streaming_json(client: TestClient):
    resp = client.post(
        "/v1/chat",
        json={"prompt": "How do I list pods?", "stream": False},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    assert "kubectl" in data["response"]
    assert data["provider"] == "gemini"
    assert data["fallback_used"] is False
    assert data["tokens_in"] > 0
    assert data["tokens_out"] > 0


def test_chat_streaming_sse(client: TestClient):
    resp = client.post(
        "/v1/chat",
        json={"prompt": "How do I list pods?", "stream": True},
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    text = resp.text
    assert "data:" in text
    assert "kubectl" in text
    assert "pods" in text
    assert '"done": true' in text.lower()


def test_chat_with_multi_turn_history(client: TestClient):
    history = [
        {"role": "user", "content": "What is a Pod?"},
        {"role": "assistant", "content": "A Pod is the smallest deployable unit in Kubernetes."},
    ]
    resp = client.post(
        "/v1/chat",
        json={
            "prompt": "How many containers can run in one?",
            "history": history,
            "stream": False,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["response"] != ""


def test_chat_request_with_message_field(client: TestClient):
    resp = client.post(
        "/v1/chat",
        json={"message": "What is an Ingress?", "stream": False},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    assert "answer" in data
    assert data["answer"] == data["response"]
    assert "tokens" in data
    assert data["tokens"]["in"] > 0
    assert data["is_fallback"] is False


def test_chat_streaming_chunks_have_chunk_alias(client: TestClient):
    resp = client.post(
        "/v1/chat",
        json={"message": "Explain Pod", "stream": True},
    )
    assert resp.status_code == 200
    assert '"chunk":' in resp.text
    assert '"is_fallback":' in resp.text


def test_chat_validation_error(client: TestClient):
    resp = client.post("/v1/chat", json={"prompt": ""})
    assert resp.status_code == 422


def test_chat_service_unavailable_when_all_fail(settings):
    primary_errors = [
        ProviderError("gemini", 500, "Crash"),
        ProviderError("gemini", 500, "Crash"),
    ]
    fallback_errors = [
        ProviderError("groq", 503, "Unavailable"),
        ProviderError("groq", 503, "Unavailable"),
    ]
    primary = FakeLLM(name="gemini", errors=primary_errors)
    fallback = FakeLLM(name="groq", errors=fallback_errors)
    failing_gateway = LLMGateway(primary=primary, fallback=fallback)

    app = create_app(settings)
    app.dependency_overrides[get_gateway] = lambda: failing_gateway

    with TestClient(app) as test_client:
        # Non-streaming
        resp = test_client.post("/v1/chat", json={"prompt": "crash", "stream": False})
        assert resp.status_code == 503

        # Streaming
        resp_stream = test_client.post("/v1/chat", json={"prompt": "crash", "stream": True})
        assert resp_stream.status_code == 503


def test_usage_endpoint(client: TestClient):
    resp = client.get("/v1/usage?days=7")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "day" in data[0]
    assert "calls" in data[0]
    assert "cost_inr" in data[0]


def test_llm_status_endpoint(client: TestClient):
    resp = client.get("/v1/llm/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "primary" in data
    assert "fallback" in data
    assert data["primary"]["circuit_breaker"] in ("closed", "open", "half-open")


def test_chat_routes_personal_without_second_llm_call(settings):
    primary = FakeLLM(
        name="gemini",
        model="gemini-3.8-flash",
        responses=["personal", "SHOULD NOT BE CALLED"],
    )
    gateway = LLMGateway(primary=primary, fallback=FakeLLM(name="groq"))
    app = create_app(settings)
    app.dependency_overrides[get_gateway] = lambda: gateway

    with TestClient(app) as test_client:
        resp = test_client.post(
            "/v1/chat",
            json={"message": "Is our production cluster healthy right now?", "stream": False},
        )
    assert resp.status_code == 200
    assert "cannot access live cluster health" in resp.json()["answer"]
    assert primary.call_count == 1


def test_chat_routes_off_topic_without_second_llm_call(settings):
    primary = FakeLLM(
        name="gemini",
        model="gemini-3.8-flash",
        responses=["off_topic", "SHOULD NOT BE CALLED"],
    )
    gateway = LLMGateway(primary=primary, fallback=FakeLLM(name="groq"))
    app = create_app(settings)
    app.dependency_overrides[get_gateway] = lambda: gateway

    with TestClient(app) as test_client:
        resp = test_client.post(
            "/v1/chat",
            json={"message": "Who won the 2011 cricket world cup?", "stream": True},
        )
    assert resp.status_code == 200
    assert "outside my Kubernetes scope" in resp.text
    assert primary.call_count == 1
