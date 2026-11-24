"""Parse and summarize corpus manifest records.

Usage:
    uv run python scripts/manifest_summary.py [path/to/manifest.jsonl]
"""

import json
import sys
from collections import defaultdict
from pathlib import Path


def summarize_manifest(manifest_path: Path) -> dict[str, int | float | dict[str, dict[str, int]]]:
    """Parse JSONL manifest and compute aggregate statistics."""
    if not manifest_path.exists():
        return {"total_files": 0, "total_bytes": 0, "total_pages": 0, "sources": {}}

    total_files = 0
    total_bytes = 0
    total_pages = 0
    source_stats: dict[str, dict[str, int]] = defaultdict(
        lambda: {"files": 0, "bytes": 0, "pages": 0}
    )

    with manifest_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            total_files += 1
            b = int(entry.get("bytes", 0))
            p = int(entry.get("pages", 1) or 1)
            src = str(entry.get("source", "unknown"))

            total_bytes += b
            total_pages += p

            source_stats[src]["files"] += 1
            source_stats[src]["bytes"] += b
            source_stats[src]["pages"] += p

    return {
        "total_files": total_files,
        "total_bytes": total_bytes,
        "total_mb": round(total_bytes / (1024 * 1024), 2),
        "total_pages": total_pages,
        "sources": dict(source_stats),
    }


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/manifest.jsonl")
    if not path.exists():
        print(f"Manifest file not found: {path}", file=sys.stderr)
        return 1

    stats = summarize_manifest(path)
    print("=== Corpus Manifest Summary ===")
    print(f"Total files: {stats['total_files']}")
    print(f"Total size:  {stats['total_mb']} MB ({stats['total_bytes']:,} bytes)")
    print(f"Total pages: {stats['total_pages']}")
    print("\nBreakdown by Source:")
    for src, data in stats["sources"].items():  # type: ignore[union-attr]
        mb = round(data["bytes"] / (1024 * 1024), 2)
        print(f"  • {src}: {data['files']} files | {mb} MB | {data['pages']} pages")

    return 0


if __name__ == "__main__":
    sys.exit(main())
