"""Data models for corpus ingestion batches and metrics."""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class IngestionBatch:
    """Represents a discrete corpus ingestion run."""

    batch_id: str
    source: str
    file_count: int
    total_bytes: int
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def megabytes(self) -> float:
        """Return total size in megabytes."""
        return round(self.total_bytes / (1024 * 1024), 2)


@dataclass
class FetchMetrics:
    """Tracks live crawler metrics during corpus downloads."""

    urls_processed: int = 0
    bytes_streamed: int = 0
    skipped_existing: int = 0
    blocked_robots: int = 0
    failed_requests: int = 0

    @property
    def total_attempted(self) -> int:
        """Total number of URLs evaluated."""
        return (
            self.urls_processed + self.skipped_existing + self.blocked_robots + self.failed_requests
        )

    @property
    def success_rate_percent(self) -> float:
        """Percentage of successfully processed URLs."""
        if not self.total_attempted:
            return 100.0
        return round((self.urls_processed / self.total_attempted) * 100, 1)
