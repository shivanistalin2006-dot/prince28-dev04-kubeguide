"""Chat and LLM usage accounting endpoints."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from typing import Annotated, Any, Self

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, model_validator

from kubeguide.api.deps import get_gateway, get_usage_repo
from kubeguide.db.llm_calls import LlmUsageRepository
from kubeguide.llm.gateway import AllProvidersFailedError, LLMGateway

router = APIRouter(prefix="/v1", tags=["chat"])


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message author role: system, user, or assistant")
    content: str = Field(..., description="Message text content")


class ChatRequest(BaseModel):
    message: str | None = Field(
        None, min_length=1, max_length=4000, description="User message or query"
    )
    prompt: str | None = Field(
        None, min_length=1, max_length=4000, description="User prompt or query alias"
    )
    stream: bool = Field(True, description="Whether to stream response chunks via SSE")
    history: list[ChatMessage] = Field(
        default_factory=list, description="Optional multi-turn conversation history"
    )
    purpose: str = Field("chat", description="Purpose tag for audit logging")

    @model_validator(mode="after")
    def populate_message_and_prompt(self) -> Self:
        text = self.message or self.prompt
        if not text:
            raise ValueError("Either 'message' or 'prompt' must be provided.")
        self.message = text
        self.prompt = text
        return self


class ChatResponse(BaseModel):
    response: str
    answer: str | None = None
    tokens_in: int
    tokens_out: int
    tokens: dict[str, int] | None = None
    latency_ms: int
    provider: str
    model: str
    fallback_used: bool
    is_fallback: bool | None = None


class DailyUsage(BaseModel):
    day: str
    calls: int
    tokens_in: int
    tokens_out: int
    cost_inr: float
    successful_calls: int | None = None
    fallback_calls: int | None = None
    p50_latency_ms: int | None = None
    p95_latency_ms: int | None = None


@router.post("/chat", summary="Chat with KubeGuide assistant")
async def chat_endpoint(
    req: ChatRequest,
    request: Request,
    gateway: Annotated[LLMGateway, Depends(get_gateway)],
) -> Any:
    """Stream or return an LLM answer using resilient multi-provider gateway."""
    request_id = getattr(request.state, "request_id", None) or uuid.uuid4().hex
    system_prompt = getattr(
        request.app.state,
        "system_prompt",
        "You are KubeGuide, an assistant for Kubernetes SREs.",
    )

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    for msg in req.history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": req.prompt})

    if req.stream:
        stream_gen = gateway.stream(
            messages,
            request_id=request_id,
            purpose=req.purpose,
        )

        try:
            first_chunk = await anext(stream_gen)
        except AllProvidersFailedError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"All LLM providers are currently unavailable: {exc}",
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"LLM streaming service error: {exc}",
            ) from exc

        async def sse_event_stream() -> AsyncIterator[str]:
            if first_chunk.delta:
                chunk_data = {"delta": first_chunk.delta, "chunk": first_chunk.delta, "done": False}
                yield f"data: {json.dumps(chunk_data)}\n\n"
            if first_chunk.done:
                payload = {
                    "done": True,
                    "tokens_in": first_chunk.tokens_in,
                    "tokens_out": first_chunk.tokens_out,
                    "tokens": {"in": first_chunk.tokens_in, "out": first_chunk.tokens_out},
                    "latency_ms": first_chunk.latency_ms,
                    "provider": first_chunk.provider,
                    "model": first_chunk.model,
                    "fallback_used": first_chunk.fallback_used,
                    "is_fallback": first_chunk.fallback_used,
                }
                yield f"data: {json.dumps(payload)}\n\n"
                return

            async for chunk in stream_gen:
                if chunk.delta:
                    chunk_data = {"delta": chunk.delta, "chunk": chunk.delta, "done": False}
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                if chunk.done:
                    payload = {
                        "done": True,
                        "tokens_in": chunk.tokens_in,
                        "tokens_out": chunk.tokens_out,
                        "tokens": {"in": chunk.tokens_in, "out": chunk.tokens_out},
                        "latency_ms": chunk.latency_ms,
                        "provider": chunk.provider,
                        "model": chunk.model,
                        "fallback_used": chunk.fallback_used,
                        "is_fallback": chunk.fallback_used,
                    }
                    yield f"data: {json.dumps(payload)}\n\n"

        return StreamingResponse(sse_event_stream(), media_type="text/event-stream")

    try:
        res = await gateway.generate(
            messages,
            request_id=request_id,
            purpose=req.purpose,
        )
        return ChatResponse(
            response=res.content,
            answer=res.content,
            tokens_in=res.tokens_in,
            tokens_out=res.tokens_out,
            tokens={"in": res.tokens_in, "out": res.tokens_out},
            latency_ms=res.latency_ms,
            provider=res.provider,
            model=res.model,
            fallback_used=res.fallback_used,
            is_fallback=res.fallback_used,
        )
    except AllProvidersFailedError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"All LLM providers are currently unavailable: {exc}",
        ) from exc


@router.get("/usage", response_model=list[DailyUsage], summary="Daily LLM usage and bill")
async def get_usage_metrics(
    usage_repo: Annotated[LlmUsageRepository, Depends(get_usage_repo)],
    days: int = Query(7, ge=1, le=90, description="Number of past days to query"),
) -> list[dict[str, Any]]:
    """Return aggregated LLM calls, token counts, and cost in INR per day."""
    return await usage_repo.by_day(days=days)


@router.get("/llm/status", summary="Provider circuit breaker status")
def get_llm_status(
    gateway: Annotated[LLMGateway, Depends(get_gateway)],
) -> dict[str, Any]:
    """Inspect live circuit breaker status for primary and fallback providers."""
    return {
        "primary": {
            "provider": gateway.primary.name,
            "model": gateway.primary.default_model,
            "circuit_breaker": gateway.primary_breaker.state,
            "failures": gateway.primary_breaker.failures,
        },
        "fallback": {
            "provider": gateway.fallback.name,
            "model": gateway.fallback.default_model,
            "circuit_breaker": gateway.fallback_breaker.state,
            "failures": gateway.fallback_breaker.failures,
        },
    }
