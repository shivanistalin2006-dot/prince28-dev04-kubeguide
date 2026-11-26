"""CLI script to run structured metadata extraction over parsed documents in PostgreSQL."""

from __future__ import annotations

import argparse
import asyncio
import sys

from kubeguide.config import get_settings
from kubeguide.db.llm_calls import record_llm_call
from kubeguide.db.session import make_engine, make_sessionmaker
from kubeguide.llm.doc_meta import DocMeta
from kubeguide.llm.extract import run
from kubeguide.llm.gateway import build_gateway
from kubeguide.llm.prompts import load


async def _main(args: argparse.Namespace) -> int:
    settings = get_settings()
    ver, prompt_text = load(settings.prompts_dir, "extract")
    engine = make_engine(settings)
    session_factory = make_sessionmaker(engine)

    async def recorder(data: dict) -> None:
        async with session_factory() as s:
            await record_llm_call(s, data)

    gateway = build_gateway(settings, recorder=recorder)

    print(
        f"Starting extraction with extract_v{ver} "
        f"(limit={args.limit}, retry_failed={args.retry_failed}, "
        f"rpm={args.rpm}, schema={args.schema})...",
        flush=True,
    )

    try:
        summary = await run(
            session_factory,
            gateway,
            prompt_text,
            ver,
            DocMeta,
            limit=args.limit,
            retry_failed=args.retry_failed,
            rpm=args.rpm,
            use_schema=args.schema,
        )
    finally:
        await engine.dispose()

    print("\n=== Extraction Summary ===")
    for key, val in summary.items():
        print(f"  {key}: {val}")
    return 1 if summary.get("stopped_early") else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract structured metadata into PostgreSQL.")
    parser.add_argument("--limit", type=int, default=None, help="Max pending documents to process")
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Re-attempt documents that previously failed for the active prompt version",
    )
    parser.add_argument("--rpm", type=float, default=12.0, help="Max requests per minute")
    parser.add_argument(
        "--schema",
        action="store_true",
        help="Use native JSON schema response_format enforcement",
    )
    args = parser.parse_args()
    return asyncio.run(_main(args))


if __name__ == "__main__":
    sys.exit(main())
