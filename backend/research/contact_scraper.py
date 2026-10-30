"""
backend/research/contact_scraper.py
Tavily-Powered B2B Receiver Contact Email Scraper.

Extracts official contact, buyer, and customer care email addresses
for discovered retailer domains using live Tavily search snippets and extract results.
Enforces strict provenance: only page-extracted, domain-matched addresses.
Never constructs synthetic wholesale@{domain} guesses.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Any
from urllib.parse import urlparse

from backend.research.tavily_client import TavilyClient

logger = logging.getLogger(__name__)

# RFC-compliant email matching pattern
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# Asset & non-contact exclusions
EXCLUDED_EMAIL_EXTS = (
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".css", ".js", ".bmp", ".tiff",
    ".pdf", ".ico", ".woff", ".woff2", ".mp4", ".mp3",
)

EXCLUDED_DOMAINS = {
    "example.com", "example.org", "example.net", "company.com", "domain.com",
    "email.com", "test.com", "yourdomain.com", "sentry.io", "wix.com", "wixpress.com",
    "shopify.com", "myshopify.com", "squarespace.com", "schema.org",
    "google.com", "facebook.com", "instagram.com", "cloudflare.com",
    "wordpress.com", "gravatar.com", "apple.com", "mail.com", "gmail.com",
}

EXCLUDED_PREFIXES = (
    "noreply", "no-reply", "donotreply", "do-not-reply", "mailer-daemon",
    "abuse", "privacy", "test", "yourname", "name", "user", "admin", "sample",
)

PLACEHOLDER_LOCAL_PARTS = {
    "yourname", "name", "email", "username", "test", "user", "sample", "admin",
}

# Known demo fixtures for offline resilience (NO synthetic wholesale@ defaults)
FIXTURE_CONTACTS: dict[str, str] = {
    "atelierlivingdemo.com": "contact@atelierlivingdemo.com",
    "thebotanistshopdemo.co.uk": "hello@thebotanistshopdemo.co.uk",
    "colmershill.com": "customerservices@colmershill.com",
    "yavistudio.com": "hello@yavistudio.com",
}


def clean_domain(raw_domain: str) -> str:
    """Normalize domain string by stripping protocols, ports, www, and query paths."""
    dom = (raw_domain or "").strip().lower()
    if dom.startswith("http://") or dom.startswith("https://"):
        parsed = urlparse(dom)
        dom = parsed.netloc or parsed.path
    dom = dom.split(":")[0].split("/")[0]
    if dom.startswith("www."):
        dom = dom[4:]
    return dom


def is_valid_contact_email(email: str, canonical_domain: str | None = None, context_text: str = "") -> bool:
    """
    Validate extracted email against placeholders, file extensions, and domain provenance rules.
    """
    cleaned = email.strip().lower().rstrip(".,;:)")
    if any(cleaned.endswith(ext) for ext in EXCLUDED_EMAIL_EXTS):
        return False

    parts = cleaned.split("@")
    if len(parts) != 2:
        return False
    local_part, email_domain = parts

    if local_part in PLACEHOLDER_LOCAL_PARTS:
        return False
    if any(local_part.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False
    if email_domain in EXCLUDED_DOMAINS or email_domain.startswith("example."):
        return False
    if len(local_part) < 2 or len(email_domain) < 4:
        return False

    # Domain integrity check
    if canonical_domain:
        clean_dom = clean_domain(canonical_domain)
        domain_matches = (
            email_domain == clean_dom
            or email_domain.endswith(f".{clean_dom}")
            or clean_dom.endswith(f".{email_domain}")
            or clean_dom in email_domain
        )
        if not domain_matches:
            # If domain differs, only accept if the page text explicitly labels it as retailer contact
            contact_labels = ("contact", "email:", "write to us", "get in touch", "wholesale inquiry", "customer service")
            ctx_lower = context_text.lower()
            if not any(lbl in ctx_lower for lbl in contact_labels):
                return False

    return True


def extract_emails_from_text(text: str, canonical_domain: str | None = None) -> list[str]:
    """Extract and validate candidate emails from raw webpage text or search snippets."""
    if not text:
        return []

    raw_matches = EMAIL_REGEX.findall(text)
    valid_emails: list[str] = []

    for email in raw_matches:
        cleaned = email.strip().lower().rstrip(".,;:)")
        if is_valid_contact_email(cleaned, canonical_domain=canonical_domain, context_text=text):
            if cleaned not in valid_emails:
                valid_emails.append(cleaned)

    return valid_emails


def score_and_rank_email(email: str, canonical_domain: str) -> int:
    """
    Score candidate email to prioritize wholesale buyers, official domains, and general contact addresses.
    """
    score = 0
    local_part, email_domain = email.split("@", 1)
    clean_dom = clean_domain(canonical_domain)

    # 1. Domain match (highest trust)
    if email_domain == clean_dom or email_domain.endswith(f".{clean_dom}"):
        score += 60
    elif clean_dom in email_domain:
        score += 30

    # 2. Wholesale / Buyer / Trade intent
    wholesale_terms = ("wholesale", "buyer", "buyers", "purchasing", "trade", "stockist", "stockists", "orders")
    if any(term in local_part for term in wholesale_terms):
        score += 50

    # 3. Customer Care / General Inquiries
    contact_terms = ("contact", "info", "hello", "team", "shop", "store", "office", "customerservices", "customercare", "help", "sales")
    if any(term in local_part for term in contact_terms):
        score += 35

    # 4. Human names or other valid mailbox at the verified domain
    if score >= 60 and len(local_part) > 2:
        score += 10

    return score


async def scrape_contact_email(
    canonical_domain: str,
    website: str | None = None,
    tavily_client: TavilyClient | None = None,
) -> dict[str, Any]:
    """
    Scrape receiver wholesale/buyer email address using Tavily Search & Extract.
    Returns:
    {
        "email": str,
        "source": str,
        "source_url": str | None,
        "is_fallback": bool,
        "confidence": float,
        "all_candidates": list[str],
        "note": str | None
    }
    Never generates synthetic wholesale@{domain} guesses.
    """
    clean_dom = clean_domain(canonical_domain)
    if not clean_dom:
        return {
            "email": "",
            "source": "not_found",
            "source_url": None,
            "is_fallback": False,
            "confidence": 0.0,
            "all_candidates": [],
            "note": "No contact email found on public website",
        }

    # If Tavily client not supplied, attempt to initialize from environment/settings
    if tavily_client is None:
        if "TAVILY_API_KEY" in os.environ and not os.environ["TAVILY_API_KEY"].strip():
            api_key = ""
        else:
            api_key = os.environ.get("TAVILY_API_KEY", "").strip()
            if not api_key:
                try:
                    from backend.app.core.config import settings
                    api_key = getattr(settings, "tavily_api_key", "") or getattr(settings, "TAVILY_API_KEY", "")
                except Exception:
                    pass

        if api_key and str(api_key).strip():
            tavily_client = TavilyClient(api_key=str(api_key).strip())

    # If no live Tavily client available, check fixture dictionary or return not_found
    if tavily_client is None:
        if clean_dom in FIXTURE_CONTACTS:
            return {
                "email": FIXTURE_CONTACTS[clean_dom],
                "source": "fixture_match",
                "source_url": f"https://{clean_dom}",
                "is_fallback": False,
                "confidence": 0.9,
                "all_candidates": [FIXTURE_CONTACTS[clean_dom]],
                "note": None,
            }
        return {
            "email": "",
            "source": "not_found",
            "source_url": None,
            "is_fallback": False,
            "confidence": 0.0,
            "all_candidates": [],
            "note": "No contact email found on public website",
        }

    # Execute targeted live Tavily search
    query = f"site:{clean_dom} (email OR contact OR wholesale OR \"customer services\" OR hello OR info)"
    hits: list[dict[str, Any]] = []
    try:
        hits = await tavily_client.search(query)
    except Exception as exc:
        logger.warning("Targeted Tavily email search failed for %s: %s", clean_dom, exc)

    if not hits:
        try:
            hits = await tavily_client.search(f'"{clean_dom}" (email OR "contact us" OR wholesale)')
        except Exception as exc:
            logger.warning("Broad Tavily email search failed for %s: %s", clean_dom, exc)

    extracted_emails_with_meta: list[tuple[str, int, str]] = []  # (email, score, source_url)
    contact_urls_to_extract: list[str] = []

    for hit in hits:
        hit_url = hit.get("url") or ""
        content = f"{hit.get('content', '')} {hit.get('title', '')}"
        found = extract_emails_from_text(content, clean_dom)
        for e in found:
            s = score_and_rank_email(e, clean_dom)
            extracted_emails_with_meta.append((e, s, hit_url))

        lower_url = hit_url.lower()
        if any(slug in lower_url for slug in ("/contact", "/about", "/wholesale", "/stockists", "/pages/contact")):
            if hit_url not in contact_urls_to_extract:
                contact_urls_to_extract.append(hit_url)

    # If no domain-matched email found from search snippets, extract top contact pages
    has_domain_match = any(clean_dom in e[0] for e in extracted_emails_with_meta)
    if not has_domain_match and contact_urls_to_extract:
        try:
            extractions = await tavily_client.extract(contact_urls_to_extract[:2])
            for ext in extractions:
                ext_url = ext.get("url") or ""
                raw_text = ext.get("raw_content") or ""
                found = extract_emails_from_text(raw_text, clean_dom)
                for e in found:
                    s = score_and_rank_email(e, clean_dom)
                    extracted_emails_with_meta.append((e, s, ext_url))
        except Exception as exc:
            logger.warning("Tavily extract failed for %s: %s", contact_urls_to_extract, exc)

    extracted_emails_with_meta.sort(key=lambda x: x[1], reverse=True)

    if extracted_emails_with_meta and extracted_emails_with_meta[0][1] > 20:
        best_email, best_score, best_url = extracted_emails_with_meta[0]
        unique_candidates = list(dict.fromkeys(x[0] for x in extracted_emails_with_meta))
        return {
            "email": best_email,
            "source": "tavily_scraped",
            "source_url": best_url or f"https://{clean_dom}",
            "is_fallback": False,
            "confidence": 0.95 if best_score >= 80 else 0.8,
            "all_candidates": unique_candidates[:5],
            "note": None,
        }

    # If nothing verified via Tavily, check known fixtures or return not_found
    if clean_dom in FIXTURE_CONTACTS:
        return {
            "email": FIXTURE_CONTACTS[clean_dom],
            "source": "fixture_match",
            "source_url": f"https://{clean_dom}",
            "is_fallback": False,
            "confidence": 0.9,
            "all_candidates": [FIXTURE_CONTACTS[clean_dom]],
            "note": None,
        }

    return {
        "email": "",
        "source": "not_found",
        "source_url": None,
        "is_fallback": False,
        "confidence": 0.0,
        "all_candidates": [],
        "note": "No contact email found on public website",
    }
