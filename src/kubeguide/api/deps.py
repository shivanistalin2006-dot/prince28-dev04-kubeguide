"""FastAPI dependency injection providers."""

from fastapi import Request

from kubeguide.config import Settings, get_settings
from kubeguide.store import DocumentStore


def get_app_settings() -> Settings:
    """Dependency to retrieve application settings."""
    return get_settings()


def get_document_store(request: Request) -> DocumentStore:
    """Dependency to retrieve the initialized DocumentStore from app state."""
    return request.app.state.store
