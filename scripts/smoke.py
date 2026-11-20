"""Smoke test script for verifying deployed service health, version and database."""

import argparse
import json
import sys
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
    parser.add_argument("url", help="Base URL of the deployed application")
    parser.add_argument("--expect-version", help="Expected git commit SHA in /health")
    parser.add_argument("--timeout", type=int, default=300, help="Maximum seconds to wait for version rollout")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    print(f"Testing service at: {base_url}")


if __name__ == "__main__":
    main()
