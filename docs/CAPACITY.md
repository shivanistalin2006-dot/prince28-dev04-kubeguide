# Capacity plan: KubeGuide

Full corpus target: + reference + release notes for 4 versions (2,500+ pages)

<!-- generated:start -->
## Measured on my start corpus (2026-11-23 09:10 UTC)

| What | Value |
|---|---|
| Files | 422 |
| Size on disk | 9.7 MB |
| Pages (PDF pages + 1 per 3,000 characters of text/HTML) | 1,505 |
| Characters of text | 4,515,862 |
| Estimated tokens (characters / 4) | 1,128,966 |
| Tokens per page | 750 |
| PDFs with almost no text (scanned? OCR is Day 7) | 0 |
| Files not measured (zip, xlsx, unreadable) | 0 |

## Estimate for the full corpus (target: 2,500 pages)

| What | How | Value |
|---|---|---|
| Scale factor | target / measured | x 1.7 |
| Tokens | measured tokens x scale | 1.87 M |
| Raw files | measured MB x scale | 16 MB |
| Chunks | tokens / 400 x 1.15 overlap | 5,391 |
| Embedding cost, one time | tokens x 1.15 x $0.15 per 1M | $0.32 = Rs 31 |
| Vector storage | chunks x 768 numbers x 4 bytes | 17 MB |
| Text in Postgres | characters x scale x 1.2 | 9 MB |

Assumptions: 4 characters per token, 400-token chunks, 768-dimension embeddings at $0.15 per 1M tokens, Rs 95 per US dollar.
<!-- generated:end -->

## What I conclude

1. **Is embedding cost a problem for this product?**
   No, one-time embedding cost is negligible at $0.32 (approx. Rs 31) for 1.87 M tokens.

2. **Do the vectors and text fit in my free Postgres?**
   Yes, combined vector storage (17 MB) and text storage (9 MB) total ~26 MB, comfortably within Neon's 500 MB free tier quota.

3. **Which number above am I least sure about, and how will I measure it better?**
   The tokens per page ratio (750 tokens/page estimated as chars / 4); I will measure exact token counts using a production tokenizer on Day 7.

4. **What changes if the corpus grows 10 times?**
   At 10x scale (25,000 pages), storage reaches ~260 MB (still within Neon's 500 MB limit) and embedding costs remain low at ~$3.20 (Rs 304). Query latency would require ivfflat or hnsw vector indexes to maintain sub-50ms search times.
