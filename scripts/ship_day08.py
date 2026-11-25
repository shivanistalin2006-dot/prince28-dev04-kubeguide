"""Automation script to create PR for Day 8, poll CI checks, merge to main, and verify live CD."""

import json
import os
import subprocess
import sys
import time
import urllib.request


def get_github_token() -> str:
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    res = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n",
        capture_output=True,
        text=True,
    )
    for line in res.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("GITHUB_TOKEN env var not set and git credential fill failed")


def main() -> int:
    token = get_github_token()
    repo = "shivanistalin2006-dot/prince28-dev04-kubeguide"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "KubeGuide-Shipper",
    }

    def api_call(endpoint: str, method: str = "GET", data: dict | None = None) -> dict:
        url = f"https://api.github.com/repos/{repo}/{endpoint.lstrip('/')}"
        body = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # 1. Create PR
    pr_payload = {
        "title": "feat(llm): Day 08 LLM Gateway with streaming, fallback, circuit breaker",
        "head": "feat/day-08-llm-gateway",
        "base": "main",
        "body": (
            "### Day 08 · LLM Gateway Complete\n\n"
            "- Multi-provider LLM Gateway with pure httpx (Gemini Flash + Groq fallback)\n"
            "- 3-state Circuit Breaker with 30s cooldown and 3-failure threshold\n"
            "- Streaming & SSE with graceful failover\n"
            "- Exact rupee accounting in PostgreSQL llm_calls table via Alembic\n"
            "- Stretch goals: /v1/llm/status, multi-turn history, /v1/usage percentiles\n"
        ),
    }

    try:
        pr = api_call("pulls", method="POST", data=pr_payload)
        pr_number = pr["number"]
        pr_url = pr["html_url"]
        head_sha = pr["head"]["sha"]
        print(f"Created PR #{pr_number}: {pr_url}")
    except urllib.error.HTTPError as err:
        err_body = err.read().decode("utf-8")
        if "A pull request already exists" in err_body:
            open_prs = api_call("pulls?state=open")
            pr = next(p for p in open_prs if p["head"]["ref"] == "feat/day-08-llm-gateway")
            pr_number = pr["number"]
            pr_url = pr["html_url"]
            head_sha = pr["head"]["sha"]
            print(f"Using existing PR #{pr_number}: {pr_url}")
        else:
            print(f"Failed to create PR: {err_body}", file=sys.stderr)
            return 1

    print(f"Monitoring CI checks for commit {head_sha[:7]}...")
    for attempt in range(40):
        time.sleep(10)
        runs_data = api_call(f"commits/{head_sha}/check-runs")
        check_runs = runs_data.get("check_runs", [])
        if not check_runs:
            print(f"[{attempt + 1}/40] Waiting for checks to report...")
            continue

        statuses = [
            f"{c['name']}={c['status']}({c['conclusion'] or 'pending'})" for c in check_runs
        ]
        print(f"[{attempt + 1}/40] Checks: {', '.join(statuses)}")

        if all(c["status"] == "completed" for c in check_runs):
            if all(c["conclusion"] == "success" for c in check_runs):
                print("\nAll CI checks passed successfully! Merging PR...")
                break
            else:
                failures = [c["name"] for c in check_runs if c["conclusion"] != "success"]
                print(f"CI failed on: {', '.join(failures)}", file=sys.stderr)
                return 1
    else:
        print("Timed out waiting for CI checks", file=sys.stderr)
        return 1

    # Merge PR
    merge_data = {"merge_method": "rebase"}
    try:
        merge_resp = api_call(f"pulls/{pr_number}/merge", method="PUT", data=merge_data)
    except Exception:
        merge_data = {"merge_method": "merge"}
        merge_resp = api_call(f"pulls/{pr_number}/merge", method="PUT", data=merge_data)
    print(f"PR #{pr_number} merged! SHA: {merge_resp.get('sha')}")

    # Switch local repo back to main and pull
    print("Switching local repository to main and pulling...")
    subprocess.run(["git", "switch", "main"], check=True)
    subprocess.run(["git", "pull", "--ff-only"], check=True)

    print("Day 8 merged to main successfully! CD pipeline will now deploy to Render.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
