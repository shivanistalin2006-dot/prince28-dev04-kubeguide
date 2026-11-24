"""All settings come from environment variables (or a local .env file)."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from kubeguide.db.url import to_asyncpg_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "kubeguide"
    # No default on purpose: if APP_ENV is missing, the app refuses to start (fail fast).
    app_env: Literal["local", "ci", "production"]
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    data_file: Path = Path("data/sample_records.json")
    database_url: str = "postgresql://localhost:5432/kubeguide"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout_seconds: int = 30
    # The commit this image was built from. CI sets it (Dockerfile ARG GIT_SHA); locally "dev".
    git_sha: str = "dev"

    @property
    def is_production(self) -> bool:
        """Return True if running in production mode."""
        return self.app_env == "production"

    @field_validator("database_url")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        return to_asyncpg_url(v)


@lru_cache
def get_settings() -> Settings:
    """Build the settings once and reuse them."""
    return Settings()
