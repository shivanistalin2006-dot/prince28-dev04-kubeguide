"""Database operations and usage accounting for LLM calls."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from kubeguide.db.models import LlmCall


async def record_llm_call(session: AsyncSession, data: dict[str, Any]) -> None:
    """Record a single LLM invocation attempt to the database."""
    call = LlmCall(
        request_id=data.get("request_id", ""),
        provider=data.get("provider", "unknown"),
        model=data.get("model", "unknown"),
        purpose=data.get("purpose", "chat"),
        prompt_version=data.get("prompt_version", "v1"),
        status=data.get("status", "error"),
        error=data.get("error"),
        tokens_in=data.get("tokens_in", 0),
        tokens_out=data.get("tokens_out", 0),
        latency_ms=data.get("latency_ms", 0),
        cost_inr=data.get("cost_inr", 0.0),
        fallback_used=data.get("fallback_used", False),
    )
    session.add(call)
    await session.commit()


class LlmUsageRepository:
    """Aggregates LLM usage and billing metrics."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def by_day(self, days: int = 7) -> list[dict[str, Any]]:
        """Return daily billing and performance breakdown for the past N days."""
        cutoff = datetime.now(UTC) - timedelta(days=days)

        stmt = (
            select(
                cast(LlmCall.created_at, Date).label("day"),
                func.count(LlmCall.id).label("calls"),
                func.count().filter(LlmCall.status == "ok").label("successful_calls"),
                func.count().filter(LlmCall.fallback_used.is_(True)).label("fallback_calls"),
                func.coalesce(func.sum(LlmCall.tokens_in), 0).label("tokens_in"),
                func.coalesce(func.sum(LlmCall.tokens_out), 0).label("tokens_out"),
                func.coalesce(func.sum(LlmCall.cost_inr), 0.0).label("cost_inr"),
                func.coalesce(func.percentile_disc(0.50).within_group(LlmCall.latency_ms), 0).label(
                    "p50_latency_ms"
                ),
                func.coalesce(func.percentile_disc(0.95).within_group(LlmCall.latency_ms), 0).label(
                    "p95_latency_ms"
                ),
            )
            .where(LlmCall.created_at >= cutoff)
            .group_by(cast(LlmCall.created_at, Date))
            .order_by(cast(LlmCall.created_at, Date).desc())
        )

        try:
            result = await self.session.execute(stmt)
            rows = result.all()
            return [
                {
                    "day": str(row.day),
                    "calls": int(row.calls),
                    "successful_calls": int(row.successful_calls),
                    "fallback_calls": int(row.fallback_calls),
                    "tokens_in": int(row.tokens_in),
                    "tokens_out": int(row.tokens_out),
                    "cost_inr": float(round(row.cost_inr, 4)),
                    "p50_latency_ms": int(row.p50_latency_ms or 0),
                    "p95_latency_ms": int(row.p95_latency_ms or 0),
                }
                for row in rows
            ]
        except Exception:
            # Fallback for SQL engines (like SQLite in unit tests) that lack percentile_disc
            simple_stmt = (
                select(
                    cast(LlmCall.created_at, Date).label("day"),
                    func.count(LlmCall.id).label("calls"),
                    func.coalesce(func.sum(LlmCall.tokens_in), 0).label("tokens_in"),
                    func.coalesce(func.sum(LlmCall.tokens_out), 0).label("tokens_out"),
                    func.coalesce(func.sum(LlmCall.cost_inr), 0.0).label("cost_inr"),
                )
                .where(LlmCall.created_at >= cutoff)
                .group_by(cast(LlmCall.created_at, Date))
                .order_by(cast(LlmCall.created_at, Date).desc())
            )
            simple_res = await self.session.execute(simple_stmt)
            return [
                {
                    "day": str(row.day),
                    "calls": int(row.calls),
                    "tokens_in": int(row.tokens_in),
                    "tokens_out": int(row.tokens_out),
                    "cost_inr": float(round(row.cost_inr, 4)),
                }
                for row in simple_res.all()
            ]
