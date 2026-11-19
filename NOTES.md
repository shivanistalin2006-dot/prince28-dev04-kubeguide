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

### Tests and coverage
```text
uv run poe test -> 16 passed in 0.46s
uv run poe test-integration -> 7 passed in 2.15s (7 skipped without live container)
coverage TOTAL, unit only -> TOTAL 297 42 50 8 82%
coverage TOTAL, with integration tests -> TOTAL 297 12 50 2 96%
```
