"""Unit tests for Settings and environment configuration."""

import pytest
from pydantic import ValidationError

from kubeguide.config import Settings


def test_settings_default_values() -> None:
    settings = Settings(app_env="local")

    assert settings.app_name == "kubeguide"
    assert settings.app_env == "local"
    assert settings.log_level == "INFO"
    assert settings.db_pool_size == 5
    assert settings.db_max_overflow == 10
    assert settings.db_pool_timeout_seconds == 30
    assert not settings.is_production


def test_settings_is_production() -> None:
    settings = Settings(app_env="production")

    assert settings.is_production is True


def test_settings_url_conversion_to_asyncpg() -> None:
    settings = Settings(
        app_env="local",
        database_url="postgresql://localhost:5432/kubeguide",
    )

    assert settings.database_url.startswith("postgresql+asyncpg://")


def test_settings_requires_app_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_ENV", raising=False)
    with pytest.raises(ValidationError):
        # Omitting app_env must fail fast
        Settings(_env_file=None)  # type: ignore[call-arg]
