"""CLI client to trigger a background ingestion job and watch progress until completion."""

from __future__ import annotations

import argparse
import sys
import time

import httpx

from kubeguide.config import get_settings


def main() -> int:
    parser = argparse.ArgumentParser(description="Start and monitor a KubeGuide ingest job.")
    parser.add_argument("--limit", type=int, default=20, help="Max documents to queue (1..2000)")
    parser.add_argument("--source", default="", help="Optional source name filter")
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Re-queue items currently on the dead-letter list",
    )
    parser.add_argument("--url", default="http://localhost:8000", help="Base API URL")
    parser.add_argument("--token", default="", help="X-Admin-Token (defaults to ADMIN_TOKEN)")
    parser.add_argument(
        "--poll",
        type=float,
        default=2.0,
        help="Seconds between progress polls",
    )
    args = parser.parse_args()

    token = args.token or get_settings().admin_token
    base_url = args.url.rstrip("/")
    headers = {"X-Admin-Token": token} if token else {}
    payload = {
        "limit": args.limit,
        "source": args.source,
        "retry_failed": args.retry_failed,
    }

    start = time.monotonic()
    with httpx.Client(timeout=30.0, headers={"Connection": "close"}) as client:
        resp = client.post(f"{base_url}/v1/ingest", json=payload, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            print(f"HTTP 200: {data.get('detail', 'Nothing to do.')}", flush=True)
            return 0
        if resp.status_code != 202:
            print(f"HTTP {resp.status_code}: {resp.text}", file=sys.stderr, flush=True)
            return 1

        accepted = resp.json()
        job_id = accepted["job_id"]
        queued = accepted["queued"]
        print(f"HTTP 202: job {job_id}, {queued} queued", flush=True)

        while True:
            try:
                prog = client.get(f"{base_url}/v1/ingest/{job_id}")
            except httpx.TransportError as exc:
                print(f"poll error ({exc}); retrying...", file=sys.stderr, flush=True)
                time.sleep(args.poll)
                continue
            if prog.status_code != 200:
                print(f"HTTP {prog.status_code}: {prog.text}", file=sys.stderr, flush=True)
                return 1
            data = prog.json()
            elapsed = int(time.monotonic() - start)
            finished = data.get("finished", False)
            label = "finished" if finished else "working "
            print(
                f"{label}  queued={data['queued']} running={data['running']} "
                f"done={data['done']} skipped={data['skipped']} "
                f"failed={data['failed']} pages={data['pages']} {elapsed}s",
                flush=True,
            )
            if finished:
                for item in data.get("items", []):
                    if item.get("status") == "failed":
                        print(
                            f"FAILED {item.get('path') or item.get('url')} "
                            f"({item.get('attempts')} try) {item.get('error')}",
                            flush=True,
                        )
                return 0
            time.sleep(args.poll)


if __name__ == "__main__":
    raise SystemExit(main())
