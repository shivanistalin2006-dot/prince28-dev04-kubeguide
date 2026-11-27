"""Structured document metadata extraction engine with validation-retry and DB persistence."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kubeguide.db.models import Document, Page
from kubeguide.llm.gateway import AllProvidersFailedError, LLMGateway

logger = logging.getLogger("kubeguide.llm.extract")

RESERVED: frozenset[str] = frozenset(
    {
        "parser",
        "pages",
        "tables",
        "chars",
        "source",
        "path",
        "extract",
        "id",
        "title",
        "doc_type",
        "source_url",
        "licence",
        "published_on",
        "sha256",
    }
)


@dataclass
class Extraction:
    """Outcome of extracting structured metadata for a single document."""

    record: BaseModel | None
    attempts: int
    errors: list[str] = field(default_factory=list)
    model: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    cost_inr: float = 0.0


def parse_json(reply: str) -> dict[str, Any]:
    """Extract and parse a JSON object from raw, fenced, or prose-wrapped model output."""
    if not reply or not reply.strip():
        raise ValueError("No JSON object found in empty reply")

    text = reply.strip()
    # Strip markdown code fences if present
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, flags=re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()

    decoder = json.JSONDecoder()
    # Try direct decode first if it starts with '{' or '['
    start_obj = text.find("{")
    start_arr = text.find("[")

    if start_obj == -1 and start_arr == -1:
        raise ValueError("No JSON object found in model reply")

    # If '[' appears before '{' (and no '{' inside), check if top-level is non-object
    if start_arr != -1 and (start_obj == -1 or start_arr < start_obj):
        try:
            parsed, _ = decoder.raw_decode(text[start_arr:])
            if not isinstance(parsed, dict):
                raise ValueError(f"Expected a JSON object, got {type(parsed).__name__}")
        except json.JSONDecodeError:
            pass

    if start_obj == -1:
        raise ValueError("No JSON object found in model reply")

    try:
        parsed, _ = decoder.raw_decode(text[start_obj:])
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed JSON: {exc.msg}") from exc

    if not isinstance(parsed, dict):
        raise ValueError(f"Expected a JSON object, got {type(parsed).__name__}")
    return parsed


def explain(error: Exception) -> str:
    """Return a concise, model-readable summary of a JSON or Pydantic validation error."""
    if isinstance(error, ValidationError):
        parts: list[str] = []
        for err in error.errors():
            loc = ".".join(str(x) for x in err.get("loc", ())) or "root"
            parts.append(f"{loc}: {err.get('msg', 'invalid value')}")
        return "; ".join(parts)
    return str(error)


async def extract(
    gateway: LLMGateway,
    prompt: str,
    version: int | str,
    text: str,
    schema: type[BaseModel],
    *,
    max_attempts: int = 3,
    use_schema: bool = False,
) -> Extraction:
    """Extract and validate `schema` from `text`, retrying with validation feedback."""
    collisions = set(schema.model_fields.keys()) & RESERVED
    if collisions:
        raise ValueError(f"Schema fields collide with RESERVED parser keys: {sorted(collisions)}")

    prompt_version = f"extract_v{version}" if isinstance(version, int) else str(version)
    schema_json = json.dumps(schema.model_json_schema(), indent=2)
    system_prompt = f"{prompt}\n\nJSON Schema:\n{schema_json}"

    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"<document>\n{text}\n</document>"},
    ]

    response_format: dict[str, Any] | None = None
    if use_schema:
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": schema.__name__,
                "schema": schema.model_json_schema(),
                "strict": True,
            },
        }

    errors: list[str] = []
    tokens_in = 0
    tokens_out = 0
    total_cost = 0.0
    last_model = ""

    for attempt in range(1, max_attempts + 1):
        res = await gateway.generate(
            messages,
            purpose="extract",
            prompt_version=prompt_version,
            temperature=0.0,
            response_format=response_format,
        )
        tokens_in += res.tokens_in
        tokens_out += res.tokens_out
        total_cost = round(total_cost + res.cost_inr, 6)
        last_model = res.model

        try:
            data = parse_json(res.content)
            record = schema.model_validate(data)
            year_val = getattr(record, "year", None)
            if year_val is not None and str(year_val) not in text:
                raise ValueError(f"year {year_val} is not in the document")
            return Extraction(
                record=record,
                attempts=attempt,
                errors=errors,
                model=last_model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cost_inr=total_cost,
            )
        except Exception as exc:
            err_msg = explain(exc)
            errors.append(err_msg)
            if attempt < max_attempts:
                messages.append({"role": "assistant", "content": res.content})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Your JSON output failed validation: {err_msg}\n"
                            "Fix the error and output ONLY a single valid JSON object."
                        ),
                    }
                )

    return Extraction(
        record=None,
        attempts=max_attempts,
        errors=errors,
        model=last_model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_inr=total_cost,
    )


async def pending(
    session: AsyncSession,
    prompt_version: str,
    *,
    limit: int | None = None,
    retry_failed: bool = False,
) -> list[Document]:
    """Return documents not yet successfully extracted by `prompt_version`."""
    stmt = select(Document).where(Document.doc_type != "record").order_by(Document.external_id)
    docs = list((await session.scalars(stmt)).all())
    out: list[Document] = []
    for doc in docs:
        meta = doc.metadata_ or {}
        ext = meta.get("extract")
        if isinstance(ext, dict) and ext.get("prompt") == prompt_version:
            has_error = "error" in ext
            if not has_error:
                continue
            if has_error and not retry_failed:
                continue
        out.append(doc)
        if limit is not None and len(out) >= limit:
            break
    return out


async def document_text(
    session: AsyncSession,
    document_id: int,
    *,
    max_pages: int = 3,
    max_chars: int = 6000,
) -> str:
    """Read and concatenate the first `max_pages` pages of a document up to `max_chars`."""
    stmt = (
        select(Page.text)
        .where(Page.document_id == document_id)
        .order_by(Page.page_no)
        .limit(max_pages)
    )
    chunks = list((await session.scalars(stmt)).all())
    joined = "\n\n".join(c for c in chunks if c)
    return joined[:max_chars]


async def save(
    session: AsyncSession,
    doc: Document,
    result: Extraction,
    prompt_version: str,
) -> None:
    """Merge validated fields into `doc.metadata_` while preserving parser metadata."""
    existing = dict(doc.metadata_ or {})
    extract_info: dict[str, Any] = {
        "prompt": prompt_version,
        "model": result.model,
        "attempts": result.attempts,
        "errors": result.errors,
    }
    if result.record is not None:
        extracted_fields = result.record.model_dump(mode="json")
        # Double-check against RESERVED before merging
        safe_fields = {k: v for k, v in extracted_fields.items() if k not in RESERVED}
        existing.update(safe_fields)
    else:
        extract_info["error"] = result.errors[-1] if result.errors else "unknown extraction error"

    existing["extract"] = extract_info
    doc.metadata_ = existing
    await session.commit()


async def run(
    session_factory: async_sessionmaker[AsyncSession],
    gateway: LLMGateway,
    prompt: str,
    version: int | str,
    schema: type[BaseModel],
    *,
    limit: int | None = None,
    retry_failed: bool = False,
    rpm: float = 12.0,
    use_schema: bool = False,
    retry_wait_seconds: float = 60.0,
) -> dict[str, Any]:
    """Run batch extraction over pending documents, committing one document at a time."""
    prompt_version = f"extract_v{version}" if isinstance(version, int) else str(version)

    async with session_factory() as session:
        docs = await pending(session, prompt_version, limit=limit, retry_failed=retry_failed)

    total_pending = len(docs)
    success = 0
    failures = 0
    repairs = 0
    tokens_in = 0
    tokens_out = 0
    total_cost = 0.0
    stopped_early = False

    delay = 60.0 / rpm if rpm > 0 else 0.0
    last_call_at = 0.0

    for idx, doc in enumerate(docs, start=1):
        async with session_factory() as session:
            db_doc = await session.get(Document, doc.id)
            if db_doc is None:
                continue
            text = await document_text(session, db_doc.id)

            if last_call_at > 0 and delay > 0:
                wait = delay - (time.monotonic() - last_call_at)
                if wait > 0:
                    await asyncio.sleep(wait)

            result: Extraction | None = None
            for provider_try in range(2):
                try:
                    last_call_at = time.monotonic()
                    result = await extract(
                        gateway,
                        prompt,
                        version,
                        text,
                        schema,
                        use_schema=use_schema,
                    )
                    break
                except AllProvidersFailedError as exc:
                    if provider_try == 0:
                        logger.warning(
                            "All providers failed on %s; sleeping %.1fs before one retry: %s",
                            db_doc.external_id,
                            retry_wait_seconds,
                            exc,
                        )
                        await asyncio.sleep(retry_wait_seconds)
                    else:
                        logger.error(
                            "Providers failed twice on %s; stopping safely: %s",
                            db_doc.external_id,
                            exc,
                        )
                        stopped_early = True

            if stopped_early or result is None:
                break

            tokens_in += result.tokens_in
            tokens_out += result.tokens_out
            total_cost = round(total_cost + result.cost_inr, 6)

            if result.record is not None:
                success += 1
                if result.attempts > 1:
                    repairs += 1
            else:
                failures += 1

            await save(session, db_doc, result, prompt_version)

        if idx % 10 == 0 or idx == total_pending:
            print(
                f"Progress {idx}/{total_pending}: ok={success}, repaired={repairs}, "
                f"failed={failures}, cost=Rs {total_cost:.4f}",
                flush=True,
            )

    return {
        "prompt_version": prompt_version,
        "pending": total_pending,
        "processed": success + failures,
        "success": success,
        "repairs": repairs,
        "failures": failures,
        "remaining": total_pending - (success + failures),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_inr": total_cost,
        "stopped_early": stopped_early,
    }
