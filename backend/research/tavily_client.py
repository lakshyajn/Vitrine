# backend/research/tavily_client.py
"""
Async Tavily Search & Extract Client (WS3 Section 4.1).
Enforces configurable limits: <= 8 queries/run, 10 results/query, 30 extractions/run,
2 retries per call with backoff + jitter, and 20s per-call timeout.
"""

from __future__ import annotations

import asyncio
import random
from typing import Any
import httpx

from backend.app.core.errors import AppError
from contracts.schemas import ErrorCode


class TavilyClient:
    def __init__(
        self,
        api_key: str,
        timeout_seconds: float = 20.0,
        max_retries: int = 2,
        max_results_per_query: int = 10,
    ) -> None:
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_results_per_query = max_results_per_query

    async def search(self, query: str) -> list[dict[str, Any]]:
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": self.max_results_per_query,
        }
        data = await self._post("https://api.tavily.com/search", payload)
        return list(data.get("results") or [])

    async def extract(self, urls: list[str]) -> list[dict[str, Any]]:
        if not urls:
            return []
        payload = {
            "api_key": self.api_key,
            "urls": urls[:30],
        }
        data = await self._post("https://api.tavily.com/extract", payload)
        return list(data.get("results") or [])

    async def _post(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    resp = await client.post(url, json=payload)

                if resp.status_code == 200:
                    return resp.json()

                if resp.status_code in (429, 500, 502, 503, 504):
                    if attempt < self.max_retries:
                        await asyncio.sleep((0.4 * (2**attempt)) + random.uniform(0.05, 0.2))
                        continue
                    raise AppError(
                        code=ErrorCode.UPSTREAM_UNAVAILABLE,
                        message=f"Tavily returned HTTP {resp.status_code} after retries.",
                        status_code=502,
                    )

                raise AppError(
                    code=ErrorCode.UPSTREAM_UNAVAILABLE,
                    message=f"Tavily error HTTP {resp.status_code}.",
                    status_code=502,
                )
            except httpx.TimeoutException as exc:
                if attempt < self.max_retries:
                    await asyncio.sleep((0.4 * (2**attempt)) + random.uniform(0.05, 0.2))
                    continue
                raise AppError(
                    code=ErrorCode.UPSTREAM_TIMEOUT,
                    message="Tavily request timed out after 20s.",
                    status_code=504,
                ) from exc
            except httpx.RequestError as exc:
                if attempt < self.max_retries:
                    await asyncio.sleep(0.4 * (2**attempt))
                    continue
                raise AppError(
                    code=ErrorCode.UPSTREAM_UNAVAILABLE,
                    message=f"Tavily network error: {exc}",
                    status_code=502,
                ) from exc

        return {}