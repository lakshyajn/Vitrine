"""
Qloo Orchestrator & Taste Provider Wrapper (Step 9 Part A).
Provides deterministic caching, audit logging to provider_calls,
per-run call quotas, exponential backoff retries, and failure isolation.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
import random
import re
import time
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select

from contracts.schemas import (
    CulturalAffinity,
    InsightOptions,
    TasteEntity,
    TasteSignal,
)
from backend.app.core.config import get_settings
from backend.app.core.logging import redact_secrets
from backend.app.db.models import ProviderCallModel, ResearchRunModel
from backend.app.db.session import async_session_maker
from backend.integrations.qloo.provider import (
    TasteResearchProvider,
    get_taste_provider,
)

logger = logging.getLogger(__name__)


def build_cache_key(endpoint: str, normalized_params: dict[str, Any]) -> str:
    """
    Build a deterministic cache key from (endpoint, json.dumps(normalized_params, sort_keys=True)).
    Uses SHA-256 for uniform length and index efficiency.
    """
    params_str = json.dumps(normalized_params, sort_keys=True)
    return hashlib.sha256(f"{endpoint}:{params_str}".encode("utf-8")).hexdigest()


def sanitize_params(params: Any) -> Any:
    """
    Deeply scrub QLOO_API_KEY, Bearer tokens, and any header credentials from params.
    """
    if isinstance(params, dict):
        sanitized: dict[str, Any] = {}
        for k, v in params.items():
            k_lower = str(k).lower()
            if any(term in k_lower for term in ("key", "secret", "token", "auth", "credential", "cookie")):
                sanitized[k] = "[REDACTED]"
            elif k_lower in ("headers", "header"):
                if isinstance(v, dict):
                    sanitized[k] = {
                        hk: (
                            "[REDACTED]"
                            if any(s in str(hk).lower() for s in ("auth", "key", "token", "secret", "cookie"))
                            else redact_secrets(str(hv))
                        )
                        for hk, hv in v.items()
                    }
                else:
                    sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_params(v)
        return sanitized
    elif isinstance(params, list):
        return [sanitize_params(x) for x in params]
    elif isinstance(params, str):
        return redact_secrets(params)
    return params


def does_signal_match_lead(
    signal_data: dict[str, Any] | TasteSignal,
    lead_location: dict[str, Any] | None,
    product_category: str | None = None,
    lead_retailer_type: str | None = None,
    anchor_category: str | None = None,
    lead_tier: str | None = None,
    category_fit_score: float | None = None,
) -> bool:
    """
    Evaluates whether a taste signal applies to a lead (Milestone F).
    Rules:
    - Never attach a hypothesis signal to an unqualified lead.
    - Never attach a hypothesis signal to a lead with unknown category fit.
    - If the lead has no verified location, returns False.
    - Requires a known location (region, city, or country matching signal text, or explicit anchor-to-region link).
    - Loose 4-letter category token matching is removed to prevent cross-category leakage.
    """
    # 1. Tier and category fit check
    if lead_tier and str(lead_tier).strip().lower() == "unqualified":
        return False
    if category_fit_score is None and (lead_tier is not None or category_fit_score is not None):
        return False

    # 2. Require known location
    loc = lead_location or {}
    region = str(loc.get("region") or "").strip().lower()
    country = str(loc.get("country") or "").strip().lower()
    city = str(loc.get("city") or "").strip().lower()

    if not region and not country and not city:
        return False

    if isinstance(signal_data, dict):
        text = str(signal_data.get("text") or "").lower()
        raw = signal_data.get("raw") or {}
        sig_region = str(signal_data.get("region_hint") or signal_data.get("region") or "").strip().lower()
    else:
        text = str(getattr(signal_data, "text", "") or "").lower()
        raw = getattr(signal_data, "raw", {}) or {}
        sig_region = str(getattr(signal_data, "region_hint", "") or getattr(signal_data, "region", "") or "").strip().lower()

    raw_str = str(raw).lower()

    # 3. Explicit anchor-to-region linkage
    if sig_region:
        if region and (region == sig_region or region in sig_region or sig_region in region):
            return True
        if country and (country == sig_region or country in sig_region or sig_region in country):
            return True
        if city and (city == sig_region or city in sig_region or sig_region in city):
            return True

    # 4. Verified location match against signal text
    for loc_token in (city, region, country):
        if loc_token and len(loc_token) >= 3:
            pattern = rf"\b{re.escape(loc_token)}\b"
            if re.search(pattern, text) or re.search(pattern, raw_str):
                return True

    return False


class QlooOrchestrator:
    """
    Orchestrates Qloo / Taste Provider calls with deterministic caching,
    per-run quota enforcement, retry with exponential backoff + jitter,
    audit logging into `provider_calls`, and complete failure isolation.
    """

    _run_call_counts: dict[str, int] = {}

    def __init__(
        self,
        run_id: UUID | None = None,
        owner_id: UUID | None = None,
        provider: TasteResearchProvider | None = None,
        max_calls_per_run: int | None = None,
        cache_ttl_hours: int | None = None,
    ) -> None:
        self.run_id = run_id
        self.owner_id = owner_id
        self.provider: TasteResearchProvider = provider or get_taste_provider()

        settings = get_settings()
        self.max_calls_per_run: int = (
            max_calls_per_run
            if max_calls_per_run is not None
            else getattr(settings, "qloo_max_calls_per_run", 20)
        )
        self.cache_ttl_hours: int = (
            cache_ttl_hours
            if cache_ttl_hours is not None
            else getattr(settings, "qloo_cache_ttl_hours", 24)
        )

        self.last_retrieved_at: datetime | None = None
        self.last_call_id: str | None = None

    @property
    def name(self) -> str:
        return getattr(self.provider, "name", "mock")

    @property
    def is_demo(self) -> bool:
        return getattr(self.provider, "is_demo", True)

    @classmethod
    def get_call_count(cls, run_id: UUID | str) -> int:
        return cls._run_call_counts.get(str(run_id), 0)

    @classmethod
    def reset_call_counts(cls, run_id: UUID | str | None = None) -> None:
        if run_id is None:
            cls._run_call_counts.clear()
        else:
            cls._run_call_counts.pop(str(run_id), None)

    async def _log_degraded_state(
        self,
        run_id: UUID | None,
        stage: str,
        reason: str,
    ) -> None:
        """Log degraded state in the research run's plan/inputs metadata."""
        if not run_id:
            return
        try:
            async with async_session_maker() as session:
                stmt = select(ResearchRunModel).where(ResearchRunModel.id == run_id)
                run = (await session.execute(stmt)).scalar_one_or_none()
                if run:
                    plan = dict(run.plan or {})
                    plan["taste_degraded"] = True
                    plan["taste_degraded_reason"] = reason
                    plan["taste_degraded_stage"] = stage
                    run.plan = plan

                    inputs = dict(run.inputs or {})
                    inputs["taste_degraded"] = True
                    inputs["taste_degraded_reason"] = reason
                    run.inputs = inputs
                    await session.commit()
        except Exception as exc:
            logger.warning("Failed to record degraded state on run %s: %s", run_id, exc)

    async def _write_provider_call(
        self,
        owner_id: UUID,
        run_id: UUID | None,
        endpoint: str,
        params: dict[str, Any],
        cache_key: str,
        status: str,
        latency_ms: int,
        response: dict[str, Any] | None,
        created_at: datetime | None = None,
    ) -> UUID:
        """Insert an audit log record into provider_calls table and return its UUID."""
        call_id = uuid4()
        clean_params = sanitize_params(params)
        record = ProviderCallModel(
            id=call_id,
            owner_id=owner_id,
            run_id=run_id,
            provider=self.name,
            endpoint=endpoint,
            params=clean_params if isinstance(clean_params, dict) else {"params": clean_params},
            cache_key=cache_key,
            status=status,
            latency_ms=latency_ms,
            response=response,
            created_at=created_at or datetime.now(timezone.utc),
        )
        try:
            async with async_session_maker() as session:
                session.add(record)
                await session.commit()
        except Exception as exc:
            logger.error("Failed to insert provider_calls record: %s", exc)
        return call_id

    def _is_transient_error(self, exc: Exception) -> bool:
        """Check if an exception is a transient timeout or HTTP 429 rate limit."""
        if isinstance(exc, (asyncio.TimeoutError, TimeoutError)):
            return True
        status_code = getattr(exc, "status_code", None)
        if status_code is None and hasattr(exc, "response"):
            status_code = getattr(exc.response, "status_code", None)
        if status_code in (408, 429, 504):
            return True
        err_msg = str(exc).lower()
        if "429" in err_msg or "rate limit" in err_msg or "timeout" in err_msg or "timed out" in err_msg:
            return True
        return False

    async def search_entities(
        self,
        query: str,
        owner_id: UUID | None = None,
        run_id: UUID | None = None,
        endpoint: str = "/v1/taste/search",
        session: Any = None,
    ) -> list[TasteEntity]:
        """
        Search taste entities with cache check, quota enforcement,
        retry on transient errors, and audit logging to provider_calls.
        """
        clean_query = (query or "").strip()
        effective_owner_id = owner_id or self.owner_id or UUID("00000000-0000-0000-0000-000000000000")
        effective_run_id = run_id or self.run_id
        run_key = str(effective_run_id) if effective_run_id else "global"

        normalized_params = {"query": clean_query.lower()}
        cache_key = build_cache_key(endpoint, normalized_params)

        # 1. Cache Lookup
        if self.cache_ttl_hours > 0:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=self.cache_ttl_hours)
            try:
                stmt = (
                    select(ProviderCallModel)
                    .where(
                        ProviderCallModel.cache_key == cache_key,
                        ProviderCallModel.status == "success",
                        ProviderCallModel.created_at >= cutoff,
                    )
                    .order_by(ProviderCallModel.created_at.desc())
                    .limit(1)
                )
                cached = None
                if session is not None:
                    cached = (await session.execute(stmt)).scalars().first()
                else:
                    async with async_session_maker() as db_session:
                        cached = (await db_session.execute(stmt)).scalars().first()

                if cached and cached.response:
                    raw_entities = (
                        cached.response.get("entities")
                        or cached.response.get("results")
                        or cached.response.get("data")
                        or []
                    )
                    cached_retrieved = cached.created_at
                    if cached.response.get("retrieved_at"):
                        try:
                            cached_retrieved = datetime.fromisoformat(cached.response["retrieved_at"])
                        except Exception:
                            pass
                    self.last_retrieved_at = cached_retrieved
                    self.last_call_id = str(cached.id)
                    logger.info("Cache hit for Qloo entity search: '%s'", clean_query)

                    entities: list[TasteEntity] = []
                    for item in raw_entities:
                        if isinstance(item, dict):
                            ent = TasteEntity.model_validate(item)
                        else:
                            ent = item
                        if hasattr(ent, "metadata") and isinstance(ent.metadata, dict):
                            ent.metadata["source_ref"] = str(cached.id)
                        entities.append(ent)
                    return entities
            except Exception as exc:
                logger.warning("Cache query failed for '%s': %s", clean_query, exc)

        # 2. Enforce Quotas
        current_calls = self._run_call_counts.get(run_key, 0)
        if current_calls >= self.max_calls_per_run:
            logger.warning("Qloo call quota of %d reached for run %s", self.max_calls_per_run, run_key)
            await self._log_degraded_state(
                effective_run_id,
                "anchor_proposal",
                f"Qloo quota of {self.max_calls_per_run} calls exceeded",
            )
            return []

        # 3. Call Provider with Retries
        max_retries = 2
        last_exc: Exception | None = None
        is_transient = False
        t0 = time.perf_counter()

        for attempt in range(max_retries + 1):
            try:
                t0 = time.perf_counter()
                raw_result = await self.provider.search_entities(clean_query)
                latency_ms = int((time.perf_counter() - t0) * 1000)

                # Successful live call
                self._run_call_counts[run_key] = current_calls + 1
                now = datetime.now(timezone.utc)
                self.last_retrieved_at = now

                serialized_entities = [
                    e.model_dump(mode="json") if hasattr(e, "model_dump") else dict(e)
                    for e in raw_result
                ]
                call_id = uuid4()
                record = ProviderCallModel(
                    id=call_id,
                    owner_id=effective_owner_id,
                    run_id=effective_run_id,
                    provider=self.name,
                    endpoint=endpoint,
                    params=sanitize_params({"query": clean_query}),
                    cache_key=cache_key,
                    status="success",
                    latency_ms=latency_ms,
                    response={
                        "entities": serialized_entities,
                        "retrieved_at": now.isoformat(),
                    },
                    created_at=now,
                )
                if session is not None:
                    session.add(record)
                else:
                    async with async_session_maker() as db_session:
                        db_session.add(record)
                        await db_session.commit()

                self.last_call_id = str(call_id)

                # Attach source_ref to entities metadata
                for ent in raw_result:
                    if hasattr(ent, "metadata") and isinstance(ent.metadata, dict):
                        ent.metadata["source_ref"] = str(call_id)

                return raw_result

            except Exception as exc:
                latency_ms = int((time.perf_counter() - t0) * 1000)
                last_exc = exc
                is_transient = self._is_transient_error(exc)
                if is_transient and attempt < max_retries:
                    delay = (0.2 * (2 ** attempt)) + random.uniform(0.01, 0.05)
                    logger.warning(
                        "Transient error searching entities '%s' (attempt %d/%d). Retrying in %.2fs: %s",
                        clean_query,
                        attempt + 1,
                        max_retries,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)
                    continue
                break

        # If exhausted or non-retryable error
        self._run_call_counts[run_key] = current_calls + 1
        final_status = "rate_limited" if is_transient else "error"
        logger.warning(
            "Qloo search_entities failed with status '%s' for '%s': %s",
            final_status,
            clean_query,
            last_exc,
        )

        call_id = uuid4()
        err_record = ProviderCallModel(
            id=call_id,
            owner_id=effective_owner_id,
            run_id=effective_run_id,
            provider=self.name,
            endpoint=endpoint,
            params=sanitize_params({"query": clean_query}),
            cache_key=cache_key,
            status=final_status,
            latency_ms=latency_ms,
            response={"error": str(last_exc)},
            created_at=datetime.now(timezone.utc),
        )
        if session is not None:
            session.add(err_record)
        else:
            async with async_session_maker() as db_session:
                db_session.add(err_record)
                await db_session.commit()

        self.last_call_id = str(call_id)

        await self._log_degraded_state(
            effective_run_id,
            "anchor_proposal",
            f"Taste entity search error: {str(last_exc)}",
        )
        return []

    async def get_insights(
        self,
        entity_id: str,
        options: InsightOptions | None = None,
        owner_id: UUID | None = None,
        run_id: UUID | None = None,
        endpoint: str = "/v1/taste/insights",
        session: Any = None,
    ) -> list[TasteSignal]:
        """
        Fetch taste signals/insights with cache check, quota enforcement,
        retry on transient errors, and audit logging to provider_calls.
        """
        clean_eid = (entity_id or "").strip()
        effective_owner_id = owner_id or self.owner_id or UUID("00000000-0000-0000-0000-000000000000")
        effective_run_id = run_id or self.run_id
        run_key = str(effective_run_id) if effective_run_id else "global"

        opt_dict = (
            options.model_dump(mode="json", exclude_none=True)
            if hasattr(options, "model_dump")
            else (dict(options) if options else {})
        )
        normalized_params = {"entity_id": clean_eid, **opt_dict}
        cache_key = build_cache_key(endpoint, normalized_params)

        # 1. Cache Lookup
        if self.cache_ttl_hours > 0:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=self.cache_ttl_hours)
            try:
                stmt = (
                    select(ProviderCallModel)
                    .where(
                        ProviderCallModel.cache_key == cache_key,
                        ProviderCallModel.status == "success",
                        ProviderCallModel.created_at >= cutoff,
                    )
                    .order_by(ProviderCallModel.created_at.desc())
                    .limit(1)
                )
                cached = None
                if session is not None:
                    cached = (await session.execute(stmt)).scalars().first()
                else:
                    async with async_session_maker() as db_session:
                        cached = (await db_session.execute(stmt)).scalars().first()

                if cached and cached.response:
                    raw_signals = (
                        cached.response.get("signals")
                        or cached.response.get("results")
                        or cached.response.get("data")
                        or []
                    )
                    cached_retrieved = cached.created_at
                    if cached.response.get("retrieved_at"):
                        try:
                            cached_retrieved = datetime.fromisoformat(cached.response["retrieved_at"])
                        except Exception:
                            pass
                    self.last_retrieved_at = cached_retrieved
                    self.last_call_id = str(cached.id)
                    logger.info("Cache hit for Qloo insights: '%s'", clean_eid)

                    signals: list[TasteSignal] = []
                    for item in raw_signals:
                        if isinstance(item, dict):
                            sig = TasteSignal.model_validate(item)
                        else:
                            sig = item
                        sig.source_ref = str(cached.id)
                        signals.append(sig)
                    return signals
            except Exception as exc:
                logger.warning("Cache query failed for insights '%s': %s", clean_eid, exc)

        # 2. Enforce Quotas
        current_calls = self._run_call_counts.get(run_key, 0)
        if current_calls >= self.max_calls_per_run:
            logger.warning("Qloo call quota of %d reached for run %s", self.max_calls_per_run, run_key)
            await self._log_degraded_state(
                effective_run_id,
                "discovery",
                f"Qloo quota of {self.max_calls_per_run} calls exceeded",
            )
            return []

        # 3. Call Provider with Retries
        max_retries = 2
        last_exc: Exception | None = None
        is_transient = False
        t0 = time.perf_counter()

        for attempt in range(max_retries + 1):
            try:
                t0 = time.perf_counter()
                raw_result = await self.provider.get_insights(
                    clean_eid,
                    options or InsightOptions(),
                )
                latency_ms = int((time.perf_counter() - t0) * 1000)

                # Successful live call
                self._run_call_counts[run_key] = current_calls + 1
                now = datetime.now(timezone.utc)
                self.last_retrieved_at = now

                serialized_signals = [
                    s.model_dump(mode="json") if hasattr(s, "model_dump") else dict(s)
                    for s in raw_result
                ]
                call_id = uuid4()
                record = ProviderCallModel(
                    id=call_id,
                    owner_id=effective_owner_id,
                    run_id=effective_run_id,
                    provider=self.name,
                    endpoint=endpoint,
                    params=sanitize_params(normalized_params),
                    cache_key=cache_key,
                    status="success",
                    latency_ms=latency_ms,
                    response={
                        "signals": serialized_signals,
                        "retrieved_at": now.isoformat(),
                    },
                    created_at=now,
                )
                if session is not None:
                    session.add(record)
                else:
                    async with async_session_maker() as db_session:
                        db_session.add(record)
                        await db_session.commit()

                self.last_call_id = str(call_id)

                # Set source_ref on all returned signals to the audit log UUID
                for sig in raw_result:
                    sig.source_ref = str(call_id)

                return raw_result

            except Exception as exc:
                latency_ms = int((time.perf_counter() - t0) * 1000)
                last_exc = exc
                is_transient = self._is_transient_error(exc)
                if is_transient and attempt < max_retries:
                    delay = (0.2 * (2 ** attempt)) + random.uniform(0.01, 0.05)
                    logger.warning(
                        "Transient error fetching insights for '%s' (attempt %d/%d). Retrying in %.2fs: %s",
                        clean_eid,
                        attempt + 1,
                        max_retries,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)
                    continue
                break

        # If exhausted or non-retryable error
        self._run_call_counts[run_key] = current_calls + 1
        final_status = "rate_limited" if is_transient else "error"
        logger.warning(
            "Qloo get_insights failed with status '%s' for '%s': %s",
            final_status,
            clean_eid,
            last_exc,
        )

        call_id = uuid4()
        err_record = ProviderCallModel(
            id=call_id,
            owner_id=effective_owner_id,
            run_id=effective_run_id,
            provider=self.name,
            endpoint=endpoint,
            params=sanitize_params(normalized_params),
            cache_key=cache_key,
            status=final_status,
            latency_ms=latency_ms,
            response={"error": str(last_exc)},
            created_at=datetime.now(timezone.utc),
        )
        if session is not None:
            session.add(err_record)
        else:
            async with async_session_maker() as db_session:
                db_session.add(err_record)
                await db_session.commit()

        self.last_call_id = str(call_id)

        await self._log_degraded_state(
            effective_run_id,
            "discovery",
            f"Taste insights error: {str(last_exc)}",
        )
        return []


def get_qloo_orchestrator(
    run_id: UUID | None = None,
    owner_id: UUID | None = None,
    provider: TasteResearchProvider | None = None,
) -> QlooOrchestrator:
    """Factory creating a QlooOrchestrator instance."""
    return QlooOrchestrator(run_id=run_id, owner_id=owner_id, provider=provider)
