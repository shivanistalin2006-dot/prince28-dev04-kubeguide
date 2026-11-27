"""Unit tests for the DocMeta Pydantic contract and extraction prompt alignment."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from kubeguide.llm.doc_meta import DocMeta


def test_doc_meta_valid_and_normalizes_lists():
    meta = DocMeta(
        doc_kind="task",
        year=2025,
        language=" EN ",
        summary="Explains how to configure liveness and readiness probes on Kubernetes pods.",
        topics=[" Probes ", "pods", "PROBES", "Health Checks"],
        section="tasks",
        k8s_versions=["1.30", "1.30", " 1.31 "],
        object_kinds=["Pod", "pod", "Deployment"],
        error_codes=["CrashLoopBackOff", "crashloopbackoff"],
    )
    assert meta.language == "en"
    assert meta.topics == ["probes", "pods", "health checks"]
    assert meta.k8s_versions == ["1.30", "1.31"]
    assert meta.object_kinds == ["pod", "deployment"]
    assert meta.error_codes == ["crashloopbackoff"]


def test_doc_meta_rejects_extra_fields():
    with pytest.raises(ValidationError):
        DocMeta(
            doc_kind="concept",
            year=None,
            language="en",
            summary="Explains Kubernetes Pod scheduling across cluster nodes.",
            section="concepts",
            unexpected_extra="nope",
        )


def test_doc_meta_rejects_invalid_kind_and_section():
    with pytest.raises(ValidationError):
        DocMeta(
            doc_kind="invalid_kind",
            year=None,
            language="en",
            summary="Explains Kubernetes Pod scheduling across cluster nodes.",
            section="concepts",
        )
    with pytest.raises(ValidationError):
        DocMeta(
            doc_kind="concept",
            year=None,
            language="en",
            summary="Explains Kubernetes Pod scheduling across cluster nodes.",
            section="unknown_section",
        )


def test_doc_meta_year_bounds():
    with pytest.raises(ValidationError):
        DocMeta(
            doc_kind="concept",
            year=1999,
            language="en",
            summary="Explains Kubernetes Pod scheduling across cluster nodes.",
            section="concepts",
        )
    with pytest.raises(ValidationError):
        DocMeta(
            doc_kind="concept",
            year=2035,
            language="en",
            summary="Explains Kubernetes Pod scheduling across cluster nodes.",
            section="concepts",
        )


def test_doc_meta_rejects_bad_lengths_and_list_limits():
    with pytest.raises(ValidationError):
        DocMeta(
            doc_kind="concept",
            year=None,
            language="en",
            summary="Too short",
            section="concepts",
        )
    with pytest.raises(ValidationError):
        DocMeta(
            doc_kind="concept",
            year=None,
            language="en",
            summary="Explains Kubernetes Pod scheduling across cluster nodes.",
            section="concepts",
            topics=[f"topic-{i}" for i in range(9)],
        )
    with pytest.raises(ValidationError):
        DocMeta(
            doc_kind="concept",
            year=None,
            language="en",
            summary="Explains Kubernetes Pod scheduling across cluster nodes.",
            section="concepts",
            topics=[""],
        )


def test_extract_prompt_describes_every_doc_meta_field():
    prompt_path = Path("prompts/extract_v1.md")
    assert prompt_path.exists()
    prompt_text = prompt_path.read_text(encoding="utf-8")
    for field_name in DocMeta.model_fields:
        assert f'"{field_name}"' in prompt_text, f"Field '{field_name}' missing from extract_v1.md"
