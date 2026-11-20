"""Smoke test script for verifying deployed service health, version and database."""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request


def check_endpoint(url: str, description: str, timeout: int = 15) -> tuple[int, dict]:
    """Perform HTTP GET request and return HTTP status and parsed JSON response."""
    req = urllib.request.Request(url, headers={"User-Agent": "SmokeTest/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode("utf-8")
            status = resp.status
            try:
                body = json.loads(data)
            except json.JSONDecodeError:
                body = {"raw": data}
            return status, body
    except urllib.error.HTTPError as e:
        data = e.read().decode("utf-8")
        try:
            body = json.loads(data)
        except json.JSONDecodeError:
            body = {"raw": data}
        return e.code, body
    except Exception as e:
        print(f"FAIL {description} -> connection error: {e}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test a deployed KubeGuide service.")
    parser.add_argument(
        "url",
        help="Base URL of the deployed application (e.g. https://kubeguide.onrender.com)",
    )
    parser.add_argument("--expect-version", help="Expected git commit SHA in /health")
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Maximum seconds to wait for version rollout",
    )
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    health_url = f"{base_url}/health"
    ready_url = f"{base_url}/ready"
    docs_url = f"{base_url}/v1/documents?limit=1"

    # 1. Health & version check
    if args.expect_version:
        start = time.time()
        matched = False
        while time.time() - start < args.timeout:
            status, body = check_endpoint(health_url, "/health")
            ver = body.get("version", "")
            if status == 200 and ver == args.expect_version:
                print(f"ok /health -> 200, version {ver}")
                matched = True
                break
            print(f"waiting: {status} {ver}")
            time.sleep(5)
        if not matched:
            print(f"FAIL: timed out waiting for version {args.expect_version}")
            sys.exit(1)
    else:
        status, body = check_endpoint(health_url, "/health")
        if status != 200:
            print(f"FAIL /health -> {status} {body}")
            sys.exit(1)
        ver = body.get("version", "unknown")
        print(f"ok /health -> 200, version {ver}")

    # 2. Readiness check
    status, body = check_endpoint(ready_url, "/ready")
    if status != 200 or not body.get("checks", {}).get("database", False):
        print(f"FAIL /ready -> {status} {body}")
        sys.exit(1)
    print(f"ok /ready -> 200 {body}")

    # 3. Documents query check
    status, body = check_endpoint(docs_url, "/v1/documents?limit=1")
    if status != 200:
        print(f"FAIL /v1/documents?limit=1 -> {status} {body}")
        sys.exit(1)
    print("ok /v1/documents?limit=1 -> 200")

    print("Smoke test passed")


if __name__ == "__main__":
    main()
