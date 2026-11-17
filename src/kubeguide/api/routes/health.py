"""Health and readiness probe endpoints."""

from typing import Any
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from kubeguide.api.deps import get_app_settings, get_document_store
from kubeguide.config import Settings
from kubeguide.store import DocumentStore

router = APIRouter(tags=["health"])


@router.get("/health")
def get_health(
    settings: Settings = Depends(get_app_settings),
) -> dict[str, Any]:
    """Liveness probe: verifies service process is running."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
    }


@router.get("/ready")
def get_ready(
    store: DocumentStore = Depends(get_document_store),
) -> Any:
    """Readiness probe: verifies document store is loaded."""
    if not store.is_loaded:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "checks": {
                    "records_loaded": False,
                },
            },
        )

    return {
        "status": "ok",
        "checks": {
            "records_loaded": True,
        },
    }
