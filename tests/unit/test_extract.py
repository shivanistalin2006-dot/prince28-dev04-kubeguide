"""Unit tests for the metadata extraction engine, JSON parsing, repair loop, and Stretch 3."""

import json
from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from kubeguide.llm.doc_meta import DocMeta
from kubeguide.llm.extract import RESERVED, explain, extract, parse_json, save
from kubeguide.llm.gateway import FakeLLM, LLMGateway


def _valid_payload(**overrides) -> str:
    data = {
        "doc_kind": "task",
        "year": 2025,
        "language": "en",
        "summary": "Explains how to debug a CrashLoopBackOff pod using kubectl logs and events.",
        "topics": ["pods", "debugging"],
        "section": "tasks",
        "k8s_versions": ["1.30"],
        "object_kinds": ["pod"],
        "error_codes": ["crashloopbackoff"],
    }
    data.update(overrides)
    return json.dumps(data)


def test_parse_json_valid_fenced_and_surrounded():
    raw = '{"a": 1, "b": "ok"}'
    assert parse_json(raw) == {"a": 1, "b": "ok"}

    fenced = '```json\n{"a": 2}\n```'
    assert parse_json(fenced) == {"a": 2}

    surrounded = 'Here is the JSON:\n{"a": 3, "nested": {"x": 1}}\nHope that helps!'
    assert parse_json(surrounded) == {"a": 3, "nested": {"x": 1}}


def test_parse_json_rejects_missing_malformed_and_non_object():
    with pytest.raises(ValueError, match="No JSON object"):
        parse_json("No JSON here at all.")

    with pytest.raises(ValueError, match="JSON object"):
        parse_json("[1, 2, 3]")

    with pytest.raises(ValueError, match="Malformed JSON"):
        parse_json('{"a": 1, "b": }')


@pytest.mark.asyncio
async def test_extract_success_and_accounting():
    gw = LLMGateway(
        primary=FakeLLM(
            name="gemini",
            model="gemini-3.8-flash",
            responses=[_valid_payload()],
            tokens_in=100,
            tokens_out=50,
        ),
        fallback=FakeLLM(name="groq"),
        usd_inr=95.0,
    )
    doc_text = "Published in 2025. Debugging CrashLoopBackOff on Pod in Kubernetes 1.30."
    res = await extract(gw, "Extract metadata", 1, doc_text, DocMeta)

    assert res.record is not None
    assert isinstance(res.record, DocMeta)
    assert res.record.doc_kind == "task"
    assert res.record.year == 2025
    assert res.attempts == 1
    assert res.errors == []
    assert res.tokens_in == 100
    assert res.tokens_out == 50
    assert res.cost_inr > 0


@pytest.mark.asyncio
async def test_extract_retry_and_repair():
    bad_reply = _valid_payload(doc_kind="not_a_kind")
    good_reply = _valid_payload(doc_kind="concept", section="concepts", year=None)

    primary = FakeLLM(
        name="gemini",
        model="gemini-3.8-flash",
        responses=[bad_reply, good_reply],
        tokens_in=80,
        tokens_out=40,
    )
    gw = LLMGateway(primary=primary, fallback=FakeLLM(name="groq"))

    res = await extract(gw, "Extract metadata", 1, "Kubernetes Pod overview.", DocMeta)
    assert res.record is not None
    assert res.record.doc_kind == "concept"
    assert res.attempts == 2
    assert len(res.errors) == 1
    assert "doc_kind" in res.errors[0]
    assert res.tokens_in == 160
    assert res.tokens_out == 80
    # Second attempt includes validation feedback
    assert "failed validation" in primary.calls[1]["messages"][-1]["content"]


@pytest.mark.asyncio
async def test_extract_exhausted_attempts_returns_none():
    bad = "not json"
    primary = FakeLLM(
        name="gemini",
        model="gemini-3.8-flash",
        responses=[bad, bad, bad],
        tokens_in=50,
        tokens_out=10,
    )
    gw = LLMGateway(primary=primary, fallback=FakeLLM(name="groq"))

    res = await extract(gw, "Extract", 1, "Some Kubernetes text.", DocMeta, max_attempts=3)
    assert res.record is None
    assert res.attempts == 3
    assert len(res.errors) == 3
    assert res.tokens_in == 150
    assert res.tokens_out == 30


@pytest.mark.asyncio
async def test_extract_rejects_hallucinated_year_and_repairs():
    """Stretch 3: reject non-null year absent from document text, accept when present."""
    hallucinated = _valid_payload(year=2024)
    repaired = _valid_payload(year=None)
    primary = FakeLLM(
        name="gemini",
        model="gemini-3.8-flash",
        responses=[hallucinated, repaired],
    )
    gw = LLMGateway(primary=primary, fallback=FakeLLM(name="groq"))

    res = await extract(
        gw, "Extract", 1, "Kubernetes Pod lifecycle documentation without any year.", DocMeta
    )
    assert res.record is not None
    assert res.record.year is None
    assert res.attempts == 2
    assert "year 2024 is not in the document" in res.errors[0]


@pytest.mark.asyncio
async def test_extract_rejects_reserved_field_collision():
    class BadSchema(BaseModel):
        parser: str

    gw = LLMGateway(primary=FakeLLM(), fallback=FakeLLM())
    with pytest.raises(ValueError, match="RESERVED"):
        await extract(gw, "Extract", 1, "Text", BadSchema)
    assert "parser" in RESERVED


@pytest.mark.asyncio
async def test_save_preserves_parser_metadata_and_handles_failure():
    class FakeSession:
        def __init__(self) -> None:
            self.committed = False

        async def commit(self) -> None:
            self.committed = True

    doc = SimpleNamespace(
        metadata_={"parser": "markdown", "pages": 4, "tables": 1},
    )
    session = FakeSession()

    valid_meta = DocMeta.model_validate_json(_valid_payload(year=None))
    from kubeguide.llm.extract import Extraction

    ok_result = Extraction(record=valid_meta, attempts=1, errors=[], model="gemini-3.8-flash")
    await save(session, doc, ok_result, "extract_v1")  # type: ignore[arg-type]

    assert session.committed is True
    assert doc.metadata_["parser"] == "markdown"
    assert doc.metadata_["pages"] == 4
    assert doc.metadata_["tables"] == 1
    assert doc.metadata_["doc_kind"] == "task"
    assert doc.metadata_["extract"]["prompt"] == "extract_v1"
    assert "error" not in doc.metadata_["extract"]

    # Failure save should NOT overwrite or write extracted fields
    doc2 = SimpleNamespace(metadata_={"parser": "html", "pages": 2})
    fail_result = Extraction(record=None, attempts=3, errors=["bad json"], model="gemini-3.8-flash")
    await save(session, doc2, fail_result, "extract_v1")  # type: ignore[arg-type]
    assert doc2.metadata_["parser"] == "html"
    assert "doc_kind" not in doc2.metadata_
    assert doc2.metadata_["extract"]["error"] == "bad json"


def test_explain_formats_validation_error():
    try:
        DocMeta.model_validate({"doc_kind": "nope"})
    except Exception as exc:
        msg = explain(exc)
        assert "doc_kind" in msg
