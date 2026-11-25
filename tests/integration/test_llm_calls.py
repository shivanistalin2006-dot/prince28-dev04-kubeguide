"""Integration test for recording LLM calls and usage repository aggregation."""

import pytest

from kubeguide.db.llm_calls import LlmUsageRepository, record_llm_call


@pytest.mark.asyncio
async def test_record_and_aggregate_llm_calls(db_session):
    # Ensure llm_calls table exists
    await record_llm_call(
        db_session,
        {
            "request_id": "test-int-req-1",
            "provider": "gemini",
            "model": "gemini-3.8-flash",
            "purpose": "chat",
            "prompt_version": "v1",
            "status": "ok",
            "tokens_in": 120,
            "tokens_out": 250,
            "latency_ms": 350,
            "cost_inr": 0.085,
            "fallback_used": False,
        },
    )

    await record_llm_call(
        db_session,
        {
            "request_id": "test-int-req-2",
            "provider": "groq",
            "model": "openai/gpt-oss-20b",
            "purpose": "chat",
            "prompt_version": "v1",
            "status": "ok",
            "tokens_in": 150,
            "tokens_out": 300,
            "latency_ms": 180,
            "cost_inr": 0.012,
            "fallback_used": True,
        },
    )

    repo = LlmUsageRepository(db_session)
    days = await repo.by_day(days=1)
    assert len(days) >= 1
    today_stats = days[0]
    assert today_stats["calls"] >= 2
    assert today_stats["tokens_in"] >= 270
    assert today_stats["tokens_out"] >= 550
    assert today_stats["cost_inr"] > 0
