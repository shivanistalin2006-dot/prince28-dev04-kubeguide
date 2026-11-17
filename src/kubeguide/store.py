"""In-memory document store loaded from JSON file."""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DocumentStore:
    """Store and query documents in memory."""

    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []
        self._loaded: bool = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def count(self) -> int:
        return len(self.records)

    def load_from_file(self, file_path: Path) -> None:
        """Load JSON records from disk."""
        if not file_path.exists():
            self._loaded = False
            self.records = []
            logger.warning("could not load records: file not found at %s", file_path)
            return

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.records = data
                else:
                    self.records = []
            self._loaded = True
            logger.info(
                "records loaded",
                extra={
                    "records": len(self.records),
                    "file": str(file_path),
                },
            )
        except Exception as exc:
            self._loaded = False
            self.records = []
            logger.warning("could not load records: %s", exc)

    def get_by_id(self, doc_id: str) -> dict[str, Any] | None:
        """Return document by its ID or None if not found."""
        for doc in self.records:
            if str(doc.get("id")) == str(doc_id):
                return doc
        return None

    def search(
        self,
        query: str | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> tuple[list[dict[str, Any]], int]:
        """Search documents with optional text filtering and pagination."""
        if query:
            q = query.lower()
            filtered = [
                doc
                for doc in self.records
                if any(q in str(val).lower() for val in doc.values())
            ]
        else:
            filtered = self.records

        total = len(filtered)
        items = filtered[offset : offset + limit]
        return items, total
