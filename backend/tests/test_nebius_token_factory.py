"""
Tests for Nebius Token Factory & NVIDIA Nemotron Integration.
Verifies:
1. Client initialization with Nebius Token Factory endpoint (https://api.tokenfactory.nebius.com/v1).
2. Dual-model task allocation (Task A/C on Super VL 120B, Task B/D on Ultra 550B).
3. Resilience, retry on 429/500/502/503, and single-repair schema recovery.
4. Dynamic runtime fallback from Token Factory to NVIDIA NIM on 401, 502, 429, or timeout.
5. Configuration fallback: when Token Factory key is not found, smoothly runs as before
   Token Factory using integrate.api.nvidia.com/v1 and respective Ultra/Super keys.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import httpx
import pytest

from backend.ai.client import NebiusClient
from backend.ai.service import (
    FixtureAIService,
    LiveAIService,
    build_outreach_fact_catalog,
    get_ai_service,
)
from backend.app.core.errors import AppError
from contracts.schemas import (
    DimensionLabel,
    EvidenceItem,
    EvidenceSourceType,
    Lead,
    LeadCandidate,
    OutreachDraft,
    OutreachDraftStatus,
    PriceSegment,
    Product,
    ProductAttributes,
    ProductInput,
    ResearchPlan,
)


# -----------------------------------------------------------------------------
# 1. NebiusClient Unit Tests
# -----------------------------------------------------------------------------

def test_nebius_client_default_endpoint():
    """Verify NebiusClient defaults to the official Nebius Token Factory OpenAI-compatible endpoint."""
    client = NebiusClient(api_key="test-key")
    assert client.base_url == "https://api.tokenfactory.nebius.com/v1"
    assert client.model_id == "nvidia/nemotron-3-ultra-550b-a55b"
    assert client.timeout_seconds == 75.0
    assert client.max_retries == 2


@pytest.mark.asyncio
async def test_nebius_client_complete_json_success():
    """Verify NebiusClient parses choices, message content, and token counts from standard OpenAI format."""
    mock_response = httpx.Response(
        status_code=200,
        json={
            "id": "chatcmpl-test",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": '{"status": "ok", "categories": ["linens"]}',
                    }
                }
            ],
            "usage": {"prompt_tokens": 42, "completion_tokens": 15},
        },
        request=httpx.Request("POST", "https://api.tokenfactory.nebius.com/v1/chat/completions"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        client = NebiusClient(api_key="test-token-factory-key")
        content, p_tok, c_tok = await client.complete_json([{"role": "user", "content": "hello"}])

        assert content == '{"status": "ok", "categories": ["linens"]}'
        assert p_tok == 42
        assert c_tok == 15
        assert mock_post.called
        call_headers = mock_post.call_args[1]["headers"]
        assert call_headers["Authorization"] == "Bearer test-token-factory-key"


@pytest.mark.asyncio
async def test_nebius_client_reasoning_content_fallback():
    """Verify support for models returning reasoning_content (e.g. DeepSeek / Nemotron reasoning variants)."""
    mock_response = httpx.Response(
        status_code=200,
        json={
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "reasoning_content": '{"decision": "approved"}',
                    }
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        },
        request=httpx.Request("POST", "https://api.tokenfactory.nebius.com/v1/chat/completions"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        client = NebiusClient(api_key="test-key")
        content, _, _ = await client.complete_json([{"role": "user", "content": "query"}])
        assert content == '{"decision": "approved"}'


@pytest.mark.asyncio
async def test_nebius_client_retries_on_rate_limit():
    """Verify exponential backoff retry when encountering HTTP 429 rate limits."""
    resp_429 = httpx.Response(
        status_code=429,
        text="Rate limited",
        request=httpx.Request("POST", "https://api.tokenfactory.nebius.com/v1/chat/completions"),
    )
    resp_200 = httpx.Response(
        status_code=200,
        json={"choices": [{"message": {"content": '{"recovered": true}'}}]},
        request=httpx.Request("POST", "https://api.tokenfactory.nebius.com/v1/chat/completions"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        mock_post.side_effect = [resp_429, resp_200]
        client = NebiusClient(api_key="test-key", max_retries=2)
        content, _, _ = await client.complete_json([{"role": "user", "content": "ping"}])

        assert content == '{"recovered": true}'
        assert mock_post.call_count == 2
        assert mock_sleep.called


# -----------------------------------------------------------------------------
# 2. Runtime Fallback Tests (Token Factory -> NVIDIA NIM)
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_nebius_client_runtime_fallback_on_401():
    """Verify that HTTP 401 on Token Factory triggers seamless fallback to NVIDIA NIM."""
    tf_401 = httpx.Response(
        status_code=401,
        text="Unauthorized token",
        request=httpx.Request("POST", "https://api.tokenfactory.nebius.com/v1/chat/completions"),
    )
    nvidia_200 = httpx.Response(
        status_code=200,
        json={
            "choices": [{"message": {"content": '{"source": "nvidia_nim_fallback"}'}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 20},
        },
        request=httpx.Request("POST", "https://integrate.api.nvidia.com/v1/chat/completions"),
    )

    client = NebiusClient(
        api_key="bad-tf-token",
        base_url="https://api.tokenfactory.nebius.com/v1",
        fallback_api_key="nvapi-ultra-fallback-key",
        fallback_base_url="https://integrate.api.nvidia.com/v1",
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # First call hits Token Factory -> returns 401. Fallback hits NVIDIA NIM -> returns 200.
        mock_post.side_effect = [tf_401, nvidia_200]
        content, p_tok, c_tok = await client.complete_json([{"role": "user", "content": "hello"}])

        assert content == '{"source": "nvidia_nim_fallback"}'
        assert p_tok == 100
        assert c_tok == 20
        assert mock_post.call_count == 2

        # Verify fallback call headers used the respective NVIDIA key and endpoint
        fallback_call = mock_post.call_args_list[1]
        assert str(fallback_call[0][0]) == "https://integrate.api.nvidia.com/v1/chat/completions"
        assert fallback_call[1]["headers"]["Authorization"] == "Bearer nvapi-ultra-fallback-key"


@pytest.mark.asyncio
async def test_nebius_client_runtime_fallback_on_502_upstream_failure():
    """Verify that persistent 502 on Token Factory triggers fallback to NVIDIA NIM."""
    tf_502 = httpx.Response(
        status_code=502,
        text="Bad Gateway",
        request=httpx.Request("POST", "https://api.tokenfactory.nebius.com/v1/chat/completions"),
    )
    nvidia_200 = httpx.Response(
        status_code=200,
        json={"choices": [{"message": {"content": '{"source": "nvidia_recovered"}'}}]},
        request=httpx.Request("POST", "https://integrate.api.nvidia.com/v1/chat/completions"),
    )

    client = NebiusClient(
        api_key="tf-key",
        base_url="https://api.tokenfactory.nebius.com/v1",
        max_retries=1,
        fallback_api_key="nvapi-super-fallback-key",
        fallback_base_url="https://integrate.api.nvidia.com/v1",
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("asyncio.sleep", new_callable=AsyncMock):
        # Initial call + 1 retry on Token Factory -> both 502, then fallback to NVIDIA -> 200
        mock_post.side_effect = [tf_502, tf_502, nvidia_200]
        content, _, _ = await client.complete_json([{"role": "user", "content": "test"}])

        assert content == '{"source": "nvidia_recovered"}'
        assert mock_post.call_count == 3
        fallback_call = mock_post.call_args_list[2]
        assert "integrate.api.nvidia.com" in str(fallback_call[0][0])
        assert fallback_call[1]["headers"]["Authorization"] == "Bearer nvapi-super-fallback-key"


@pytest.mark.asyncio
async def test_nebius_client_direct_nvidia_routing_for_nvapi_keys():
    """Verify that when an nvapi-* key is used, it immediately routes to NVIDIA NIM without hitting Token Factory."""
    nvidia_200 = httpx.Response(
        status_code=200,
        json={"choices": [{"message": {"content": '{"direct": true}'}}]},
        request=httpx.Request("POST", "https://integrate.api.nvidia.com/v1/chat/completions"),
    )

    client = NebiusClient(
        api_key="nvapi-direct-key-12345",
        base_url="https://api.tokenfactory.nebius.com/v1",
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = nvidia_200
        content, _, _ = await client.complete_json([{"role": "user", "content": "direct"}])

        assert content == '{"direct": true}'
        assert mock_post.call_count == 1
        called_url = str(mock_post.call_args[0][0])
        assert called_url == "https://integrate.api.nvidia.com/v1/chat/completions"


# -----------------------------------------------------------------------------
# 3. Dual-Model LiveAIService Routing Tests
# -----------------------------------------------------------------------------

def test_live_ai_service_model_assignment():
    """Verify Task A & C are assigned to Fast client (Super VL 120B), and B & D to Primary (Ultra 550B)."""
    primary = NebiusClient(
        api_key="key-ultra",
        model_id="nvidia/nemotron-3-ultra-550b-a55b",
        base_url="https://api.tokenfactory.nebius.com/v1",
    )
    fast = NebiusClient(
        api_key="key-fast",
        model_id="nvidia/nemotron-3.5-super-vl-120b-a12b",
        base_url="https://api.tokenfactory.nebius.com/v1",
    )

    service = LiveAIService(client=primary, fast_client=fast)
    assert service.model_id == "nvidia/nemotron-3-ultra-550b-a55b"
    assert service.fast_model_id == "nvidia/nemotron-3.5-super-vl-120b-a12b"


@pytest.mark.asyncio
async def test_structure_product_uses_fast_model_with_fallback():
    """Verify Task A calls fast client first and falls back to primary client if fast client fails."""
    primary = NebiusClient(api_key="primary-key", model_id="ultra-550b")
    fast = NebiusClient(api_key="fast-key", model_id="super-120b")

    # Fast client fails with upstream timeout, Primary client succeeds
    fast.complete_json = AsyncMock(side_effect=AppError(code="upstream_timeout", message="Upstream timeout"))
    valid_attrs = {
        "materials": ["organic cotton", "linen"],
        "motifs": ["botanical woodblock"],
        "price_segment": "mid_premium",
        "price_min": 45.0,
        "price_max": 85.0,
        "moq": 12,
        "category": "Home Textiles",
    }
    primary.complete_json = AsyncMock(return_value=(json.dumps(valid_attrs), 100, 50))

    service = LiveAIService(client=primary, fast_client=fast)
    result = await service.structure_product("Hand block printed cotton cushion covers")

    assert isinstance(result, ProductAttributes)
    assert result.category == "Home Textiles"
    assert result.moq == 12
    assert fast.complete_json.called
    assert primary.complete_json.called


@pytest.mark.asyncio
async def test_plan_research_uses_primary_ultra_model():
    """Verify Task B calls primary model (Ultra 550B) for deep market reasoning."""
    primary = NebiusClient(api_key="primary-key", model_id="ultra-550b")
    fast = NebiusClient(api_key="fast-key", model_id="super-120b")

    plan_data = {
        "target_regions": ["Western Europe"],
        "target_retailer_types": ["independent concept boutique"],
        "aesthetic_candidates": ["botanical", "scandinavian modern"],
        "search_queries": ["independent design concept stores copenhagen"],
        "hypotheses_rationale": "High affinity for natural fibers and artisanal textiles in Scandinavia.",
        "notes": "Focused search queries for Western Europe concept stores",
    }
    primary.complete_json = AsyncMock(return_value=(json.dumps(plan_data), 200, 100))

    product = Product(
        owner_id=uuid4(),
        name="Artisan Table Linens",
        category="Home Textiles",
        description="Handcrafted block printed napkins and table runners",
        materials=["pure linen"],
        motifs=["botanical woodblock"],
        price_segment=PriceSegment.MID_PREMIUM,
        moq=12,
    )

    service = LiveAIService(client=primary, fast_client=fast)
    plan = await service.plan_research(product)

    assert isinstance(plan, ResearchPlan)
    assert len(plan.target_regions) == 1
    assert "Western Europe" in plan.target_regions
    assert primary.complete_json.called


@pytest.mark.asyncio
async def test_assess_lead_truth_preservation():
    """Verify Task C assesses lead against verified evidence and preserves unverified gaps."""
    fast = NebiusClient(api_key="fast-key", model_id="super-120b")
    primary = NebiusClient(api_key="primary-key", model_id="ultra-550b")

    lead_id = uuid4()
    evidence_id = uuid4()
    candidate = LeadCandidate(
        id=lead_id,
        name="Nordic Living Stockholm",
        website="https://nordicliving.se",
        canonical_domain="nordicliving.se",
    )
    evidence = [
        EvidenceItem(
            id=evidence_id,
            lead_id=lead_id,
            url="https://nordicliving.se/brands",
            excerpt="We stock curated European artisan home goods, ceramics, and handwoven textiles.",
            source_type=EvidenceSourceType.OFFICIAL_SITE,
        )
    ]
    product = Product(
        owner_id=uuid4(),
        name="Artisan Table Linens",
        category="Home Textiles",
        description="Handcrafted block printed napkins and table runners",
        materials=["pure linen"],
        motifs=["botanical"],
        price_segment=PriceSegment.MID_PREMIUM,
        moq=12,
    )

    assessment_data = {
        "category_fit": {
            "label": "high",
            "reasons": ["Stocks curated European artisan home goods and textiles."],
            "evidence_ids": [str(evidence_id)],
        },
        "aesthetic_fit": {
            "label": "high",
            "reasons": ["Store visual identity aligns with natural handcrafted linen collections."],
            "evidence_ids": [str(evidence_id)],
        },
        "seller_compat": {
            "label": "unknown",
            "reasons": [],
            "evidence_ids": [],
        },
        "summary": "Strong retail vector for artisanal home textiles.",
        "unknowns": ["No public wholesale ordering minimums or trade terms found on store website."],
    }
    fast.complete_json = AsyncMock(return_value=(json.dumps(assessment_data), 150, 80))

    service = LiveAIService(client=primary, fast_client=fast)
    assessment = await service.assess_lead(product, candidate, evidence)

    assert assessment.category_fit.label == DimensionLabel.HIGH
    assert assessment.aesthetic_fit.label == DimensionLabel.HIGH
    assert assessment.seller_compat.label == DimensionLabel.UNKNOWN
    assert len(assessment.unknowns) >= 1
    assert "wholesale" in assessment.unknowns[0].lower()


@pytest.mark.asyncio
async def test_draft_outreach_strictly_grounded():
    """Verify Task D produces grounded pitch citing catalog facts without exposing technical IDs."""
    primary = NebiusClient(api_key="primary-key", model_id="ultra-550b")
    fast = NebiusClient(api_key="fast-key", model_id="super-120b")

    lead_id = uuid4()
    product_id = uuid4()
    ev_id = uuid4()

    lead = Lead(
        id=lead_id,
        run_id=uuid4(),
        product_id=product_id,
        name="Nordic Living Stockholm",
        website="https://nordicliving.se",
        canonical_domain="nordicliving.se",
    )
    product = Product(
        id=product_id,
        owner_id=uuid4(),
        name="Artisan Table Linens",
        category="Home Textiles",
        description="Handcrafted block printed napkins and table runners",
        materials=["pure linen"],
        motifs=["botanical"],
        price_segment=PriceSegment.MID_PREMIUM,
        moq=12,
    )
    evidence = [
        EvidenceItem(
            id=ev_id,
            lead_id=lead_id,
            url="https://nordicliving.se/brands",
            excerpt="Stockists of European handcrafted linens and home accessories.",
        )
    ]

    outreach_payload = {
        "subject": "Wholesale Inquiry: Handcrafted Linen Collection for Nordic Living Stockholm",
        "body": (
            "Dear Nordic Living Stockholm Team,\n\n"
            "I noticed that your boutique stocks curated European handcrafted linens. "
            "Our workshop specializes in Artisan Table Linens crafted with pure linen and botanical motifs. "
            "We offer a mid-premium wholesale program with a minimum order of 12 sets.\n\n"
            "Would you be open to reviewing our digital line sheet?\n\nWarm regards,\nAtelier Director"
        ),
        "facts_used": [
            {"fact_id": "fact-1", "text": "Workshop specializes in Artisan Table Linens with pure linen"},
            {"fact_id": f"evidence-{ev_id}", "text": "Stockists of European handcrafted linens"},
        ],
        "warnings": [],
    }
    primary.complete_json = AsyncMock(return_value=(json.dumps(outreach_payload), 300, 120))

    service = LiveAIService(client=primary, fast_client=fast)
    draft = await service.draft_outreach(product, lead, evidence)

    assert isinstance(draft, OutreachDraft)
    assert draft.status == OutreachDraftStatus.DRAFT
    assert "Nordic Living Stockholm" in draft.subject
    # Verify no raw internal technical ID leaks into the readable body text
    assert f"evidence-{ev_id}" not in draft.body
    assert "fact-1" not in draft.body
    assert len(draft.facts_used) >= 2


# -----------------------------------------------------------------------------
# 4. Factory Resolution & Fallback Configuration Tests
# -----------------------------------------------------------------------------

def test_get_ai_service_with_token_factory_key(monkeypatch):
    """Verify get_ai_service targets Token Factory with NVIDIA NIM fallback when Token Factory key is set."""
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.setenv("NEBIUS_TOKEN_FACTORY_API_KEY", "token-factory-secret-key-12345")
    monkeypatch.setenv("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1")
    monkeypatch.setenv("NEBIUS_API_KEY", "nvapi-ultra-fallback")
    monkeypatch.setenv("NEMOTRON_FAST_API_KEY", "nvapi-fast-fallback")

    try:
        from backend.app.core.config import get_settings
        get_settings.cache_clear()
    except Exception:
        pass

    service = get_ai_service()
    assert isinstance(service, LiveAIService)
    assert service.client.base_url == "https://api.tokenfactory.nebius.com/v1"
    assert service.client.api_key == "token-factory-secret-key-12345"
    assert service.client.fallback_base_url == "https://integrate.api.nvidia.com/v1"
    assert service.client.fallback_api_key == "nvapi-ultra-fallback"

    assert service.fast_client.base_url == "https://api.tokenfactory.nebius.com/v1"
    assert service.fast_client.fallback_base_url == "https://integrate.api.nvidia.com/v1"
    assert service.fast_client.fallback_api_key == "nvapi-fast-fallback"


def test_get_ai_service_fallback_to_nvidia_nim_when_token_factory_not_found(monkeypatch):
    """
    Verify requirement:
    'if api key not found then fallback to calling ultra and super through
    integrate.api.nvidia.com/v1 and their respective keys, got it? and obviously if
    token factory not there, then we can run as same as before this token factory'
    """
    monkeypatch.delenv("APP_ENV", raising=False)
    # Token Factory key is NOT found / absent / empty:
    monkeypatch.setenv("NEBIUS_TOKEN_FACTORY_API_KEY", "")
    # Respective NVIDIA keys are provided:
    monkeypatch.setenv("NEBIUS_API_KEY", "nvapi-ultra-original-key")
    monkeypatch.setenv("NEMOTRON_FAST_API_KEY", "nvapi-super-original-key")

    try:
        from backend.app.core.config import get_settings
        get_settings.cache_clear()
    except Exception:
        pass

    service = get_ai_service()
    assert isinstance(service, LiveAIService)

    # Primary client targets NVIDIA NIM directly with Ultra key
    assert service.client.base_url == "https://integrate.api.nvidia.com/v1"
    assert service.client.api_key == "nvapi-ultra-original-key"
    assert service.client.model_id == "nvidia/nemotron-3-ultra-550b-a55b"

    # Fast client targets NVIDIA NIM directly with Super key
    assert service.fast_client.base_url == "https://integrate.api.nvidia.com/v1"
    assert service.fast_client.api_key == "nvapi-super-original-key"
    assert service.fast_client.model_id == "nvidia/nemotron-3.5-super-vl-120b-a12b"


def test_get_ai_service_fallback_to_fixture_when_unconfigured(monkeypatch):
    """Verify get_ai_service returns FixtureAIService when no keys whatsoever are provided."""
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.setenv("NEBIUS_API_KEY", "")
    monkeypatch.setenv("NEBIUS_TOKEN_FACTORY_API_KEY", "")
    monkeypatch.setenv("NEMOTRON_FAST_API_KEY", "")

    try:
        from backend.app.core.config import get_settings
        get_settings.cache_clear()
    except Exception:
        pass

    service = get_ai_service()
    assert isinstance(service, FixtureAIService)
