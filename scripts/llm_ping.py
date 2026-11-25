"""Direct ping test to Gemini and Groq without going through the gateway.

Usage:
    uv run python scripts/llm_ping.py
"""

import sys
import time

import httpx

from kubeguide.config import get_settings


def ping_provider(name: str, base_url: str, key: str, model: str, timeout: float = 30.0) -> None:
    if not key:
        print(f"{name:<8} NO KEY: {name.upper()}_API_KEY is not set in .env")
        return

    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {key}"}
    body = {
        "model": model,
        "messages": [{"role": "user", "content": "ping"}],
    }

    t0 = time.perf_counter()
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, headers=headers, json=body)
            elapsed_ms = int((time.perf_counter() - t0) * 1000)

            if resp.status_code != 200:
                print(f"{name:<8} FAILED HTTP {resp.status_code}: {resp.text[:200]}")
                return

            data = resp.json()
            usage = data.get("usage", {})
            choice = data.get("choices", [{}])[0]
            answer = (choice.get("message", {}).get("content") or "").strip().replace("\n", " ")
            tokens_in = usage.get("prompt_tokens", 0)
            tokens_out = usage.get("completion_tokens", 0)
            print(
                f"{name:<8} OK {model} said '{answer[:30]}' in {elapsed_ms} ms, "
                f"tokens in={tokens_in} out={tokens_out}"
            )

    except Exception as exc:  # noqa: BLE001
        print(f"{name:<8} FAILED: {type(exc).__name__}: {exc}")


def main() -> int:
    settings = get_settings()
    providers = [
        (
            "gemini",
            settings.llm_primary_base_url,
            settings.gemini_api_key,
            settings.llm_primary_model,
        ),
        (
            "groq",
            settings.llm_fallback_base_url,
            settings.groq_api_key,
            settings.llm_fallback_model,
        ),
    ]

    for name, base_url, key, model in providers:
        ping_provider(name, base_url, key, model, settings.llm_timeout_seconds)

    return 0


if __name__ == "__main__":
    sys.exit(main())
