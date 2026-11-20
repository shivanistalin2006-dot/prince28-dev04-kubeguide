"""Health and readiness probe endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from kubeguide.api.deps import check_db, get_app_settings
from kubeguide.config import Settings

router = APIRouter(tags=["health"])


@router.get("/health")
def get_health(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> dict[str, Any]:
    """Liveness probe: verifies service process is running and returns version."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.app_env,
        "version": settings.git_sha,
    }


@router.get("/ready")
async def get_ready(
    db_ok: Annotated[bool, Depends(check_db)],
) -> Any:
    """Readiness probe: verifies database connectivity."""
    if not db_ok:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "checks": {
                    "database": False,
                },
            },
        )

    return {
        "status": "ready",
        "checks": {
            "database": True,
        },
    }
