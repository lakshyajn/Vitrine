"""
Nebius / Nemotron Async HTTP Client (WS3 Section 3.2).
Supports Nebius Token Factory with automatic fallback to NVIDIA NIM (integrate.api.nvidia.com).
Implements explicit timeouts, bounded retries (max 2), exponential backoff + jitter,
and transparent fallback routing.
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any
import httpx

from backend.app.core.errors import AppError
from contracts.schemas import ErrorCode

logger = logging.getLogger(__name__)


class NebiusClient:
    def __init__(
        self,
        api_key: str,
        model_id: str = "nvidia/nemotron-3-ultra-550b-a55b",
        base_url: str = "https://api.tokenfactory.nebius.com/v1",
        timeout_seconds: float = 75.0,
        max_retries: int = 2,
        fallback_api_key: str | None = None,
        fallback_base_url: str = "https://integrate.api.nvidia.com/v1",
    ) -> None:
        self.api_key = api_key
        self.model_id = model_id
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.fallback_api_key = fallback_api_key
        self.fallback_base_url = fallback_base_url.rstrip("/")

    async def _try_fallback(
        self, body: dict[str, Any]
    ) -> tuple[str, int | None, int | None] | None:
        """Attempt seamless fallback to NVIDIA NIM endpoint if Token Factory fails."""
        fb_key = self.fallback_api_key or (self.api_key if self.api_key.startswith("nvapi-") else None)
        if not fb_key:
            return None
        fb_url = f"{self.fallback_base_url}/chat/completions"
        fb_headers = {
            "Authorization": f"Bearer {fb_key}",
            "Content-Type": "application/json",
        }
        try:
            logger.info("Nebius Token Factory failed; falling back to NVIDIA NIM (%s)", fb_url)
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                fb_resp = await client.post(fb_url, headers=fb_headers, json=body)
            if fb_resp.status_code == 200:
                data = fb_resp.json()
                msg = data["choices"][0]["message"]
                content = msg.get("content") or msg.get("reasoning_content") or ""
                usage = data.get("usage") or {}
                return (
                    content,
                    usage.get("prompt_tokens"),
                    usage.get("completion_tokens"),
                )
            logger.warning("NVIDIA NIM fallback returned HTTP %s: %s", fb_resp.status_code, fb_resp.text[:200])
        except Exception as exc:
            logger.warning("NVIDIA NIM fallback request error: %s", exc)
        return None

    async def complete_json(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
    ) -> tuple[str, int | None, int | None]:
        # If the key is directly an NVIDIA NIM key (nvapi-), route to NVIDIA endpoint immediately
        effective_base_url = self.base_url
        if self.api_key.startswith("nvapi-") and "tokenfactory.nebius.com" in self.base_url:
            effective_base_url = self.fallback_base_url

        url = f"{effective_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4096,
            "response_format": {"type": "json_object"},
        }

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(url, headers=headers, json=body)

                if response.status_code == 200:
                    data = response.json()
                    msg = data["choices"][0]["message"]
                    content = msg.get("content")
                    if not content and "reasoning_content" in msg:
                        content = msg["reasoning_content"]
                    usage = data.get("usage") or {}
                    return (
                        content or "",
                        usage.get("prompt_tokens"),
                        usage.get("completion_tokens"),
                    )

                # HTTP 401 Unauthorized on Token Factory: immediate fallback to NVIDIA NIM
                if response.status_code == 401 and "tokenfactory.nebius.com" in url:
                    fallback_result = await self._try_fallback(body)
                    if fallback_result is not None:
                        return fallback_result

                # Retryable status codes (429, 500, 502, 503, 504)
                if response.status_code in (429, 500, 502, 503, 504):
                    if attempt < self.max_retries:
                        delay = (0.4 * (2**attempt)) + random.uniform(0.05, 0.2)
                        await asyncio.sleep(delay)
                        continue
                    # Primary retries exhausted: try fallback before raising
                    if "tokenfactory.nebius.com" in url:
                        fallback_result = await self._try_fallback(body)
                        if fallback_result is not None:
                            return fallback_result
                    raise AppError(
                        code=ErrorCode.UPSTREAM_UNAVAILABLE,
                        message=f"Nebius API returned HTTP {response.status_code} after retries.",
                        status_code=502,
                    )

                # Other HTTP errors: try fallback before raising
                if "tokenfactory.nebius.com" in url:
                    fallback_result = await self._try_fallback(body)
                    if fallback_result is not None:
                        return fallback_result

                raise AppError(
                    code=ErrorCode.UPSTREAM_UNAVAILABLE,
                    message=f"Nebius API error HTTP {response.status_code}.",
                    status_code=502,
                )

            except httpx.TimeoutException as exc:
                if attempt < self.max_retries:
                    delay = (0.4 * (2**attempt)) + random.uniform(0.05, 0.2)
                    await asyncio.sleep(delay)
                    continue
                if "tokenfactory.nebius.com" in url:
                    fallback_result = await self._try_fallback(body)
                    if fallback_result is not None:
                        return fallback_result
                raise AppError(
                    code=ErrorCode.UPSTREAM_TIMEOUT,
                    message="Nebius API call timed out.",
                    status_code=504,
                ) from exc
            except httpx.RequestError as exc:
                if attempt < self.max_retries:
                    await asyncio.sleep(0.4 * (2**attempt))
                    continue
                if "tokenfactory.nebius.com" in url:
                    fallback_result = await self._try_fallback(body)
                    if fallback_result is not None:
                        return fallback_result
                raise AppError(
                    code=ErrorCode.UPSTREAM_UNAVAILABLE,
                    message=f"Nebius network connection failed: {exc}",
                    status_code=502,
                ) from exc

        if "tokenfactory.nebius.com" in url:
            fallback_result = await self._try_fallback(body)
            if fallback_result is not None:
                return fallback_result

        raise AppError(
            code=ErrorCode.UPSTREAM_UNAVAILABLE,
            message="Nebius API unavailable.",
            status_code=502,
        )
