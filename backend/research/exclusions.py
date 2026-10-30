# backend/research/exclusions.py
"""
Data-driven Domain and URL Exclusions Engine (WS3 Milestone C).
Filters out social media, reference/wikis, travel aggregators, government/education,
museums/institutions, mass marketplaces, and job/classified sites with explicit match reasons.
Supports settings override.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse
from backend.research.dedupe import extract_canonical_domain

# 1. Social networks and discussion forums
EXCLUDED_SOCIAL_FORUMS = {
    "reddit.com", "quora.com", "facebook.com", "instagram.com", "twitter.com",
    "x.com", "youtube.com", "pinterest.com", "linkedin.com", "tiktok.com",
    "threads.net", "tumblr.com", "discord.com", "t.me", "telegram.org",
    "snapchat.com", "flickr.com", "vimeo.com", "whatsapp.com",
}

# 2. Reference, encyclopedias, wikis, blogging platforms, news/media
EXCLUDED_REFERENCE_NEWS = {
    "wikipedia.org", "wikimedia.org", "fandom.com", "wikihow.com", "wiktionary.org",
    "medium.com", "substack.com", "blogger.com", "wordpress.com", "nytimes.com",
    "theguardian.com", "bbc.com", "bbc.co.uk", "cnn.com", "forbes.com", "reuters.com",
    "bloomberg.com", "wsj.com", "huffpost.com", "buzzfeed.com", "dezeen.com",
    "elledecor.com", "architecturaldigest.com", "vogue.com", "houseandgarden.co.uk",
}

# 3. Travel, review, and directory aggregators
EXCLUDED_TRAVEL_AGGREGATORS = {
    "tripadvisor.com", "tripadvisor.co.uk", "tripadvisor.in", "yelp.com", "yelp.co.uk",
    "yellowpages.com", "yellowpages.ca", "evendo.com", "mapquest.com", "foursquare.com",
    "trustpilot.com", "bbb.org", "timeout.com", "lonelyplanet.com", "theculturetrip.com",
    "visitlondon.com", "visitbritain.com", "expedia.com", "booking.com", "airbnb.com",
    "crunchbase.com", "dnb.com", "zoominfo.com", "rocketreach.co", "apollo.io",
}

# 4. Mass online marketplaces and wholesale directory portals
EXCLUDED_MARKETPLACES_CHAINS = {
    "amazon.com", "amazon.co.uk", "amazon.de", "amazon.in", "amazon.fr", "amazon.it", "amazon.es",
    "alibaba.com", "aliexpress.com", "indiamart.com", "tradeindia.com", "walmart.com",
    "target.com", "ikea.com", "wayfair.com", "wayfair.co.uk", "temu.com", "ebay.com",
    "ebay.co.uk", "etsy.com", "faire.com", "ankorstore.com", "costco.com", "tesco.com",
    "argos.co.uk", "marksandspencer.com", "johnlewis.com",
}

# 5. Job boards and classified sites
EXCLUDED_JOB_CLASSIFIEDS = {
    "indeed.com", "glassdoor.com", "craigslist.org", "gumtree.com", "monster.com",
    "ziprecruiter.com", "linkedin.com/jobs", "upwork.com", "fiverr.com",
}

# 6. Government and education TLD regex patterns
GOV_EDU_PATTERN = re.compile(
    r"(?:(?:\.|\b)(?:gov|edu|mil|ac)\.[a-z]{2,3}$)|(?:(?:\.|\b)(?:gov|edu|mil)$)",
    re.IGNORECASE,
)

# 7. Institutional / Museum domain keyword regex
INSTITUTION_KEYWORD_PATTERN = re.compile(
    r"(?:museum|nationalmuseum|artgallery|library|historical|archives|archive|parliament|embassy)",
    re.IGNORECASE,
)


def is_domain_excluded_detailed(url_or_domain: str) -> tuple[bool, str | None]:
    """
    Checks if a domain or URL is excluded with a specific data-driven reason.
    Returns (is_excluded, reason_str).
    """
    if not url_or_domain or not str(url_or_domain).strip():
        return False, None

    raw = str(url_or_domain).strip().lower()
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    full_host = (parsed.netloc or parsed.path).split(":")[0].lower()
    if full_host.startswith("www."):
        full_host = full_host[4:]

    dom = extract_canonical_domain(raw)
    if not dom:
        dom = full_host
    if dom.startswith("www."):
        dom = dom[4:]

    # Check settings override if configured
    try:
        from backend.app.core.config import get_settings
        settings = get_settings()
        override_set = getattr(settings, "excluded_domains_override", None)
        if override_set and dom in override_set:
            return True, f"Domain excluded by settings configuration override: {dom}"
    except Exception:
        pass

    # 1. Social & forums
    for s_dom in EXCLUDED_SOCIAL_FORUMS:
        if dom == s_dom or dom.endswith(f".{s_dom}"):
            return True, f"Excluded social platform or forum domain: {dom}"

    # 2. Reference, fandom, news
    for r_dom in EXCLUDED_REFERENCE_NEWS:
        if dom == r_dom or dom.endswith(f".{r_dom}"):
            return True, f"Excluded reference, wiki, or news publication domain: {dom}"

    # 3. Travel & listing aggregators
    for t_dom in EXCLUDED_TRAVEL_AGGREGATORS:
        if dom == t_dom or dom.endswith(f".{t_dom}"):
            return True, f"Excluded aggregator, directory, or travel guide: {dom}"

    # 4. Marketplaces & chains
    for m_dom in EXCLUDED_MARKETPLACES_CHAINS:
        if dom == m_dom or dom.endswith(f".{m_dom}"):
            return True, f"Excluded mass marketplace or retail chain: {dom}"

    # 5. Job & classifieds
    for j_dom in EXCLUDED_JOB_CLASSIFIEDS:
        if dom == j_dom or dom.endswith(f".{j_dom}"):
            return True, f"Excluded classifieds or employment listing domain: {dom}"

    # 6. Government & Educational institutions (.gov, .gov.*, .edu, .ac.*, .mil)
    if GOV_EDU_PATTERN.search(dom) or GOV_EDU_PATTERN.search(full_host):
        return True, f"Excluded government or academic institution domain: {dom or full_host}"

    # 7. Institutional / Museum domain keywords
    if INSTITUTION_KEYWORD_PATTERN.search(dom) or INSTITUTION_KEYWORD_PATTERN.search(full_host):
        return True, f"Excluded non-retail institution, museum, or cultural archive: {dom or full_host}"

    return False, None


def is_excluded_retailer_domain(url_or_domain: str) -> tuple[bool, str | None]:
    """Compatibility alias for is_domain_excluded_detailed."""
    return is_domain_excluded_detailed(url_or_domain)


def is_domain_excluded(url_or_domain: str) -> bool:
    """Convenience boolean check for domain exclusion."""
    return is_domain_excluded_detailed(url_or_domain)[0]
