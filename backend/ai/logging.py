"""
Model Call Logging & Telemetry (WS3 Section 3.2).
Logs task, model_id, prompt_version, latency_ms, validation_ok, tokens, error_code.
Never logs API keys, Bearer tokens, or full email bodies.
"""

from __future__ import annotations

import logging
from uuid import UUID

from backend.ai.schemas import AICallLog

logger = logging.getLogger("backend.ai")

_CALL_HISTORY: list[AICallLog] = []


def log_ai_call(
    *,
    task: str,
    model_id: str,
    prompt_version: str = "v1.0",
    latency_ms: int,
    validation_ok: bool,
    tokens_in: int | None = None,
    tokens_out: int | None = None,
    error_code: str | None = None,
    run_id: UUID | None = None,
) -> AICallLog:
    entry = AICallLog(
        task=task,
        model_id=model_id,
        prompt_version=prompt_version,
        latency_ms=max(0, latency_ms),
        validation_ok=validation_ok,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        error_code=error_code,
        run_id=run_id,
    )
    _CALL_HISTORY.append(entry)
    if len(_CALL_HISTORY) > 500:
        _CALL_HISTORY.pop(0)

    logger.info(
        "ws3_ai_call task=%s model_id=%s version=%s latency_ms=%d valid=%s error=%s",
        task,
        model_id,
        prompt_version,
        entry.latency_ms,
        validation_ok,
        error_code,
    )
    return entry


def get_ai_call_history() -> list[AICallLog]:
    return list(_CALL_HISTORY)


def clear_ai_call_history() -> None:
    _CALL_HISTORY.clear()