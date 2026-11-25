"""Unit tests for the LLM Gateway, pricing formulas, circuit breaker, and fallback logic."""

import pytest

from kubeguide.llm.gateway import (
    AllProvidersFailedError,
    CircuitBreaker,
    FakeLLM,
    LLMGateway,
    OpenAICompatProvider,
    ProviderError,
    cost_inr,
)


def test_cost_inr_calculation():
    # gemini-3.8-flash: input 0.75 / M, output 3.75 / M, USD/INR = 86.0
    # 1000 input tokens = 0.00075 USD = 0.0645 INR
    # 1000 output tokens = 0.00375 USD = 0.3225 INR
    # Total = 0.387 INR
    cost = cost_inr("gemini-3.8-flash", 1000, 1000, usd_inr=86.0)
    assert cost == pytest.approx(0.387, rel=1e-3)

    # openai/gpt-oss-20b: input 0.075 / M, output 0.30 / M
    cost_groq = cost_inr("openai/gpt-oss-20b", 10000, 10000, usd_inr=86.0)
    # (10000*0.075 + 10000*0.30) / 1M * 86 = 3.75 / 100 * 86 = 0.3225 INR
    assert cost_groq == pytest.approx(0.3225, rel=1e-3)


def test_circuit_breaker_lifecycle():
    breaker = CircuitBreaker("test-breaker", failure_threshold=2, cooldown_seconds=0.1)
    assert breaker.state == "closed"
    assert breaker.can_attempt() is True

    # First failure: still closed
    breaker.record_failure()
    assert breaker.state == "closed"
    assert breaker.can_attempt() is True

    # Second failure: trips to open
    breaker.record_failure()
    assert breaker.state == "open"
    assert breaker.can_attempt() is False

    # After cooldown, transitions to half-open
    import time

    time.sleep(0.12)
    assert breaker.state == "half-open"
    assert breaker.can_attempt() is True

    # Success in half-open resets to closed
    breaker.record_success()
    assert breaker.state == "closed"
    assert breaker.failures == 0


def test_circuit_breaker_half_open_failure_reopens():
    breaker = CircuitBreaker("test-breaker", failure_threshold=1, cooldown_seconds=0.05)
    breaker.record_failure()
    assert breaker.state == "open"

    import time

    time.sleep(0.06)
    assert breaker.state == "half-open"

    breaker.record_failure()
    assert breaker.state == "open"


@pytest.mark.asyncio
async def test_gateway_primary_success():
    records = []

    async def mock_recorder(data):
        records.append(data)

    primary = FakeLLM(name="gemini", model="gemini-3.8-flash", responses=["Hello Kubernetes"])
    fallback = FakeLLM(name="groq", model="openai/gpt-oss-20b", responses=["Fallback answer"])
    gateway = LLMGateway(primary=primary, fallback=fallback, recorder=mock_recorder)

    res = await gateway.generate([{"role": "user", "content": "hi"}], request_id="req-1")
    assert res.content == "Hello Kubernetes"
    assert res.provider == "gemini"
    assert res.fallback_used is False
    assert primary.call_count == 1
    assert fallback.call_count == 0

    assert len(records) == 1
    assert records[0]["status"] == "ok"
    assert records[0]["provider"] == "gemini"
    assert records[0]["fallback_used"] is False


@pytest.mark.asyncio
async def test_gateway_fallback_when_primary_fails():
    records = []

    async def mock_recorder(data):
        records.append(data)

    primary = FakeLLM(
        name="gemini",
        model="gemini-3.8-flash",
        errors=[ProviderError("gemini", 503, "Overloaded", retryable=True)],
    )
    fallback = FakeLLM(
        name="groq",
        model="openai/gpt-oss-20b",
        responses=["Greetings from Groq!"],
    )
    gateway = LLMGateway(primary=primary, fallback=fallback, recorder=mock_recorder)

    res = await gateway.generate([{"role": "user", "content": "hi"}], request_id="req-2")
    assert res.content == "Greetings from Groq!"
    assert res.provider == "groq"
    assert res.fallback_used is True
    assert primary.call_count == 1
    assert fallback.call_count == 1

    # Should have recorded failure for primary and success for fallback
    assert len(records) == 2
    assert records[0]["status"] == "error"
    assert records[0]["provider"] == "gemini"
    assert records[1]["status"] == "ok"
    assert records[1]["provider"] == "groq"
    assert records[1]["fallback_used"] is True


@pytest.mark.asyncio
async def test_gateway_streaming_success():
    records = []

    async def mock_recorder(data):
        records.append(data)

    primary = FakeLLM(
        name="gemini",
        model="gemini-3.8-flash",
        responses=["Pod is running in cluster"],
    )
    fallback = FakeLLM(name="groq", model="openai/gpt-oss-20b")
    gateway = LLMGateway(primary=primary, fallback=fallback, recorder=mock_recorder)

    chunks = []
    messages = [{"role": "user", "content": "status"}]
    async for chunk in gateway.stream(messages, request_id="req-stream"):
        chunks.append(chunk)

    # Yields words + terminal chunk
    deltas = [c.delta for c in chunks if not c.done]
    assert "".join(deltas) == "Pod is running in cluster"
    terminal = chunks[-1]
    assert terminal.done is True
    assert terminal.provider == "gemini"
    assert terminal.tokens_in > 0
    assert terminal.tokens_out > 0

    assert len(records) == 1
    assert records[0]["status"] == "ok"


@pytest.mark.asyncio
async def test_gateway_streaming_fallback_when_primary_fails_immediately():
    primary = FakeLLM(
        name="gemini",
        model="gemini-3.8-flash",
        errors=[ProviderError("gemini", 500, "Internal Server Error")],
    )
    fallback = FakeLLM(
        name="groq",
        model="openai/gpt-oss-20b",
        responses=["Fallback stream content"],
    )
    gateway = LLMGateway(primary=primary, fallback=fallback)

    chunks = []
    messages = [{"role": "user", "content": "ping"}]
    async for chunk in gateway.stream(messages, request_id="req-f-stream"):
        chunks.append(chunk)

    deltas = [c.delta for c in chunks if not c.done]
    assert "".join(deltas) == "Fallback stream content"
    assert chunks[-1].provider == "groq"
    assert chunks[-1].fallback_used is True


@pytest.mark.asyncio
async def test_gateway_all_providers_fail_raises():
    primary = FakeLLM(name="gemini", errors=[ProviderError("gemini", 500, "Down")])
    fallback = FakeLLM(name="groq", errors=[ProviderError("groq", 503, "Unavailable")])
    gateway = LLMGateway(primary=primary, fallback=fallback)

    with pytest.raises(AllProvidersFailedError):
        await gateway.generate([{"role": "user", "content": "fail"}], request_id="req-both-fail")


def test_openai_compat_provider_missing_key():
    provider = OpenAICompatProvider("gemini", "https://example.com", "", "model-x")
    with pytest.raises(ProviderError) as exc_info:
        import asyncio

        asyncio.run(provider.generate([{"role": "user", "content": "hi"}]))
    assert "not configured" in str(exc_info.value)
