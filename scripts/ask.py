"""Interactive CLI client to test streaming or JSON responses from /v1/chat.

Usage:
    uv run python scripts/ask.py "How do I troubleshoot a CrashLoopBackOff pod?"
    uv run python scripts/ask.py --json "What is a DaemonSet?"
    uv run python scripts/ask.py --base-url https://kubeguide.onrender.com "What is a Service?"
"""

from __future__ import annotations

import argparse
import json
import sys
import time

import httpx


def ask(prompt: str, base_url: str = "http://localhost:8000", stream: bool = True) -> int:
    url = f"{base_url.rstrip('/')}/v1/chat"
    payload = {"prompt": prompt, "stream": stream}

    print(f"\nAsking '{prompt}' at {url} (stream={stream})...\n" + "-" * 60)
    t0 = time.perf_counter()

    try:
        if not stream:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(url, json=payload)
                elapsed_ms = int((time.perf_counter() - t0) * 1000)
                if resp.status_code != 200:
                    print(f"Error {resp.status_code}: {resp.text}", file=sys.stderr)
                    return 1
                data = resp.json()
                print(data["response"])
                print("-" * 60)
                print(
                    f"Provider: {data['provider']} ({data['model']}) | "
                    f"Fallback: {data['fallback_used']} | "
                    f"Tokens: in={data['tokens_in']} out={data['tokens_out']} | "
                    f"Latency: {data['latency_ms']} ms (client {elapsed_ms} ms)"
                )
                return 0

        # Streaming mode via SSE
        first_word_ms = None
        with (
            httpx.Client(timeout=60.0) as client,
            client.stream("POST", url, json=payload) as resp,
        ):
            if resp.status_code != 200:
                body = resp.read().decode("utf-8", errors="replace")
                print(f"Error {resp.status_code}: {body}", file=sys.stderr)
                return 1

            terminal_chunk = None
            for line in resp.iter_lines():
                line = line.strip()
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[len("data:") :].strip()
                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                if chunk.get("delta"):
                    if first_word_ms is None:
                        first_word_ms = int((time.perf_counter() - t0) * 1000)
                    sys.stdout.write(chunk["delta"])
                    sys.stdout.flush()

                if chunk.get("done"):
                    terminal_chunk = chunk
                    break

            print()
            print("-" * 60)
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            if terminal_chunk:
                p_name = terminal_chunk.get("provider")
                m_name = terminal_chunk.get("model")
                fb = terminal_chunk.get("fallback_used")
                tin = terminal_chunk.get("tokens_in")
                tout = terminal_chunk.get("tokens_out")
                print(
                    f"Provider: {p_name} ({m_name}) | Fallback: {fb} | "
                    f"Tokens: in={tin} out={tout} | "
                    f"First chunk: {first_word_ms or 0} ms | Total: {elapsed_ms} ms"
                )
            else:
                print(f"Completed in {elapsed_ms} ms (no final accounting chunk)")
            return 0

    except Exception as exc:  # noqa: BLE001
        print(f"Connection failed: {exc}", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Ask questions to KubeGuide /v1/chat")
    default_q = "How do I troubleshoot a CrashLoopBackOff pod?"
    parser.add_argument("prompt", nargs="?", default=default_q)
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base API URL")
    parser.add_argument("--json", action="store_true", help="Request non-streaming JSON response")
    args = parser.parse_args()

    return ask(args.prompt, base_url=args.base_url, stream=not args.json)


if __name__ == "__main__":
    sys.exit(main())
