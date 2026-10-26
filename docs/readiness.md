# WS2 Backend Readiness Report

## 1. Executive Summary

The Vitrine backend (WS2) is feature-complete, hardened, and verified against the Contract v0.2 specification and architectural decisions. All endpoints across Products, Research Runs, Taste Anchors, Leads, Lead Evidence, and Outreach Studio are implemented, tested, and passing.

Key hardening mechanisms delivered in Step 9:
- **Stuck-Run Recovery:** Runs interrupted or stalled during `running` state past `STAGE_TIMEOUT_SECONDS` (120s) are automatically detected and transitioned to `failed` upon startup, while runs in `awaiting_review` remain untouched.
- **Per-User Rate Limiting:** Sliding-window in-memory rate limiter on high-compute endpoints (`POST /api/v1/research-runs` and `POST /api/v1/leads/{id}/outreach-drafts`) returning HTTP 429 in the Appendix A.5 envelope.
- **Qloo Taste Orchestration:** Deterministic caching (24h TTL), quota caps (20 calls/run), exponential backoff retries on 429/timeouts, strict audit logging in `provider_calls`, failure isolation, and cultural affinity matching.
- **Fixed Demo Scenario Seeding:** Idempotent CLI script (`python -m backend.app.db.seed_demo`) populating the "Sample Seller" catalog with `is_demo: true` across all entities.

---

## 2. Endpoint Implementation Status

All endpoints conform strictly to Contract v0.2 wire types and return responses in standard envelopes.

| Category | Method | Path | Status | Verification |
| :--- | :--- | :--- | :--- | :--- |
| **System** | `GET` | `/health` | Completed | Liveness probe returning `{"status": "ok"}` |
| | `GET` | `/api/v1/integrations/status` | Completed | Reports live/mock state for AI, Search, Taste without leaking secrets |
| **Profile** | `GET` | `/api/v1/profile` | Completed | Returns seller profile for authenticated caller |
| | `PUT` | `/api/v1/profile` | Completed | Idempotent upsert of seller profile |
| **Products** | `GET` | `/api/v1/products` | Completed | Lists products owned by caller |
| | `POST` | `/api/v1/products` | Completed | Creates new product with price/MOQ validation |
| | `GET` | `/api/v1/products/{id}` | Completed | Fetches product by ID with tenant isolation |
| | `PATCH` | `/api/v1/products/{id}` | Completed | Partial updates to product attributes |
| | `DELETE` | `/api/v1/products/{id}` | Completed | Soft/hard delete with cascade cleanup |
| **Research Runs** | `POST` | `/api/v1/research-runs` | Completed | Queues Phase 1 run; rate-limited (10/min); Idempotency-Key support |
| | `GET` | `/api/v1/research-runs` | Completed | Lists research runs owned by caller |
| | `GET` | `/api/v1/research-runs/{id}` | Completed | Fetches run status, stage, plan, error metadata |
| | `POST` | `/api/v1/research-runs/{id}/rerun` | Completed | Spawns a new run copying previous run inputs |
| **Taste Anchors** | `GET` | `/api/v1/research-runs/{id}/anchors` | Completed | Lists proposed/confirmed anchors for run |
| | `POST` | `/api/v1/research-runs/{id}/anchors` | Completed | Adds user-defined anchor (`source="user_added"`) |
| | `PATCH` | `/api/v1/taste-anchors/{id}` | Completed | Confirms, rejects, or updates anchor rationale |
| | `POST` | `/api/v1/research-runs/{id}/confirm-anchors` | Completed | Finalizes anchor review, initiates Phase 2 (Discovery) |
| **Hypotheses** | `GET` | `/api/v1/research-runs/{id}/hypotheses` | Completed | Returns market hypotheses with attached taste signals |
| **Leads** | `GET` | `/api/v1/leads` | Completed | Paged lead list with filtering by tier, review_status, product |
| | `GET` | `/api/v1/leads/{id}` | Completed | Fetches lead details, scores, assessment, cultural affinity |
| | `PATCH` | `/api/v1/leads/{id}` | Completed | Updates `review_status` (new, saved, contacted, rejected) |
| **Evidence** | `GET` | `/api/v1/leads/{id}/evidence` | Completed | Lists persisted evidence items with database UUIDs |
| **Outreach** | `POST` | `/api/v1/leads/{id}/outreach-drafts` | Completed | Generates grounded outreach draft; rate-limited (10/min) |
| | `GET` | `/api/v1/leads/{id}/outreach-drafts` | Completed | Lists versioned drafts for lead |
| | `GET` | `/api/v1/outreach-drafts` | Completed | Lists drafts across leads with status/product filters |
| | `GET` | `/api/v1/outreach-drafts/{id}` | Completed | Fetches specific draft by ID |
| | `PATCH` | `/api/v1/outreach-drafts/{id}` | Completed | Edits subject, body, followup_notes, status |

---

## 3. Multi-Tenant Security & Owner Isolation

1. **Authentication Enforcement:**
   - Every protected route injects `user: CurrentUser = Depends(current_user)`.
   - JWT tokens are verified using `SUPABASE_JWT_SECRET` with HS256. Missing, invalid, or expired tokens return HTTP 401 in the Appendix A.5 error envelope.
2. **Owner Isolation:**
   - Database queries strictly enforce `WHERE owner_id == user.id` (or `user_id == user.id` for profiles).
   - Path parameters (`{id}`) and payload IDs are never trusted as proof of ownership. If a resource exists but belongs to another user, the API returns HTTP 404 to avoid leaking resource existence.
3. **Secret Redaction:**
   - All outgoing logs and exception messages pass through `redact_secrets()`, scrubbing `QLOO_API_KEY`, `NEBIUS_API_KEY`, `TAVILY_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, and `Bearer` tokens.

---

## 4. Deterministic Lead Scoring & Evidence Model

1. **Scoring Engine:**
   - Dimension scores (`category_fit`, `aesthetic_fit`, `evidence_quality`, `seller_compat`, `overall`, `completeness`) use nullable `float | None` and are never coerced to zero when evidence is missing.
   - Lead tiers (`qualified`, `needs_review`, `unqualified`) are computed deterministically.
   - Specific, readable reasons are recorded in `lead.scores["tier_reasons"]`.
2. **Provenance & Counterparty Trust:**
   - Evidence records carry provenance tags (`verified_fact`, `ai_inference`, `counterparty_claim`).
   - Every `EvidenceItem` has a persistent database UUID in `lead_evidence` before assessment begins.
3. **Canonical Domain Deduplication:**
   - Domains are normalized to root canonical format (`sub.example.com/shop` -> `example.com`).
   - Conflict merging: rediscovering an existing domain for the same product updates `lead.run_id` without creating duplicate records (DECISION-D2).
   - Domain exclusion: generic platforms (amazon, etsy, instagram, linkedin, etc.) are excluded or flagged.

---

## 5. Day 4 Hardening & Resilience

### Stuck-Run Recovery
- **Hook:** Executed inside FastAPI's `lifespan` startup handler.
- **Criteria:** Runs with `status == "running"` and `heartbeat_at` older than `STAGE_TIMEOUT_SECONDS` (120s) or `NULL`.
- **Action:** Transitioned to `status = "failed"`, `error = {"code": "internal_error", "message": "interrupted"}`, and `finished_at = now`.
- **Awaiting Review Isolation:** Runs in `status == "awaiting_review"` are preserved indefinitely for user interaction.

### Per-User Rate Limiting
- **Mechanism:** In-memory sliding-window limiter (`backend/app/core/rate_limit.py`).
- **Endpoints Protected:** `POST /api/v1/research-runs` and `POST /api/v1/leads/{id}/outreach-drafts`.
- **Threshold:** 10 requests per 60-second window per user.
- **Violation:** Raises `AppError(code="rate_limited", message="Too many requests, please retry shortly", status_code=429)` formatted in the Appendix A.5 error envelope.

---

## 6. Qloo Orchestration (Live / Cache / Fallback)

The `QlooOrchestrator` (`backend/app/integrations/qloo_wrapper.py`) wraps taste intelligence calls:
- **Deterministic Cache Key:** SHA-256 hash of `(endpoint, json.dumps(normalized_params, sort_keys=True))`.
- **Cache Lookup:** Checks `provider_calls` for a matching `cache_key`, `status == "success"`, within `QLOO_CACHE_TTL_HOURS` (24h). On cache hits, returns data with original `retrieved_at` without invoking the network or incrementing the quota counter.
- **Quota Cap:** Enforces `QLOO_MAX_CALLS_PER_RUN` (default 20 calls/run). Calls exceeding quota log a degraded state and return gracefully.
- **Transient Retries:** On `asyncio.TimeoutError` or HTTP 429, retries up to 2 times with exponential backoff + jitter. If retries are exhausted, records status `"rate_limited"` in `provider_calls`.
- **Audit Logging:** Every call is persisted to `provider_calls` with sanitized parameters (credentials and headers redacted). The row UUID is returned as `source_ref` on all signals and entities.
- **Failure Isolation:** Any upstream error (401, 429, 5xx, timeouts) is caught, logged in run metadata (`taste_degraded: true`), falls back to `ai_proposed` anchors, and allows the run to proceed to completion.
- **Live vs Demo Persistence:** When live (`is_demo: false`), anchors are tagged `source="qloo"`, `is_demo=false`, and real external IDs are preserved. Cultural affinity is populated into `lead.cultural_affinity` only when region or category matches apply to the lead.

---

## 7. Fixed Demo Scenario Seed Script

The seed script (`backend/app/db/seed_demo.py`) provides an idempotent entrypoint:
- **CLI Command:** `python -m backend.app.db.seed_demo [--owner-id <UUID>]`
- **Seeded Entities (`is_demo: true` on all records):**
  - **Profile:** "Sample Seller" (small textile workshop in India).
  - **4 Products:** Block-printed cotton table runner, cushion cover set, table linen set, throw (botanical motifs; terracotta, indigo, ochre colours; `mid_premium`; MOQ 50; monthly capacity 1500).
  - **1 Completed ResearchRun:** With confirmed `TasteAnchor`s and `MarketHypothesis` rows.
  - **3 Scored Leads:** 2 `qualified` ("Maison & Objet Boutique", "Atelier Living Concept") and 1 `needs_review` ("Galerie Moderne Living") with persisted `LeadEvidence` items.
  - **1 OutreachDraft:** Version 1 draft grounded in verified evidence for "Maison & Objet Boutique".

---

## 8. Test Verification Summary

The complete test suite runs under pytest with full asynchronous execution and passes without errors:

```text
backend\tests\test_auth_and_db.py .....                                  [  5%]
backend\tests\test_contracts.py ............                             [ 17%]
backend\tests\test_discovery_and_leads.py .......                        [ 24%]
backend\tests\test_foundation.py ......                                  [ 30%]
backend\tests\test_hardening_and_demo.py ...                             [ 33%]
backend\tests\test_openapi_and_stubs.py .......                          [ 40%]
backend\tests\test_outreach.py ..........                                [ 50%]
backend\tests\test_products_and_profile.py ............                  [ 62%]
backend\tests\test_qloo_orchestration.py .........                       [ 71%]
backend\tests\test_research_runs_phase1.py ........                      [ 80%]
backend\tests\test_scoring.py ...........                                [ 91%]
backend\tests\test_ws3_suite.py .........                                [100%]

============================= 99 passed in 4.92s ==============================
```
