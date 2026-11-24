"""Request ID, timing, structured logging, and crash-net middleware."""

import logging
import re
import time
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from kubeguide.api.errors import problem_response

logger = logging.getLogger(__name__)

_SAFE_REQUEST_ID_REGEX = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assigns request ID, tracks timing, logs access, and catches unhandled exceptions."""

    async def dispatch(self, request: Request, call_next) -> Response:
        raw_id = (request.headers.get("X-Request-ID") or "").strip()
        request_id = raw_id if raw_id and _SAFE_REQUEST_ID_REGEX.match(raw_id) else uuid4().hex[:16]

        request.state.request_id = request_id
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "unhandled exception during request",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(exc),
                },
            )
            return problem_response(
                status_code=500,
                title="Internal Server Error",
                detail="An unexpected error occurred.",
                instance=request.url.path,
                request_id=request_id,
            )

        duration_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"

        logger.info(
            "request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )

        return response


def register_middleware(app: FastAPI) -> None:
    """Register middleware on the FastAPI app."""
    app.add_middleware(RequestContextMiddleware)
