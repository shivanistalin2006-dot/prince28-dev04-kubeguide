"""Redis-backed ARQ job queue wrapper. This is the only module that talks to Redis directly."""

from __future__ import annotations

from arq.connections import ArqRedis, RedisSettings, create_pool
from redis.exceptions import RedisError


class QueueUnavailableError(Exception):
    """Raised when the Redis job queue cannot be reached."""


def make_redis_settings(redis_url: str, *, fast_fail: bool = False) -> RedisSettings:
    """Parse a Redis DSN into ARQ RedisSettings."""
    rs = RedisSettings.from_dsn(redis_url)
    if fast_fail:
        rs.conn_timeout = 2
        rs.conn_retries = 0
        rs.conn_retry_delay = 0
    return rs


class JobQueue:
    """Thin async wrapper around an ARQ Redis pool."""

    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url
        self._pool: ArqRedis | None = None

    async def open(self) -> None:
        """Open the Redis connection pool if not already open."""
        if self._pool is not None:
            return
        try:
            self._pool = await create_pool(make_redis_settings(self.redis_url, fast_fail=True))
        except (OSError, RedisError, TimeoutError, Exception) as exc:
            self._pool = None
            raise QueueUnavailableError(f"The job queue (Redis) cannot be reached: {exc}") from exc

    async def close(self) -> None:
        """Close the underlying Redis pool cleanly."""
        if self._pool is not None:
            await self._pool.aclose()
            self._pool = None

    async def ping(self) -> bool:
        """Verify Redis connectivity."""
        await self.open()
        assert self._pool is not None
        try:
            return bool(await self._pool.ping())
        except (OSError, RedisError, TimeoutError) as exc:
            raise QueueUnavailableError(f"The job queue (Redis) cannot be reached: {exc}") from exc

    async def put(self, item_ids: list[int]) -> None:
        """Enqueue one ARQ job per IngestItem ID."""
        if not item_ids:
            return
        await self.open()
        assert self._pool is not None
        try:
            for item_id in item_ids:
                await self._pool.enqueue_job(
                    "ingest_document",
                    item_id,
                    _job_id=f"ingest:{item_id}",
                )
        except (OSError, RedisError, TimeoutError) as exc:
            raise QueueUnavailableError(f"The job queue (Redis) cannot be reached: {exc}") from exc
