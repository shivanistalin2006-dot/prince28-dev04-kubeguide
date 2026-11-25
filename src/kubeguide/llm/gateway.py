"""LLM Gateway: multi-provider client with circuit breaking, fallback, streaming, and accounting."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger("kubeguide.llm")

# Pricing per million tokens (input, output) in USD
PRICES_USD: dict[str, tuple[float, float]] = {
    "gemini-3.8-flash": (0.75, 3.75),
    "gemini-3.5-flash-lite": (0.30, 2.50),
    "openai/gpt-oss-20b": (0.075, 0.30),
    "openai/gpt-oss-120b": (0.15, 0.60),
}


def cost_inr(model: str, tokens_in: int, tokens_out: int, usd_inr: float = 86.0) -> float:
    """Calculate exact rupee cost for a model invocation given token counts."""
    rate_in, rate_out = PRICES_USD.get(model, (0.75, 3.75))
    cost_usd = (tokens_in * rate_in + tokens_out * rate_out) / 1_000_000.0
    return round(cost_usd * usd_inr, 6)


class LLMError(Exception):
    """Base exception for all LLM gateway errors."""


class ProviderError(LLMError):
    """An error raised when communicating with a specific provider."""

    def __init__(
        self,
        provider: str,
        status_code: int | None,
        message: str,
        retryable: bool = False,
    ) -> None:
        super().__init__(f"[{provider}] {status_code or 'ERR'}: {message}")
        self.provider = provider
        self.status_code = status_code
        self.message = message
        self.retryable = retryable


class CircuitBreakerOpenError(LLMError):
    """Raised when an attempt is rejected because the circuit breaker is open."""

    def __init__(self, provider: str) -> None:
        super().__init__(f"Circuit breaker for provider '{provider}' is open")
        self.provider = provider


class AllProvidersFailedError(LLMError):
    """Raised when all configured providers (primary & fallback) failed or are tripped."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__(f"All providers failed: {'; '.join(errors)}")
        self.errors = errors


@dataclass
class ProviderResult:
    """Non-streaming generation result."""

    content: str
    tokens_in: int
    tokens_out: int
    latency_ms: int
    model: str
    provider: str
    fallback_used: bool = False


@dataclass
class StreamChunk:
    """A streaming token delta or terminal accounting chunk."""

    delta: str
    done: bool = False
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    model: str = ""
    provider: str = ""
    fallback_used: bool = False


class CircuitBreaker:
    """Simple three-state circuit breaker: closed, open, half-open."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        cooldown_seconds: float = 30.0,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.failures = 0
        self.opened_at: float | None = None
        self._state = "closed"

    @property
    def state(self) -> str:
        if (
            self._state == "open"
            and self.opened_at is not None
            and time.monotonic() - self.opened_at >= self.cooldown_seconds
        ):
            self._state = "half-open"
        return self._state

    def can_attempt(self) -> bool:
        return self.state in ("closed", "half-open")

    def record_success(self) -> None:
        self.failures = 0
        self.opened_at = None
        self._state = "closed"

    def record_failure(self) -> None:
        if self.state == "half-open":
            self._state = "open"
            self.opened_at = time.monotonic()
        else:
            self.failures += 1
            if self.failures >= self.failure_threshold:
                self._state = "open"
                self.opened_at = time.monotonic()


class OpenAICompatProvider:
    """Calls an OpenAI-compatible REST endpoint (/chat/completions)."""

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str,
        default_model: str,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.default_model = default_model
        self.timeout_seconds = timeout_seconds

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _classify_error(self, status: int, text: str) -> ProviderError:
        retryable = status in (429, 500, 502, 503, 504)
        return ProviderError(
            self.name,
            status,
            f"HTTP {status}: {text[:200]}",
            retryable=retryable,
        )

    async def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
    ) -> ProviderResult:
        if not self.api_key:
            raise ProviderError(
                self.name, 401, f"{self.name} API key is not configured", retryable=False
            )

        active_model = model or self.default_model
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": active_model,
            "messages": messages,
            "temperature": 0.2,
        }

        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(url, headers=self._headers(), json=payload)
                elapsed_ms = int((time.perf_counter() - t0) * 1000)

                if resp.status_code != 200:
                    raise self._classify_error(resp.status_code, resp.text)

                data = resp.json()
                choice = data.get("choices", [{}])[0]
                content = choice.get("message", {}).get("content", "")
                usage = data.get("usage", {})
                tokens_in = usage.get("prompt_tokens") or max(
                    1, sum(len(m.get("content", "")) for m in messages) // 4
                )
                tokens_out = usage.get("completion_tokens") or max(1, len(content) // 4)

                return ProviderResult(
                    content=content,
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    latency_ms=elapsed_ms,
                    model=active_model,
                    provider=self.name,
                )
        except httpx.RequestError as exc:
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            raise ProviderError(self.name, None, f"Network error: {exc}", retryable=True) from exc

    async def stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
    ) -> AsyncIterator[StreamChunk]:
        if not self.api_key:
            raise ProviderError(
                self.name, 401, f"{self.name} API key is not configured", retryable=False
            )

        active_model = model or self.default_model
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": active_model,
            "messages": messages,
            "stream": True,
            "stream_options": {"include_usage": True},
            "temperature": 0.2,
        }

        t0 = time.perf_counter()
        try:
            client = httpx.AsyncClient(timeout=self.timeout_seconds)
            try:
                async with client.stream(
                    "POST", url, headers=self._headers(), json=payload
                ) as resp:
                    if resp.status_code != 200:
                        body = await resp.aread()
                        raise self._classify_error(
                            resp.status_code, body.decode("utf-8", errors="replace")
                        )

                    total_text: list[str] = []
                    tokens_in = 0
                    tokens_out = 0

                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if not line or not line.startswith("data:"):
                            continue
                        data_str = line[len("data:") :].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            parsed = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue

                        choices = parsed.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {}).get("content", "")
                            if delta:
                                total_text.append(delta)
                                yield StreamChunk(
                                    delta=delta,
                                    model=active_model,
                                    provider=self.name,
                                )

                        usage = parsed.get("usage")
                        if usage:
                            tokens_in = usage.get("prompt_tokens", tokens_in)
                            tokens_out = usage.get("completion_tokens", tokens_out)

                    elapsed_ms = int((time.perf_counter() - t0) * 1000)
                    full_content = "".join(total_text)
                    if tokens_in == 0:
                        tokens_in = max(1, sum(len(m.get("content", "")) for m in messages) // 4)
                    if tokens_out == 0:
                        tokens_out = max(1, len(full_content) // 4)

                    yield StreamChunk(
                        delta="",
                        done=True,
                        tokens_in=tokens_in,
                        tokens_out=tokens_out,
                        latency_ms=elapsed_ms,
                        model=active_model,
                        provider=self.name,
                    )
            finally:
                await client.aclose()
        except httpx.RequestError as exc:
            raise ProviderError(self.name, None, f"Network error: {exc}", retryable=True) from exc


class FakeLLM:
    """Programmable fake provider for fast deterministic tests."""

    def __init__(
        self,
        name: str = "fake",
        model: str = "fake-model",
        responses: list[str] | None = None,
        errors: list[Exception] | None = None,
        latency_ms: int = 15,
        tokens_in: int = 10,
        tokens_out: int = 20,
    ) -> None:
        self.name = name
        self.default_model = model
        self.responses = list(responses or ["Hello from FakeLLM!"])
        self.errors = list(errors or [])
        self.latency_ms = latency_ms
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out
        self.call_count = 0
        self.calls: list[dict[str, Any]] = []

    async def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
    ) -> ProviderResult:
        self.call_count += 1
        active_model = model or self.default_model
        self.calls.append({"messages": messages, "model": active_model})

        if self.errors:
            err = self.errors.pop(0)
            raise err

        resp_text = self.responses.pop(0) if self.responses else "Default fake answer"
        return ProviderResult(
            content=resp_text,
            tokens_in=self.tokens_in,
            tokens_out=self.tokens_out,
            latency_ms=self.latency_ms,
            model=active_model,
            provider=self.name,
        )

    async def stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
    ) -> AsyncIterator[StreamChunk]:
        self.call_count += 1
        active_model = model or self.default_model
        self.calls.append({"messages": messages, "model": active_model})

        if self.errors:
            err = self.errors.pop(0)
            raise err

        resp_text = self.responses.pop(0) if self.responses else "Default fake answer"
        # Yield words in chunks
        words = resp_text.split(" ")
        for i, word in enumerate(words):
            sep = " " if i < len(words) - 1 else ""
            yield StreamChunk(
                delta=word + sep,
                model=active_model,
                provider=self.name,
            )

        yield StreamChunk(
            delta="",
            done=True,
            tokens_in=self.tokens_in,
            tokens_out=self.tokens_out,
            latency_ms=self.latency_ms,
            model=active_model,
            provider=self.name,
        )


class LLMGateway:
    """Orchestrates primary and fallback providers, circuit breakers, and auditing."""

    def __init__(
        self,
        primary: OpenAICompatProvider | FakeLLM,
        fallback: OpenAICompatProvider | FakeLLM,
        primary_breaker: CircuitBreaker | None = None,
        fallback_breaker: CircuitBreaker | None = None,
        recorder: Callable[[dict[str, Any]], Any] | None = None,
        usd_inr: float = 86.0,
    ) -> None:
        self.primary = primary
        self.fallback = fallback
        self.primary_breaker = primary_breaker or CircuitBreaker(primary.name)
        self.fallback_breaker = fallback_breaker or CircuitBreaker(fallback.name)
        self.recorder = recorder
        self.usd_inr = usd_inr

    async def _record(self, data: dict[str, Any]) -> None:
        if self.recorder:
            try:
                res = self.recorder(data)
                if hasattr(res, "__await__"):
                    await res
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to record LLM call to DB: %s", exc)

    async def generate(
        self,
        messages: list[dict[str, str]],
        request_id: str,
        purpose: str = "chat",
        prompt_version: str = "v1",
    ) -> ProviderResult:
        errors: list[str] = []

        # 1. Try Primary
        if self.primary_breaker.can_attempt():
            t0 = time.perf_counter()
            try:
                res = await self.primary.generate(messages)
                self.primary_breaker.record_success()
                await self._record(
                    {
                        "request_id": request_id,
                        "provider": res.provider,
                        "model": res.model,
                        "purpose": purpose,
                        "prompt_version": prompt_version,
                        "status": "ok",
                        "error": None,
                        "tokens_in": res.tokens_in,
                        "tokens_out": res.tokens_out,
                        "latency_ms": res.latency_ms,
                        "cost_inr": cost_inr(
                            res.model, res.tokens_in, res.tokens_out, self.usd_inr
                        ),
                        "fallback_used": False,
                    }
                )
                res.fallback_used = False
                return res
            except Exception as exc:
                elapsed_ms = int((time.perf_counter() - t0) * 1000)
                self.primary_breaker.record_failure()
                err_msg = str(exc)
                errors.append(f"Primary ({self.primary.name}): {err_msg}")
                logger.warning("Primary LLM %s failed: %s", self.primary.name, err_msg)
                await self._record(
                    {
                        "request_id": request_id,
                        "provider": self.primary.name,
                        "model": getattr(self.primary, "default_model", "unknown"),
                        "purpose": purpose,
                        "prompt_version": prompt_version,
                        "status": "error",
                        "error": err_msg[:500],
                        "tokens_in": 0,
                        "tokens_out": 0,
                        "latency_ms": elapsed_ms,
                        "cost_inr": 0.0,
                        "fallback_used": False,
                    }
                )
        else:
            errors.append(f"Primary ({self.primary.name}) breaker is OPEN")

        # 2. Try Fallback
        if self.fallback_breaker.can_attempt():
            t0 = time.perf_counter()
            try:
                res = await self.fallback.generate(messages)
                self.fallback_breaker.record_success()
                await self._record(
                    {
                        "request_id": request_id,
                        "provider": res.provider,
                        "model": res.model,
                        "purpose": purpose,
                        "prompt_version": prompt_version,
                        "status": "ok",
                        "error": None,
                        "tokens_in": res.tokens_in,
                        "tokens_out": res.tokens_out,
                        "latency_ms": res.latency_ms,
                        "cost_inr": cost_inr(
                            res.model, res.tokens_in, res.tokens_out, self.usd_inr
                        ),
                        "fallback_used": True,
                    }
                )
                res.fallback_used = True
                return res
            except Exception as exc:
                elapsed_ms = int((time.perf_counter() - t0) * 1000)
                self.fallback_breaker.record_failure()
                err_msg = str(exc)
                errors.append(f"Fallback ({self.fallback.name}): {err_msg}")
                logger.error("Fallback LLM %s failed: %s", self.fallback.name, err_msg)
                await self._record(
                    {
                        "request_id": request_id,
                        "provider": self.fallback.name,
                        "model": getattr(self.fallback, "default_model", "unknown"),
                        "purpose": purpose,
                        "prompt_version": prompt_version,
                        "status": "error",
                        "error": err_msg[:500],
                        "tokens_in": 0,
                        "tokens_out": 0,
                        "latency_ms": elapsed_ms,
                        "cost_inr": 0.0,
                        "fallback_used": True,
                    }
                )
        else:
            errors.append(f"Fallback ({self.fallback.name}) breaker is OPEN")

        raise AllProvidersFailedError(errors)

    async def stream(
        self,
        messages: list[dict[str, str]],
        request_id: str,
        purpose: str = "chat",
        prompt_version: str = "v1",
    ) -> AsyncIterator[StreamChunk]:
        """Stream response chunks from primary, falling back seamlessly if primary fails."""
        errors: list[str] = []

        # 1. Try Primary
        if self.primary_breaker.can_attempt():
            t0 = time.perf_counter()
            first_yielded = False
            try:
                async for chunk in self.primary.stream(messages):
                    first_yielded = True
                    if chunk.done:
                        self.primary_breaker.record_success()
                        await self._record(
                            {
                                "request_id": request_id,
                                "provider": chunk.provider,
                                "model": chunk.model,
                                "purpose": purpose,
                                "prompt_version": prompt_version,
                                "status": "ok",
                                "error": None,
                                "tokens_in": chunk.tokens_in,
                                "tokens_out": chunk.tokens_out,
                                "latency_ms": chunk.latency_ms,
                                "cost_inr": cost_inr(
                                    chunk.model, chunk.tokens_in, chunk.tokens_out, self.usd_inr
                                ),
                                "fallback_used": False,
                            }
                        )
                        chunk.fallback_used = False
                        yield chunk
                        return
                    chunk.fallback_used = False
                    yield chunk
            except Exception as exc:
                elapsed_ms = int((time.perf_counter() - t0) * 1000)
                self.primary_breaker.record_failure()
                err_msg = str(exc)
                errors.append(f"Primary ({self.primary.name}): {err_msg}")
                logger.warning("Primary LLM %s stream failed: %s", self.primary.name, err_msg)
                await self._record(
                    {
                        "request_id": request_id,
                        "provider": self.primary.name,
                        "model": getattr(self.primary, "default_model", "unknown"),
                        "purpose": purpose,
                        "prompt_version": prompt_version,
                        "status": "error",
                        "error": err_msg[:500],
                        "tokens_in": 0,
                        "tokens_out": 0,
                        "latency_ms": elapsed_ms,
                        "cost_inr": 0.0,
                        "fallback_used": False,
                    }
                )
                if first_yielded:
                    # Chunks were already sent to client; cannot cleanly restart stream
                    raise
        else:
            errors.append(f"Primary ({self.primary.name}) breaker is OPEN")

        # 2. Try Fallback
        if self.fallback_breaker.can_attempt():
            t0 = time.perf_counter()
            try:
                async for chunk in self.fallback.stream(messages):
                    if chunk.done:
                        self.fallback_breaker.record_success()
                        await self._record(
                            {
                                "request_id": request_id,
                                "provider": chunk.provider,
                                "model": chunk.model,
                                "purpose": purpose,
                                "prompt_version": prompt_version,
                                "status": "ok",
                                "error": None,
                                "tokens_in": chunk.tokens_in,
                                "tokens_out": chunk.tokens_out,
                                "latency_ms": chunk.latency_ms,
                                "cost_inr": cost_inr(
                                    chunk.model, chunk.tokens_in, chunk.tokens_out, self.usd_inr
                                ),
                                "fallback_used": True,
                            }
                        )
                        chunk.fallback_used = True
                        yield chunk
                        return
                    chunk.fallback_used = True
                    yield chunk
            except Exception as exc:
                elapsed_ms = int((time.perf_counter() - t0) * 1000)
                self.fallback_breaker.record_failure()
                err_msg = str(exc)
                errors.append(f"Fallback ({self.fallback.name}): {err_msg}")
                logger.error("Fallback LLM %s stream failed: %s", self.fallback.name, err_msg)
                await self._record(
                    {
                        "request_id": request_id,
                        "provider": self.fallback.name,
                        "model": getattr(self.fallback, "default_model", "unknown"),
                        "purpose": purpose,
                        "prompt_version": prompt_version,
                        "status": "error",
                        "error": err_msg[:500],
                        "tokens_in": 0,
                        "tokens_out": 0,
                        "latency_ms": elapsed_ms,
                        "cost_inr": 0.0,
                        "fallback_used": True,
                    }
                )
                raise AllProvidersFailedError(errors) from exc
        else:
            errors.append(f"Fallback ({self.fallback.name}) breaker is OPEN")

        raise AllProvidersFailedError(errors)


def build_gateway(
    settings: Any,
    recorder: Callable[[dict[str, Any]], Any] | None = None,
) -> LLMGateway:
    """Build production gateway using application settings."""
    primary = OpenAICompatProvider(
        name="gemini",
        base_url=settings.llm_primary_base_url,
        api_key=settings.gemini_api_key,
        default_model=settings.llm_primary_model,
        timeout_seconds=settings.llm_timeout_seconds,
    )
    fallback = OpenAICompatProvider(
        name="groq",
        base_url=settings.llm_fallback_base_url,
        api_key=settings.groq_api_key,
        default_model=settings.llm_fallback_model,
        timeout_seconds=settings.llm_timeout_seconds,
    )
    return LLMGateway(
        primary=primary,
        fallback=fallback,
        recorder=recorder,
        usd_inr=settings.usd_inr,
    )
