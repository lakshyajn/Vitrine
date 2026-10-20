"""
Canonical Domain Normalization & Company Identity Deduplication.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from contracts.schemas import LeadCandidate

MARKETPLACE_DOMAINS = {"etsy.com", "faire.com", "ankorstore.com"}
MULTI_PART_TLDS = {
    "co.uk", "org.uk", "ac.uk", "com.au", "co.nz", "co.jp", "co.in", "com.br", "com.sg"
}
LEGAL_SUFFIX_PATTERN = re.compile(
    r"\b(ltd|limited|llc|inc|incorporated|gmbh|sarl|bv|pvt|co|company|boutique|shop|store|studio|living|home)\b",
    re.IGNORECASE,
)


def extract_canonical_domain(raw_url: str) -> str:
    u = str(raw_url or "").strip().lower()
    if not u:
        return ""
    if not u.startswith(("http://", "https://")):
        u = f"https://{u}"
    
    try:
        parsed = urlparse(u)
        host = str(parsed.hostname or "")
    except Exception:
        host = u.split("/")[2] if "//" in u else u

    # Foolproof www. stripping (compatible with all Python versions)
    if host.startswith("www."):
        host = host[4:]
        
    if not host:
        return ""

    parts = host.split(".")
    if len(parts) >= 3 and ".".join(parts[-2:]) in MULTI_PART_TLDS:
        registrable = ".".join(parts[-3:])
    elif len(parts) >= 2:
        registrable = ".".join(parts[-2:])
    else:
        registrable = host

    if registrable in MARKETPLACE_DOMAINS:
        try:
            path_str = getattr(parsed, "path", "")
            segments = [seg for seg in path_str.strip("/").split("/") if seg]
            if len(segments) >= 2 and segments[0] in ("shop", "store", "brand", "b"):
                return f"{registrable}/{segments[0]}/{segments[1]}"
            if segments:
                return f"{registrable}/{segments[0]}"
        except Exception:
            pass

    return registrable


def normalize_business_name(name: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", (name or "").lower())
    cleaned = LEGAL_SUFFIX_PATTERN.sub(" ", cleaned)
    return " ".join(cleaned.split())


def _token_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    set_a = set(a.split())
    set_b = set(b.split())
    if not set_a or not set_b:
        return 0.0
    return (2.0 * len(set_a & set_b)) / (len(set_a) + len(set_b))


def deduplicate_lead_candidates(candidates: list[LeadCandidate]) -> list[LeadCandidate]:
    by_domain: dict[str, LeadCandidate] = {}

    for cand in candidates:
        dom = extract_canonical_domain(cand.website) or cand.canonical_domain.lower()
        cand.canonical_domain = dom
        for ev in cand.evidence:
            ev.domain_matches_lead = extract_canonical_domain(ev.url) == dom

        if dom in by_domain:
            primary = by_domain[dom]
            existing_sigs = {(e.url.rstrip("/"), e.excerpt[:100]) for e in primary.evidence}
            for ev in cand.evidence:
                sig = (ev.url.rstrip("/"), ev.excerpt[:100])
                if sig not in existing_sigs:
                    primary.evidence.append(ev)
                    existing_sigs.add(sig)
            primary.website_verified = primary.website_verified or cand.website_verified
            if primary.location is None and cand.location is not None:
                primary.location = cand.location
        else:
            by_domain[dom] = cand

    merged_list = list(by_domain.values())

    for idx, current in enumerate(merged_list):
        norm_curr = normalize_business_name(current.name)
        city_curr = (current.location.city or "").strip().lower() if current.location else ""
        if not norm_curr or not city_curr:
            continue
        for prior in merged_list[:idx]:
            norm_prior = normalize_business_name(prior.name)
            city_prior = (prior.location.city or "").strip().lower() if prior.location else ""
            if city_curr == city_prior and _token_similarity(norm_curr, norm_prior) >= 0.85:
                current.possible_duplicate_of_domain = prior.canonical_domain
                break

    return merged_list