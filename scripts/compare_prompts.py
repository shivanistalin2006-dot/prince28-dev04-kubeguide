"""Evaluate and compare all classify_v*.md prompt versions against eval/prompt_testset.jsonl."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

from kubeguide.config import get_settings
from kubeguide.llm.classify import LABELS, accuracy, classify, find_leaks
from kubeguide.llm.gateway import build_gateway
from kubeguide.llm.prompts import load, versions

CACHE_DIR = Path("eval/cache")


def _cache_key(prompt_text: str, question: str) -> str:
    payload = f"{prompt_text}\n---\n{question}".encode()
    return hashlib.sha256(payload).hexdigest()


def _load_cache(key: str) -> dict[str, Any] | None:
    path = CACHE_DIR / f"{key}.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "predicted" in data and "reply" in data:
            return data
    except (OSError, json.JSONDecodeError):
        return None
    return None


def _save_cache(key: str, data: dict[str, Any]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{key}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_testset(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def build_confusion_matrix(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    """Build confusion counts: true_label -> {predicted_label: count}."""
    cols = [*LABELS, "invalid"]
    matrix: dict[str, dict[str, int]] = {true_lbl: {c: 0 for c in cols} for true_lbl in LABELS}
    for row in rows:
        t = row["expected"]
        p = row["predicted"] if row["predicted"] in cols else "invalid"
        if t in matrix:
            matrix[t][p] += 1
    return matrix


async def run_comparison(rpm: float = 12.0, testset_path: Path | None = None) -> int:
    settings = get_settings()
    prompts_dir = settings.prompts_dir
    testset_file = testset_path or Path("eval/prompt_testset.jsonl")

    testset = _load_testset(testset_file)
    questions = [row["question"] for row in testset]
    vers = versions(prompts_dir, "classify")
    if not vers:
        print(f"No classify_v*.md prompts found in {prompts_dir}", file=sys.stderr)
        return 1

    # 1. Check for leakage first
    loaded_prompts: list[tuple[int, str]] = []
    for ver in vers:
        _, prompt_text = load(prompts_dir, "classify", ver)
        leaks = find_leaks(prompt_text, questions)
        if leaks:
            print(f"LEAK detected in classify_v{ver}: {leaks}", file=sys.stderr)
            return 1
        loaded_prompts.append((ver, prompt_text))

    gateway = build_gateway(settings)
    delay = 60.0 / rpm if rpm > 0 else 0.0
    last_call_at = 0.0

    all_results: dict[int, list[dict[str, Any]]] = {}

    for ver, prompt_text in loaded_prompts:
        ver_rows: list[dict[str, Any]] = []
        cache_hits = 0
        live_calls = 0

        for idx, item in enumerate(testset, start=1):
            question = item["question"]
            expected = item["label"]
            key = _cache_key(prompt_text, question)
            cached = _load_cache(key)

            if cached is not None:
                cache_hits += 1
                ver_rows.append({"line": idx, "question": question, **cached})
                continue

            # Respect RPM before live call
            now = time.monotonic()
            wait = delay - (now - last_call_at)
            if last_call_at > 0 and wait > 0:
                await asyncio.sleep(wait)

            predicted, res = await classify(gateway, prompt_text, ver, question)
            last_call_at = time.monotonic()
            live_calls += 1

            record = {
                "expected": expected,
                "predicted": predicted,
                "reply": res.content,
                "tokens_in": res.tokens_in,
                "tokens_out": res.tokens_out,
                "cost_inr": res.cost_inr,
                "provider": res.provider,
                "model": res.model,
            }
            _save_cache(key, record)
            ver_rows.append({"line": idx, "question": question, **record})

        print(
            f"classify_v{ver}: {len(ver_rows)} questions (live={live_calls}, cached={cache_hits})",
            flush=True,
        )
        all_results[ver] = ver_rows

    # 2. Summary table
    print("\n## Prompt Comparison Table\n")
    print("| Prompt | Correct | Total | Accuracy | Input tokens | Output tokens | Cost |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    for ver in vers:
        rows = all_results[ver]
        total = len(rows)
        correct = sum(1 for r in rows if r["expected"] == r["predicted"])
        acc_pct = accuracy(rows) * 100.0
        tok_in = sum(r["tokens_in"] for r in rows)
        tok_out = sum(r["tokens_out"] for r in rows)
        cost = sum(r["cost_inr"] for r in rows)
        print(
            f"| classify_v{ver} | {correct} | {total} | {acc_pct:.1f}% | "
            f"{tok_in} | {tok_out} | Rs {cost:.4f} |"
        )

    # 3. Confusion matrices (Stretch 4)
    print("\n## Confusion Tables\n")
    for ver in vers:
        print(f"### classify_v{ver}\n")
        print(
            "| True label | Predicted docs | Predicted personal | Predicted off_topic | Invalid |"
        )
        print("|---|---:|---:|---:|---:|")
        matrix = build_confusion_matrix(all_results[ver])
        for true_lbl in LABELS:
            c = matrix[true_lbl]
            print(
                f"| {true_lbl} | {c['docs']} | {c['personal']} | "
                f"{c['off_topic']} | {c['invalid']} |"
            )
        print()

    # 4. Misclassified questions
    print("## Misclassified Questions\n")
    for ver in vers:
        misses = [r for r in all_results[ver] if r["expected"] != r["predicted"]]
        print(f"### classify_v{ver} ({len(misses)} missed)")
        if not misses:
            print("- None (100% accuracy)")
        else:
            for m in misses:
                reply_clean = " ".join(str(m["reply"]).split())[:120]
                print(
                    f"- Line {m['line']}: expected `{m['expected']}`, "
                    f"got `{m['predicted']}` | reply: `{reply_clean}` | q: {m['question']}"
                )
        print()

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare classify_v*.md prompt versions.")
    parser.add_argument("--rpm", type=float, default=12.0, help="Max live requests per minute")
    parser.add_argument(
        "--testset",
        type=Path,
        default=Path("eval/prompt_testset.jsonl"),
        help="Path to JSONL evaluation test set",
    )
    args = parser.parse_args()
    return asyncio.run(run_comparison(rpm=args.rpm, testset_path=args.testset))


if __name__ == "__main__":
    sys.exit(main())
