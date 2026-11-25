# Shortcuts for Mac/Linux. On Windows, run the same tasks with: uv run poe <task>
.PHONY: dev test test-integration cov lint format up down logs reset stats manifest parse parse-retry compare-parsers ask ask-live llm-ping usage

dev:
	uv run poe dev

test:
	uv run poe test

test-integration:
	uv run poe test-integration

cov:
	uv run poe cov

lint:
	uv run poe lint

format:
	uv run ruff format .

stats:
	uv run python scripts/db_stats.py

manifest:
	uv run python scripts/manifest_summary.py

parse:
	uv run python scripts/parse_corpus.py

parse-retry:
	uv run python scripts/parse_corpus.py --retry-failed

compare-parsers:
	uv run python scripts/compare_parsers.py

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f api

reset:
	docker compose down -v

ask:
	uv run python scripts/ask.py

llm-ping:
	uv run python scripts/llm_ping.py

ask-live:
	uv run python scripts/ask.py --url https://kubeguide.onrender.com

usage:
	curl -s https://kubeguide.onrender.com/v1/usage
