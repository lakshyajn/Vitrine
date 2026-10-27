"""
Validation, Claim Verification & Single-Repair Retry Pipeline (WS3 Section 3.2 & 3.3).
Raises WS2's AppError(ErrorCode.AI_OUTPUT_INVALID) when validation or claim checks fail.
"""

from __future__ import annotations

import json
import re
from typing import Any, Awaitable, Callable, TypeVar
from uuid import UUID

from pydantic import BaseModel, ValidationError

from backend.app.core.errors import AppError
from contracts.schemas import (
    DimensionLabel,
    ErrorCode,
    EvidenceItem,
    LeadAssessment,
    ResearchPlan,
)

T = TypeVar("T", bound=BaseModel)

URL_PATTERN = re.compile(r"https?://[^\s)>\]]+", re.IGNORECASE)
NUMBER_PATTERN = re.compile(r"\b\d+(?:[.,]\d+)?\b")
FORBIDDEN_PLAN_CLAIMS = (
    "qloo returned",
    "qloo confirmed",
    "qloo verified",
    "according to qloo results",
)


def raise_ai_output_invalid(message: str, details: dict[str, Any] | None = None) -> None:
    raise AppError(
        code=ErrorCode.AI_OUTPUT_INVALID,
        message=message,
        status_code=502,
        details=details,
    )


def parse_json_object(raw_text: str) -> dict[str, Any]:
    if not raw_text or not raw_text.strip():
        raise_ai_output_invalid("Model returned empty response.")
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise_ai_output_invalid(f"Model returned invalid JSON: {exc}")
    if not isinstance(parsed, dict):
        raise_ai_output_invalid("Model JSON output must be a JSON object.")
    return parsed


def validate_research_plan_claims(plan: ResearchPlan) -> None:
    """Task B post-check: Plan must only contain proposals, never fake provider results."""
    combined = " ".join(
        [
            *(plan.aesthetic_candidates or []),
            *(plan.search_queries or []),
            plan.hypotheses_rationale or "",
            plan.notes or "",
        ]
    ).lower()
    for phrase in FORBIDDEN_PLAN_CLAIMS:
        if phrase in combined:
            raise_ai_output_invalid(
                f"ResearchPlan contains unsupported claim that a provider already returned data: '{phrase}'"
            )


def validate_lead_assessment_claims(
    assessment: LeadAssessment, evidence: list[EvidenceItem]
) -> None:
    """
    Task C post-checks (WS3 Section 3.3):
    1. Every high/medium/low label must cite >= 1 valid evidence_id from input evidence.
    2. Every cited evidence_id must exist in input evidence.
    3. No uncited URLs in summary or reasons.
    4. Summary length <= 600 chars.
    """
    valid_ids: set[UUID] = {item.id for item in evidence if item.id is not None}
    valid_urls: set[str] = {item.url.lower().rstrip("/") for item in evidence}

    if not assessment.summary or len(assessment.summary.strip()) > 600:
        raise_ai_output_invalid("LeadAssessment summary is empty or exceeds 600 characters.")

    for dim_name in ("category_fit", "aesthetic_fit", "seller_compat"):
        dim = getattr(assessment, dim_name)
        label_str = str(dim.label)

        if label_str in (
            DimensionLabel.HIGH.value,
            DimensionLabel.MEDIUM.value,
            DimensionLabel.LOW.value,
        ):
            if not dim.reasons:
                raise_ai_output_invalid(
                    f"Dimension '{dim_name}' is labeled '{label_str}' but has no reasons.",
                    {"dimension": dim_name},
                )
            if not dim.evidence_ids:
                raise_ai_output_invalid(
                    f"Dimension '{dim_name}' is labeled '{label_str}' but cites zero evidence_ids.",
                    {"dimension": dim_name},
                )

        for eid in dim.evidence_ids:
            if eid not in valid_ids:
                raise_ai_output_invalid(
                    f"Dimension '{dim_name}' cites non-existent evidence_id '{eid}'.",
                    {"dimension": dim_name, "invalid_evidence_id": str(eid)},
                )

    all_text = " ".join(
        [
            assessment.summary,
            *assessment.category_fit.reasons,
            *assessment.aesthetic_fit.reasons,
            *assessment.seller_compat.reasons,
        ]
    )
    for url in URL_PATTERN.findall(all_text):
        normalized = url.lower().rstrip(".,;/)")
        if normalized not in valid_urls:
            raise_ai_output_invalid(
                f"LeadAssessment contains URL not present in input evidence: {url}",
                {"unverified_url": url},
            )


def validate_and_ground_outreach_draft(
    raw_data: dict[str, Any],
    fact_catalog: dict[str, dict[str, str | None]],
) -> dict[str, Any]:
    """
    Task D post-checks (WS3 Section 3.3):
    1. Subject and body must be present and within length limits.
    2. Every fact_id in facts_used must exist in fact_catalog.
    3. Body cannot contain URLs outside fact_catalog.
    4. Any numbers in body not present in fact_catalog are flagged in warnings[].
    """
    subject = str(raw_data.get("subject") or "").strip()
    body = str(raw_data.get("body") or "").strip()

    # Deterministically strip any accidental LLM inline citation artifacts (e.g. (evidence-uuid), (fact-1))
    body = re.sub(r"\s*[\(\[](?:evidence-[a-f0-9\-]+|fact-\d+)[\)\]]", "", body).strip()
    subject = re.sub(r"\s*[\(\[](?:evidence-[a-f0-9\-]+|fact-\d+)[\)\]]", "", subject).strip()

    if not subject or len(subject) > 200:
        raise_ai_output_invalid("OutreachDraft subject is missing or exceeds 200 characters.")
    if not body or len(body) > 3000:
        raise_ai_output_invalid("OutreachDraft body is missing or exceeds 3000 characters.")

    facts_used_raw = raw_data.get("facts_used")
    if not isinstance(facts_used_raw, list) or len(facts_used_raw) == 0:
        raise_ai_output_invalid("OutreachDraft must cite at least one fact in facts_used.")

    grounded_facts: list[dict[str, str | None]] = []
    for item in facts_used_raw:
        if not isinstance(item, dict):
            raise_ai_output_invalid("Each entry in facts_used must be an object.")
        fid = str(item.get("fact_id") or "")
        if fid not in fact_catalog:
            raise_ai_output_invalid(
                f"OutreachDraft cites unknown fact_id '{fid}' not in supplied fact catalog.",
                {"invalid_fact_id": fid},
            )
        grounded_facts.append(
            {
                "fact_id": fid,
                "text": str(fact_catalog[fid]["text"]),
                "source_url": fact_catalog[fid]["source_url"],
            }
        )

    allowed_urls = {
        str(v["source_url"]).lower().rstrip("/")
        for v in fact_catalog.values()
        if v.get("source_url")
    }
    for url in URL_PATTERN.findall(body):
        norm_url = url.lower().rstrip(".,;/)")
        if norm_url not in allowed_urls:
            raise_ai_output_invalid(
                f"OutreachDraft body contains unauthorized URL outside fact list: {url}",
                {"unauthorized_url": url},
            )

    catalog_blob = " ".join(str(v["text"]) for v in fact_catalog.values())
    allowed_numbers = set(NUMBER_PATTERN.findall(catalog_blob))
    warnings: list[str] = [str(w) for w in (raw_data.get("warnings") or [])]

    for num in NUMBER_PATTERN.findall(body):
        if num not in allowed_numbers:
            warning_msg = f"Numeric claim '{num}' in draft body is not in the approved fact catalog; verify before sending."
            if warning_msg not in warnings:
                warnings.append(warning_msg)

    raw_data["subject"] = subject
    raw_data["body"] = body
    raw_data["facts_used"] = grounded_facts
    raw_data["warnings"] = warnings
    return raw_data


async def execute_with_single_repair(
    llm_call: Callable[[list[dict[str, str]]], Awaitable[tuple[str, int | None, int | None]]],
    messages: list[dict[str, str]],
    parse_and_validate: Callable[[dict[str, Any]], T],
) -> tuple[T, int | None, int | None]:
    """
    Runs: parse JSON -> validate schema & claim checks -> on failure, 1 repair retry
    sending validation errors back -> if still invalid, raises ai_output_invalid.
    """
    chat_messages = [dict(m) for m in messages]
    tokens_in_total = 0
    tokens_out_total = 0
    last_error = "Unknown validation error"

    for attempt in range(2):  # 0 = initial call, 1 = single repair retry
        raw_text, t_in, t_out = await llm_call(chat_messages)
        if t_in:
            tokens_in_total += t_in
        if t_out:
            tokens_out_total += t_out

        try:
            payload = parse_json_object(raw_text)
            validated = parse_and_validate(payload)
            return validated, (tokens_in_total or None), (tokens_out_total or None)
        except ValidationError as vex:
            last_error = f"Pydantic validation failed: {vex}"
        except AppError as aex:
            if aex.code != ErrorCode.AI_OUTPUT_INVALID:
                raise
            last_error = aex.message

        if attempt == 0:
            chat_messages.append({"role": "assistant", "content": raw_text or "{}"})
            chat_messages.append(
                {
                    "role": "user",
                    "content": (
                        f"Your previous response failed validation with error:\n{last_error}\n"
                        "Please fix the error and return ONLY the valid JSON object."
                    ),
                }
            )
        else:
            raise_ai_output_invalid(f"Model output failed validation after repair retry: {last_error}")

    raise_ai_output_invalid(last_error)
    raise AssertionError("Unreachable")