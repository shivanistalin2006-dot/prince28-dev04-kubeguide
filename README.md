# KubeGuide

A Kubernetes assistant for on-call engineers that explains errors, objects and kubectl output from the official docs for the cluster's version.

**Status:** Day 1 foundation (FastAPI skeleton, quality gates). Live URL from Day 5.

## Who it's for
Site reliability engineer at a Chennai logistics startup who is on call for three Kubernetes clusters.

## The problem
On-call engineers troubleshoot recurring issues such as CrashLoopBackOff and ImagePullBackOff during production incidents. Official documentation is extensive, making it difficult to locate root causes quickly under pressure. In addition, breaking API changes between Kubernetes versions can cause unexpected failures. Effective debugging requires aligning exact cluster versions with relevant documentation and kubectl diagnostic outputs.

## Data sources
kubernetes/website docs (concepts, tasks, reference), release notes and deprecated API migration guide for the last 4 minor versions.
- https://github.com/kubernetes/website
- https://kubernetes.io/docs/reference/using-api/deprecation-guide/
- Terms: Kubernetes docs CC BY 4.0.

## Hardest problem (my interview story)
Version skew and troubleshooting: answers must respect the cluster version and removed APIs, and troubleshooting needs both the user's kubectl output and the right docs, step by step.

## Signature feature
Error decoder: paste 'kubectl describe' output or an event and get a cause tree with doc links.

## Target metric
Right root cause in the top 2 for 80%+ of 30 broken-cluster scenarios.

## Run it locally
```bash
uv sync
cp .env.example .env  # Windows: copy .env.example .env
uv run uvicorn kubeguide.api.main:create_app --factory --reload
```
Then open http://localhost:8000/docs

## Checks
```bash
uv run pytest
uv run ruff check .
```
