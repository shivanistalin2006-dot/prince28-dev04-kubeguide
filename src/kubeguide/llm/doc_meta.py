"""Strict Pydantic schema for structured Kubernetes document metadata extraction."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

ShortTag = Annotated[str, StringConstraints(min_length=1, max_length=40, strip_whitespace=True)]

DocKind = Literal[
    "concept",
    "task",
    "reference",
    "tutorial",
    "release_note",
    "guide",
    "other",
]

DocSection = Literal[
    "concepts",
    "tasks",
    "reference",
    "tutorials",
    "releases",
    "other",
]


def _normalize_tags(values: list[str]) -> list[str]:
    """Lowercase, strip, drop empties, and deduplicate while preserving order."""
    seen: set[str] = set()
    out: list[str] = []
    for item in values:
        cleaned = " ".join(item.strip().lower().split())
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            out.append(cleaned)
    return out


class DocMeta(BaseModel):
    """Validated metadata extracted from a KubeGuide Kubernetes documentation file."""

    model_config = ConfigDict(extra="forbid")

    # 5 common assignment fields
    doc_kind: DocKind = Field(..., description="Document category in the Kubernetes corpus.")
    year: int | None = Field(
        default=None,
        ge=2014,
        le=2027,
        description="Four-digit year explicitly mentioned in the document, or null if absent.",
    )
    language: Annotated[
        str,
        StringConstraints(min_length=2, max_length=10, strip_whitespace=True, to_lower=True),
    ] = Field(..., description="ISO 639-1 language code of the document, e.g. 'en'.")
    summary: Annotated[
        str,
        StringConstraints(min_length=10, max_length=320, strip_whitespace=True),
    ] = Field(..., description="Concise 1-2 sentence summary (10-320 characters).")
    topics: list[ShortTag] = Field(
        default_factory=list,
        max_length=8,
        description="Up to 8 short lowercase topic tags covered by the document.",
    )

    # KubeGuide-specific document-level filter fields
    section: DocSection = Field(
        ...,
        description=(
            "Top-level Kubernetes docs section: "
            "concepts, tasks, reference, tutorials, releases, or other."
        ),
    )
    k8s_versions: list[ShortTag] = Field(
        default_factory=list,
        max_length=6,
        description="Up to 6 Kubernetes versions mentioned (e.g. '1.25', '1.30'), or [].",
    )
    object_kinds: list[ShortTag] = Field(
        default_factory=list,
        max_length=8,
        description="Up to 8 Kubernetes API object kinds (e.g. 'pod', 'deployment'), or [].",
    )
    error_codes: list[ShortTag] = Field(
        default_factory=list,
        max_length=6,
        description=(
            "Up to 6 pod/container error states mentioned (e.g. 'crashloopbackoff'), or []."
        ),
    )

    @field_validator("topics", "k8s_versions", "object_kinds", "error_codes", mode="after")
    @classmethod
    def normalize_and_dedup_lists(cls, v: list[str]) -> list[str]:
        return _normalize_tags(v)
