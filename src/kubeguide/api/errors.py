"""RFC 9457 Problem Details error models and exception handlers."""

from typing import Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ProblemDetails(BaseModel):
    """RFC 9457 Problem Details schema."""

    type: str = "about:blank"
    title: str
    status: int
    detail: str
    instance: str | None = None
    request_id: str | None = None
    errors: list[dict[str, Any]] | None = None


class NotFoundProblem(HTTPException):
    """Exception for 404 Not Found problem details."""

    def __init__(
        self,
        detail: str,
        instance: str | None = None,
        title: str = "Not Found",
    ) -> None:
        super().__init__(status_code=404, detail=detail)
        self.title = title
        self.instance = instance


def problem_response(
    status_code: int,
    title: str,
    detail: str,
    instance: str | None = None,
    request_id: str | None = None,
    errors: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    """Build an RFC 9457 application/problem+json response."""
    content: dict[str, Any] = {
        "type": "about:blank",
        "title": title,
        "status": status_code,
        "detail": detail,
    }
    if instance is not None:
        content["instance"] = instance
    if request_id is not None:
        content["request_id"] = request_id
    if errors is not None:
        content["errors"] = errors

    headers = {}
    if request_id:
        headers["X-Request-ID"] = request_id

    return JSONResponse(
        status_code=status_code,
        content=content,
        media_type="application/problem+json",
        headers=headers,
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register RFC 9457 exception handlers on the FastAPI application."""

    @app.exception_handler(NotFoundProblem)
    async def not_found_problem_handler(
        request: Request, exc: NotFoundProblem
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", request.headers.get("X-Request-ID"))
        return problem_response(
            status_code=404,
            title=exc.title,
            detail=exc.detail,
            instance=exc.instance or request.url.path,
            request_id=request_id,
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", request.headers.get("X-Request-ID"))
        title = getattr(exc, "title", None)
        if not title:
            titles = {
                400: "Bad Request",
                401: "Unauthorized",
                403: "Forbidden",
                404: "Not Found",
                409: "Conflict",
                422: "Unprocessable Entity",
                500: "Internal Server Error",
                503: "Service Unavailable",
            }
            title = titles.get(exc.status_code, "Error")

        instance = getattr(exc, "instance", request.url.path)
        return problem_response(
            status_code=exc.status_code,
            title=title,
            detail=str(exc.detail),
            instance=instance,
            request_id=request_id,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", request.headers.get("X-Request-ID"))
        errors = []
        for err in exc.errors():
            loc_parts = err.get("loc", ())
            field = ".".join(str(p) for p in loc_parts)
            errors.append({"field": field, "message": err.get("msg", "Invalid")})

        return problem_response(
            status_code=422,
            title="Unprocessable Entity",
            detail="Validation error",
            instance=request.url.path,
            request_id=request_id,
            errors=errors,
        )
