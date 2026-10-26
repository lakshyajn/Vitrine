"""
Per-User In-Memory Sliding-Window Rate Limiter.
Applies sliding-window rate limits to expensive endpoints (POST /research-runs, POST /outreach-drafts).
Raises AppError(code="rate_limited", message="Too many requests, please retry shortly", status_code=429).
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
import time
from uuid import UUID

from fastapi import Depends

from backend.app.auth.deps import CurrentUser, current_user
from backend.app.core.errors import AppError


class RateLimiter:
    """
    Lightweight in-memory sliding-window rate limiter per authenticated user.
    """

    def __init__(self, limit: int = 10, window_seconds: int = 60, name: str = "default") -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.name = name
        self._history: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def __call__(self, user: CurrentUser = Depends(current_user)) -> None:
        user_key = f"{self.name}:{user.id}"
        now = time.monotonic()
        cutoff = now - self.window_seconds

        async with self._lock:
            # Filter timestamps within current sliding window
            valid_timestamps = [t for t in self._history[user_key] if t > cutoff]
            if len(valid_timestamps) >= self.limit:
                raise AppError(
                    code="rate_limited",
                    message="Too many requests, please retry shortly",
                    status_code=429,
                )
            valid_timestamps.append(now)
            self._history[user_key] = valid_timestamps

    def reset(self, user_id: UUID | str | None = None) -> None:
        if user_id is None:
            self._history.clear()
        else:
            self._history.pop(f"{self.name}:{user_id}", None)


# Global instances for endpoint rate limits (default 10 requests / 60 seconds)
research_runs_rate_limiter = RateLimiter(limit=10, window_seconds=60, name="research_runs")
outreach_drafts_rate_limiter = RateLimiter(limit=10, window_seconds=60, name="outreach_drafts")


def reset_rate_limiters() -> None:
    """Reset all active rate limiters (used in test teardown/setup)."""
    research_runs_rate_limiter.reset()
    outreach_drafts_rate_limiter.reset()
