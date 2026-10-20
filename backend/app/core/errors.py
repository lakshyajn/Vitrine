"""
Core Error Envelopes and Exception Handlers.
Strictly conforms to Contract v0.2 Appendix A.5:
{"error": {"code": ..., "message": ..., "details": ..., "request_id": ...}}
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from contracts.schemas import ErrorCode
from backend.app.core.logging import get_request_id, redact_secrets

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Custom application exception mapping to standard ErrorCode and status code."""

    def __init__(
        self,
        code: ErrorCode | str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ):
        self.code = code.value if isinstance(code, ErrorCode) else str(code)
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


def _get_req_id(request: Request) -> str:
    """Retrieve request ID from request state, contextvar, or generate fallback."""
    return getattr(request.state, "request_id", None) or get_request_id() or str(uuid4())


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle custom AppError instances."""
    req_id = _get_req_id(request)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": redact_secrets(exc.message),
                "details": exc.details,
                "request_id": req_id,
            }
        },
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI / Pydantic request validation errors (422 -> validation_error)."""
    req_id = _get_req_id(request)

    details: dict[str, Any] = {}
    errors = exc.errors()

    for err in errors:
        loc = [str(x) for x in err.get("loc", []) if x != "body"]
        field_key = ".".join(loc) if loc else "payload"
        msg = err.get("msg", "Validation error")
        if field_key == "payload" and "price_min" in msg:
            field_key = "price_min"
        elif field_key == "payload" and "moq" in msg:
            field_key = "moq"
        details[field_key] = msg

    primary_msg = "Request validation failed"
    if details:
        first_field, first_reason = next(iter(details.items()))
        primary_msg = f"Invalid value for '{first_field}': {first_reason}"

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": ErrorCode.VALIDATION_ERROR.value,
                "message": redact_secrets(primary_msg),
                "details": details,
                "request_id": req_id,
            }
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle standard FastAPI HTTPException instances."""
    req_id = _get_req_id(request)

    status_to_code: dict[int, ErrorCode] = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        409: ErrorCode.CONFLICT,
        422: ErrorCode.VALIDATION_ERROR,
        429: ErrorCode.RATE_LIMITED,
        502: ErrorCode.UPSTREAM_UNAVAILABLE,
        503: ErrorCode.UPSTREAM_UNAVAILABLE,
        504: ErrorCode.UPSTREAM_TIMEOUT,
    }

    err_code = status_to_code.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
    message = str(exc.detail) if exc.detail else "An HTTP error occurred"

    details = None
    if isinstance(exc.detail, dict):
        details = exc.detail
        message = details.get("message", message)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": err_code.value,
                "message": redact_secrets(message),
                "details": details,
                "request_id": req_id,
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled server exceptions (500 -> internal_error)."""
    req_id = _get_req_id(request)
    logger.exception("Unhandled server exception: %s", redact_secrets(str(exc)))

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": ErrorCode.INTERNAL_ERROR.value,
                "message": "An internal server error occurred",
                "details": None,
                "request_id": req_id,
            }
        },
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register all error handlers onto the FastAPI application."""
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_exception_handler)  # type: ignore[arg-type]
