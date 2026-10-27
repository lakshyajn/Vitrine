"""
Nebius / Nemotron Async HTTP Client (WS3 Section 3.2).
Supports Nebius AI Studio, NVIDIA NIM, OpenRouter, or local Ollama endpoints.
Implements explicit timeouts, bounded retries (max 2), and exponential backoff + jitter.
"""

from __future__ import annotations

import asyncio
import random
import httpx

from backend.app.core.errors import AppError
from contracts.schemas import ErrorCode


class NebiusClient:
    def __init__(
        self,
        api_key: str,
        model_id: str = "nvidia/nemotron-3-ultra-550b-a55b",
        base_url: str = "https://integrate.api.nvidia.com/v1",
        timeout_seconds: float = 75.0,
        max_retries: int = 2,
    ) -> None:
        self.api_key = api_key
        self.model_id = model_id
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    async def complete_json(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
    ) -> tuple[str, int | None, int | None]:
        url = f"{self.base_url}/chat/completions"
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

                if response.status_code in (429, 500, 502, 503, 504):
                    if attempt < self.max_retries:
                        delay = (0.4 * (2**attempt)) + random.uniform(0.05, 0.2)
                        await asyncio.sleep(delay)
                        continue
                    raise AppError(
                        code=ErrorCode.UPSTREAM_UNAVAILABLE,
                        message=f"Nebius API returned HTTP {response.status_code} after retries.",
                        status_code=502,
                    )

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
                raise AppError(
                    code=ErrorCode.UPSTREAM_TIMEOUT,
                    message="Nebius API call timed out.",
                    status_code=504,
                ) from exc
            except httpx.RequestError as exc:
                if attempt < self.max_retries:
                    await asyncio.sleep(0.4 * (2**attempt))
                    continue
                raise AppError(
                    code=ErrorCode.UPSTREAM_UNAVAILABLE,
                    message=f"Nebius network connection failed: {exc}",
                    status_code=502,
                ) from exc

        raise AppError(
            code=ErrorCode.UPSTREAM_UNAVAILABLE,
            message="Nebius API unavailable.",
            status_code=502,
        )