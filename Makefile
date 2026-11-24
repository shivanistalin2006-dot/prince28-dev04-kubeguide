# Shortcuts for Mac/Linux. On Windows, run the same tasks with: uv run poe <task>
.PHONY: dev test test-integration cov lint format up down logs reset stats manifest

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

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f api

reset:
	docker compose down -v
