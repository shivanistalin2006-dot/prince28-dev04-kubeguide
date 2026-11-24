# Engineering notes: KubeGuide

## D03 · PostgreSQL

### Migrations (upgrade, downgrade, upgrade)
```text
$ uv run alembic downgrade -1
INFO  [alembic.runtime.migration] Context impl AsyncpgImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running downgrade 002_add_gin_index_on_metadata -> 001_create_documents_and_pages, add gin index on metadata

$ uv run alembic current
INFO  [alembic.runtime.migration] Context impl AsyncpgImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
001_create_documents_and_pages

$ uv run alembic upgrade head
INFO  [alembic.runtime.migration] Context impl AsyncpgImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 001_create_documents_and_pages -> 002_add_gin_index_on_metadata, add gin index on metadata

$ uv run alembic history
<base> -> 001_create_documents_and_pages, create documents and pages
001_create_documents_and_pages -> 002_add_gin_index_on_metadata (head), add gin index on metadata
```

### The loader is idempotent
```text
run 1:
records=20 inserted=20 updated=0 unchanged=0

run 2:
records=20 inserted=0 updated=0 unchanged=20

run 3 (after editing one record):
records=20 inserted=0 updated=1 unchanged=19
```

### EXPLAIN for ?page=VALUE
```text
$ uv run python scripts/explain.py page pod-lifecycle
-- 1) What the planner chooses on its own:
Seq Scan on documents  (cost=0.00..1.25 rows=1 width=40) (actual time=0.015..0.021 rows=1 loops=1)
  Filter: (metadata @> '{"page": "pod-lifecycle"}'::jsonb)
  Rows Removed by Filter: 19
Planning Time: 0.082 ms
Execution Time: 0.038 ms

-- 2) Seq scan switched off, to prove the index can be used:
Bitmap Heap Scan on documents  (cost=4.26..8.27 rows=1 width=40) (actual time=0.022..0.024 rows=1 loops=1)
  Recheck Cond: (metadata @> '{"page": "pod-lifecycle"}'::jsonb)
  Heap Blocks: exact=1
  ->  Bitmap Index Scan on ix_documents_metadata_gin  (cost=0.00..4.26 rows=1 width=0) (actual time=0.014..0.014 rows=1 loops=1)
        Index Cond: (metadata @> '{"page": "pod-lifecycle"}'::jsonb)
Planning Time: 0.075 ms
Execution Time: 0.045 ms
```

Why did the planner choose a Seq Scan on my table?
With only 20 records, all database pages fit in a single memory block, making a sequential scan faster than index lookups. The planner avoids the overhead of reading the index structure when scanning the small table directly requires fewer I/O operations.

When would it switch to the GIN index?
It switches to the GIN index when table cardinality scales to thousands of records and high filter selectivity makes index traversal cheaper than full table scans.

## D04 · Docker, Compose and tests

### The image
```text
REPOSITORY   TAG       IMAGE ID       CREATED          SIZE
kubeguide    dev       8d2039cae7b1   12 minutes ago   234MB

uid=999(app) gid=999(app) groups=999(app)
```
- Size: 234 MB (target: under 400 MB)
- First build: 72 s. After changing one line of code: 1.4 s.
- Which step said CACHED, and why?
  The step `uv sync --locked --no-install-project --no-dev` was CACHED because `uv.lock` and `pyproject.toml` remained unchanged, allowing Docker to reuse the pre-built dependency layer.

### The stack
```text
NAME                  IMAGE                    COMMAND                  SERVICE   CREATED          STATUS                    PORTS
kubeguide-api-1       kubeguide:dev            "sh -c 'exec uvicorn…"   api       10 minutes ago   Up 10 minutes (healthy)   0.0.0.0:8000->8000/tcp
kubeguide-db-1        pgvector/pgvector:pg17   "docker-entrypoint.s…"   db        10 minutes ago   Up 10 minutes (healthy)   0.0.0.0:5433->5432/tcp
kubeguide-migrate-1   kubeguide:dev            "sh -c 'alembic upgr…"   migrate   10 minutes ago   Exited (0) 10 minutes ago
kubeguide-redis-1     redis:7-alpine           "docker-entrypoint.s…"   redis     10 minutes ago   Up 10 minutes (healthy)   0.0.0.0:6379->6379/tcp

# docker compose logs migrate (first up):
kubeguide-migrate-1  | records=20 inserted=20 updated=0 unchanged=0
# docker compose logs migrate (after down + up):
kubeguide-migrate-1  | records=20 inserted=0 updated=0 unchanged=20
```

### Breaking the database on purpose
```text
db stopped: /health -> 200 OK {"status":"ok"}
db stopped: /ready -> 503 Service Unavailable {"status":"unavailable","checks":{"database":false}}
db started: /ready -> 200 OK {"status":"ready","checks":{"database":true}}
```
Why should a load balancer stop sending traffic here but not restart the app?
If the database is down or restarting, killing the app container won't fix Postgres and will cause crash loops.
The load balancer should cut ingress traffic while letting the container wait for database recovery.

### Tests and coverage
```text
uv run poe test -> 16 passed in 0.46s
uv run poe test-integration -> 7 passed in 2.15s (7 skipped without live container)
coverage TOTAL, unit only -> TOTAL 297 42 50 8 82%
coverage TOTAL, with integration tests -> TOTAL 297 12 50 2 96%
```
Two files or lines my coverage report says are never run, and whether they matter:
`src/kubeguide/api/deps.py` (lines 35-43) and `src/kubeguide/db/repository.py` (lines 47-62) are skipped during unit tests because FakeRepo is injected; they don't matter for unit isolation as they are tested in integration runs.

## D05 · CI/CD and going live
- Live URL: https://kubeguide.onrender.com
- OpenAPI Docs: https://kubeguide.onrender.com/docs
- Root path `/`: Configured with HTTP redirect to `/docs` for seamless browser exploration.
- CI run for pull request 1: https://github.com/shivanistalin2006-dot/prince28-dev04-kubeguide/actions
- First deploy that ran by itself: https://github.com/shivanistalin2006-dot/prince28-dev04-kubeguide/actions
- Merge clicked at 13:24 → "Smoke test passed" at 13:28 → lead time: 4 min

### Smoke test output from that CD run
```text
ok /health -> 200, version 1ad8337
ok /ready -> 200 {'status': 'ready', 'checks': {'database': True}}
ok /v1/documents?limit=1 -> 200
Smoke test passed
```

### Rollback drill
- Rolled back to sha 1ad8337 : started 13:29, smoke passed 13:32 (3 min)
- Rolled forward to sha d995259 : 3 min
- During the rollback, the database stayed on the newer schema. Why is that safe here?
  All migrations follow backward-compatible expansion rules (adding nullable columns or new tables). Older code versions only interact with the columns they know about, avoiding breaks against the existing schema.

### Where my secrets live
- Neon string: GitHub Secret DATABASE_URL + Render environment. Not in Git, not in the image.
- Render deploy hook: GitHub Secret RENDER_DEPLOY_HOOK only.

### Monitoring
- UptimeRobot checks /health every 5 minutes; alerts go to my email.
- One thing that would make my live app faster on its first request:
  Upgrading from the Render Free tier to an instance with persistent worker memory prevents instance idling and eliminates cold-start spin-up latency.

### Stretch tasks
- Human gate (continuous delivery):
  A manual approval gate before production deployment is valuable during planned change freezes, compliance audits, or multi-service synchronized releases where coordinated operational sign-off is required.
- DORA Lead Time & CI/CD Performance:
  - CD Run 1 lead time: ~4 minutes (PR merge to smoke test green).
  - CD Run 2 lead time: ~3.5 minutes.
  - Slowest step: Render container pulling and booting (takes ~60-90s on free instance).

## D06 · Collecting the corpus
- Start target: Concepts + tasks pages (about 700 pages)
- Collected today: 422 files, 1,505 pages, 9.7 MB (from DATASET.md)
- Doors used: URL list / Git repository

### Licence check
| Source | Licence or terms, in my words | May I show full text in answers? |
|---|---|---|
| k8s-docs (kubernetes/website) | CC BY 4.0 (attribution required, commercial & derivative use permitted) | Yes, with citation and original link |
| kubernetes-io (docs pages) | CC BY 4.0 (attribution required, commercial & derivative use permitted) | Yes, with citation and original link |

### robots.txt
- Site: https://kubernetes.io . Its robots.txt says (2 lines):
  User-agent: *
  Allow: /
- Was anything blocked for my bot? What did I do about it?
  No, 0 files were blocked. The crawler identifies as examate-student-bot/0.1 with repository contact info and respects all robots.txt rules.

### Kill and resume
- Run 1: I pressed Ctrl+C after 3 files
- Run 2: downloaded=7 skipped=3
- Run 3: downloaded=0 skipped=10

### Capacity (from docs/CAPACITY.md)
- Tokens per page, measured: 750
- Full corpus: 1.87 M tokens, 5,391 chunks, embedding about Rs 31, vectors 17 MB
- The number that surprised me most, and why (2 lines):
  The total storage for the full corpus vectors and text is only ~26 MB, proving that an extensive technical corpus easily fits into free-tier serverless PostgreSQL without high infra costs.

### One thing that went wrong today, and how I fixed it
Door 2 initially encountered a non-empty directory error when cloning into data/raw/k8s-docs because the initial 10 URL downloads used the same directory name; separating sources in data/sources.csv to kubernetes-io resolved the conflict cleanly.

## D07 · Parsing my corpus

### Corpus Parsing Summary
- Files in manifest: 422 files (412 Markdown/YAML from `kubernetes/website`, 10 HTML from `kubernetes.io`)
- Files parsed into PostgreSQL: 422 files (100% coverage after failure retry)
- Total pages extracted: 1,710 pages stored in PostgreSQL `pages` table
- Dead-letter failures remaining: 0 unresolved failures in `parse_failures`
- Parser idempotency: Verified by running `python scripts/parse_corpus.py` twice; subsequent run skips already-parsed files and completes in <1s.

### Parser Engine Comparison (10 Complex Files)
We evaluated `trafilatura` against raw DOM text extraction (`lxml`) across 10 intricate Kubernetes documentation pages containing headers, navigations, sidebars, and code blocks:

| File | Trafilatura (chars) | Lxml (chars) | Diff (chars) | Trafilatura (ms) | Lxml (ms) | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `configure-liveness-readiness-startup-probes-e1c0be00.html` | 14,799 | 41,622 | -26,823 | 290.6 | 27.7 | trafilatura preferred: cleanly stripped nav/boilerplates |
| `debug-pods-b62c530a.html` | 6,967 | 31,989 | -25,022 | 164.4 | 25.7 | trafilatura preferred: cleanly stripped nav/boilerplates |
| `debug-service-261a96a8.html` | 20,111 | 46,724 | -26,613 | 221.5 | 24.7 | trafilatura preferred: cleanly stripped nav/boilerplates |
| `deployment-d9a16560.html` | 45,604 | 78,352 | -32,748 | 321.2 | 30.5 | trafilatura preferred: cleanly stripped nav/boilerplates |
| `deprecation-guide-0fc64549.html` | 10,258 | 42,583 | -32,325 | 189.8 | 23.1 | trafilatura preferred: cleanly stripped nav/boilerplates |
| `manage-resources-containers-d3611dbe.html` | 26,334 | 56,539 | -30,205 | 263.6 | 28.6 | trafilatura preferred: cleanly stripped nav/boilerplates |
| `pod-lifecycle-3e34f258.html` | 40,437 | 67,060 | -26,623 | 344.1 | 28.6 | trafilatura preferred: cleanly stripped nav/boilerplates |
| `pull-image-private-registry-2e249b9b.html` | 7,616 | 33,653 | -26,037 | 198.1 | 27.8 | trafilatura preferred: cleanly stripped nav/boilerplates |
| `rbac-6be4067d.html` | 42,345 | 69,171 | -26,826 | 490.0 | 40.0 | trafilatura preferred: cleanly stripped nav/boilerplates |
| `statefulset-f82fae6f.html` | 22,127 | 51,086 | -28,959 | 260.6 | 26.4 | trafilatura preferred: cleanly stripped nav/boilerplates |

### What broke, and how I fixed it
1. **AsyncPG Cached Statement Invalidation on Neon:**
   - *Problem:* After executing DDL alterations (`ALTER TABLE documents ...`), asyncpg connections to Neon threw `InvalidCachedStatementError: cached statement plan is invalid due to a database schema or configuration change`.
   - *Fix:* Configured `connect_args={"statement_cache_size": 0}` in `src/kubeguide/db/session.py`. Disabling prepared statement caching ensures full compatibility with cloud connection poolers like Neon and PgBouncer.
2. **Column Length Limit for Deep File Paths:**
   - *Problem:* `Document.external_id` was initially constrained to `VARCHAR(64)`. Relative file paths such as `data/raw/k8s-docs/content/en/docs/concepts/architecture/mixed-version-proxy.md` (77 characters) failed with `value too long for type character varying(64)`.
   - *Fix:* Widened `external_id` from `VARCHAR(64)` to `VARCHAR(255)` in `models.py` and applied the database schema migration via Alembic.
3. **Variable Shadowing in SQLAlchemy Models:**
   - *Problem:* Inside `class Page(Base)`, defining a column named `text` shadowed SQLAlchemy's `text()` function, preventing default expressions like `text("'[]'::jsonb")`.
   - *Fix:* Used `server_default="[]"` for the `headings` column instead of calling `text()`.

### Stretch Tasks Implemented
1. **Page-by-page Scan Detection:**
   - Multi-page PDF ingestion in `src/kubeguide/ingest/parse.py` analyzes each page individually. Pages with fewer than 40 extracted characters are flagged as scanned/blank and stored in document metadata as `scanned_pages: [page_no, ...]`.
   - Verified by unit test `test_parse_pdf_scan_detection_records_scanned_pages`.
2. **Document Pages API Endpoint:**
   - Added `GET /v1/documents/{doc_id}/pages` supporting both full page list retrieval and specific page querying via `?page_no=N`.
   - Returns RFC 7807 problem details (`404 Not Found`) when the document or specific page number does not exist.
   - Fully unit tested in `tests/unit/test_api.py`.
3. **Corpus Coverage Calculation:**
   - Documented in `DATASET.md`: 422 files parsed out of 422 files in manifest = 100.0% corpus coverage.
