"""
Structured JSON Logging & Secret Redaction Module.
Provides JSON formatting, request_id context tracking, and automated scrubbing
of Bearer tokens and configured API secrets (QLOO_API_KEY, NEBIUS_API_KEY, etc.).
"""

from __future__ import annotations

from contextvars import ContextVar
from datetime import datetime, timezone
import json
import logging
import re
import sys
from typing import Any
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Context variable for tracking request ID across async tasks
request_id_ctx: ContextVar[str] = ContextVar("request_id_ctx", default="")

# Pattern for Bearer tokens
BEARER_PATTERN = re.compile(r"(Bearer\s+)[A-Za-z0-9\-_\.]+", re.IGNORECASE)


def get_request_id() -> str:
    """Return the current request_id from context or generate a fallback."""
    rid = request_id_ctx.get()
    return rid if rid else ""


def set_request_id(rid: str) -> None:
    """Set the current request_id in context."""
    request_id_ctx.set(rid)


def redact_secrets(text: str, extra_secrets: set[str] | None = None) -> str:
    """Scrub Bearer tokens and configured API keys from any text string."""
    if not isinstance(text, str) or not text:
        return text

    # Redact Bearer tokens
    redacted = BEARER_PATTERN.sub(r"\1[REDACTED]", text)

    # Gather configured secrets from settings
    try:
        from backend.app.core.config import get_settings
        secrets = get_settings().get_configured_secrets()
    except Exception:
        secrets = set()

    if extra_secrets:
        secrets.update(extra_secrets)

    for secret in secrets:
        if secret and len(secret) >= 4:
            redacted = redacted.replace(secret, "[REDACTED]")

    return redacted


class SecretRedactionFilter(logging.Filter):
    """Logging filter that redacts secrets from log messages and arguments."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_secrets(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: redact_secrets(v) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    redact_secrets(a) if isinstance(a, str) else a
                    for a in record.args
                )
        return True


class StructuredJsonFormatter(logging.Formatter):
    """Formatter outputting single-line JSON with timestamp, level, request_id, and redacted message."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": redact_secrets(record.getMessage()),
            "request_id": getattr(record, "request_id", None) or get_request_id() or None,
        }

        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            log_data["exception"] = redact_secrets(exc_text)

        # Include custom extra fields if provided
        for key, value in record.__dict__.items():
            if key not in (
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "id", "levelname", "levelno", "lineno", "module",
                "msecs", "message", "msg", "name", "pathname", "process",
                "processName", "relativeCreated", "stack_info", "thread",
                "threadName", "request_id"
            ) and not key.startswith("_"):
                log_data[key] = redact_secrets(str(value)) if isinstance(value, str) else value

        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO") -> None:
    """Configure root logger with StructuredJsonFormatter and SecretRedactionFilter."""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJsonFormatter())
    handler.addFilter(SecretRedactionFilter())
    root_logger.addHandler(handler)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware attaching request_id to context, request state, and response headers."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        req_id = request.headers.get("X-Request-ID")
        if not req_id or not req_id.strip():
            req_id = str(uuid4())

        set_request_id(req_id)
        request.state.request_id = req_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response
