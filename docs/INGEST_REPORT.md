# Ingestion Report: KubeGuide

<!-- generated:start -->
## Database snapshot (2026-11-27 12:42 UTC)

| Metric | Value |
|---|---:|
| Documents in PostgreSQL (`doc_type != 'record'`) | 409 |
| Pages of text | 1,685 |
| Characters of text | 4,092,910 |
| Tokens of text (`chars / 4`) | 1,023,227 |
| Structured metadata extracted (`extract_v1` ok) | 144 |
| Structured metadata extraction errors | 0 |
| Parse dead-letter table (`parse_failures`) | 3 |

## Background queue summary (`ingest_jobs` / `ingest_items`)

| Status | Count |
|---|---:|
| Total ingest jobs | 3 |
| Completed (`done`) | 27 |
| Skipped (`skipped`) | 0 |
| Failed (`failed`) | 12 |
| Active dead-letter items | 3 |
| Queued / Running | 0 |

## Dead-letter reasons

| Reason prefix | Count |
|---|---:|
| `parse:empty` | 3 |
| `parse` | 3 |

## LLM usage & cost (`llm_calls`)

| Purpose | Calls | Input tokens | Output tokens | Cost (INR) |
|---|---:|---:|---:|---:|
| extract | 291 | 396,453 | 122,053 | Rs 7.2462 |
| chat | 9 | 521 | 1,477 | Rs 0.0458 |
| **Total** | **300** | **396,974** | **123,530** | **Rs 7.2920** |

## Comparison against Monday's estimate (`docs/CAPACITY.md`)

| Metric | Monday estimate (`CAPACITY.md`) | Measured in PostgreSQL | Difference |
|---|---:|---:|---:|
| Start-corpus pages | 1,505 | 1,685 | +180 |
| Tokens of text | 1,128,966 | 1,023,227 | -105,739 |

Measured pages are slightly higher than Monday's `3,000`-char page estimate because paragraph-boundary splitting produces shorter chunks, while measured tokens of clean text are lower after stripping HTML navigation boilerplate and YAML frontmatter.
<!-- generated:end -->

## What I learnt

1. Separating the API (HTTP 202) from the background worker via Redis + Postgres keeps request
   latency flat even when ingestion involves slow downloads and rate-limited LLM calls.
2. Tracking item attempts and state in Postgres (`ingest_items`) ensures crash recovery: an
   abruptly killed worker leaves interrupted items recoverable after the visibility timeout without
   duplicating rows in `documents`.
3. Comparing actual extracted pages and tokens against Monday's `docs/CAPACITY.md` estimate
   highlights where cleaning boilerplates and HTML nav affects real token volume.
