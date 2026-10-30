# Qloo Cultural Taste & Affinity Integration Findings (`docs/qloo-findings.md`)

## 1. Current Live Status
- **Status:** **Not yet run against live API** (offline fixture and mock mode active; live API key not configured or awaiting live key authorization).
- **Environment:** Mock provider active (`is_demo = True`), caching in SQLite/PostgreSQL `provider_calls` enabled with TTL.

---

## 2. Taste Hygiene & Contract Calibration

### 2.1 Category Fallback Removal
- **Change:** Removed the hardcoded `"Home Decor & Living"` fallback in both `MockTasteProvider` and `QlooTasteProvider`.
- **Truth Rule:** Missing categories now strictly remain `None`. Commodity and non-decor products (e.g., stationery, pencils, hardware) never receive synthetic home decor categories.

### 2.2 Taxonomy Filter Alignment
- **Constant:** `QLOO_DEFAULT_INSIGHTS_FILTER_TYPE = "urn:entity:brand"`.
- **Rationale:** Qloo's V2 insights endpoint requires an entity type URN. The primary target for B2B retailer aesthetic alignment is brand entities (`urn:entity:brand`).
- **Future Extension:** Can be broadened to `urn:entity:place` for geographic / brick-and-mortar venue insights when regional foot-traffic or local store density analysis is enabled.

### 2.3 Strict Lead Matching Rules (`does_signal_match_lead`)
- **Location Requirement:** Signal matching requires a verified retailer location (`city`, `region`, or `country`) matching the signal text or an explicit anchor-to-region linkage.
- **Leakage Prevention:** Removed loose 4-letter category token matching that previously caused unrelated hypotheses to attach to retailer leads.
- **Tier & Relevance Gate:** Cultural affinity signals are NEVER attached to `unqualified` leads or leads where `category_fit` is unknown (`null`). If a lead has no location, `cultural_affinity` strictly remains `None`.

### 2.4 Commodity & Zero-Anchor Bypass
- If `plan.taste_relevance == "not_applicable"`, Phase 1 and Phase 2 bypass Qloo calls entirely.
- Sellers can proceed without anchors (`proceed_without_anchors: true` or zero anchors on commodity products); Phase 2 completes discovery and scoring cleanly without failing or calling Qloo.

---

## 3. Live Qloo Experimentation Plan (Upon Key Authorization)

1. **Entity Search Precision:**
   - Execute queries across 4 distinct product categories: stationery/pencils, artisanal home textiles, ceramics, and leather goods.
   - Verify returned entity types, taxonomy tags, and latency.

2. **Affinity Vector Sanity:**
   - Query `/v2/insights` with confirmed brand IDs.
   - Assert affinity scores are bounded in `[0.0, 1.0]`, and check whether cross-category affinities are coherent.

3. **Quota & Rate-Limit Hardening:**
   - Validate 429 exponential backoff with jitter and per-run quota enforcement (default max 10 Qloo calls per run).
   - Ensure cache hits return in `< 5ms` with zero counter increment or network egress.
