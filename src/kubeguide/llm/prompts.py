"""Versioned prompt discovery and loading utilities."""

from __future__ import annotations

import re
from pathlib import Path


def versions(directory: Path, task: str) -> list[int]:
    """Return sorted numeric prompt versions for `<task>_v<n>.md` in `directory`."""
    if not directory.exists():
        return []
    pattern = re.compile(rf"^{re.escape(task)}_v(\d+)$")
    found: list[int] = []
    for path in directory.glob(f"{task}_v*.md"):
        match = pattern.match(path.stem)
        if match:
            found.append(int(match.group(1)))
    return sorted(found)


def load(directory: Path, task: str, version: int | None = None) -> tuple[int, str]:
    """Load `<task>_v<version>.md`, or the newest version when `version` is None."""
    if version is None:
        avail = versions(directory, task)
        if not avail:
            raise FileNotFoundError(
                f"No prompt files matching '{task}_v<n>.md' found in {directory}"
            )
        version = avail[-1]

    path = directory / f"{task}_v{version}.md"
    if not path.is_file():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return version, path.read_text(encoding="utf-8").strip()
