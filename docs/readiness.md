# Vitrine Platform Readiness & Hardening Report (`docs/readiness.md`)

## 1. Executive Summary

<div align="justify">

The Vitrine platform (Backend WS2, AI Integrations WS3, and Frontend WS1) is feature-complete, hardened, and verified against Contract v0.2 specifications and production readiness standards.

### System Verification Summary
- **Backend Test Suite (Pytest):** **130 / 130 tests passing** (140s execution, including 2 new production safeguard tests, 12 contract tests, and multi-user tenant isolation tests).
- **Frontend Test Suite (Vitest):** **37 / 37 tests passing** across all route, layout, and component suites.
- **Frontend Type Safety:** `tsc --noEmit` passing with **0 errors**.
- **Frontend Linter:** `eslint .` passing with **0 errors and 0 warnings**.
- **Production Build:** Vite production bundle compiles cleanly in 7.26s.

</div>

---

## 2. Hardening Mechanisms & Architectural Enhancements

### 2.1 Production Safeguards Against Fixture Fallback

<div align="justify">

- **Problem Identified:** Previously, when `QLOO_API_KEY` or `NEBIUS_API_KEY` were omitted in production (`APP_ENV=production`), the pipeline factories unconditionally fell back to returning `FixtureResearchPipeline` and `FixtureAIService`, silently serving fabricated stockists and canned copy to real users.
- **Hardening Delivered:** In `backend/research/pipeline.py` and `backend/ai/service.py`, explicit environment checks ensure that in `production` or `prod`, missing API keys immediately raise:
  - `AppError("upstream_unavailable", "Live market intelligence service is unavailable in production.", status_code=503)`
  - `AppError("ai_generation_failed", "Live AI service is unavailable in production.", status_code=503)`
- **Regression Verification:** Added dedicated test suite `backend/tests/test_production_safeguards.py` (2/2 passing). Offline development and test environments preserve fixture fallback for local workflows.

</div>

### 2.2 Global Viewport-Centered Modal Architecture

<div align="justify">

- **Problem Identified:** Popups and confirmation dialogs were rendering in the center of the scrollable document rather than the visible browser viewport. Two interacting root causes were identified:
  1. Ancestor `.animate-page-enter` in `Shell.tsx` retained `transform: translateY(0)`, establishing a CSS containing block that trapped all `position: fixed` descendants.
  2. Dialogs were rendered inline inside nested scroll containers (`<main className="overflow-y-auto">`) without a React portal.
- **Hardening Delivered:**
  - Created centralized `frontend/src/components/shared/Modal.tsx` exporting `Modal` and `ConfirmationModal` mounted via `createPortal(..., document.body)`.
  - Configured backdrop `fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/60 backdrop-blur-xs`.
  - Added background scroll-lock (`document.body.style.overflow = 'hidden'`), keyboard focus trap (`Tab` / `Shift+Tab`), and native `Escape` key handling.
  - Corrected `@keyframes enter-up` in `frontend/src/index.css` to conclude at `transform: none`.
  - Migrated all application dialogs (Product Deletion, Lead List Rejection, Lead Detail Rejection, Outreach Regeneration, AI Extraction, New Run, Onboarding).

</div>

### 2.3 Maker Tone & Cultural Terminology

<div align="justify">

- Replaced internal AI/Qloo jargon with maker-centric concepts (*"Shopper affinity matching"*, *"Store curation alignment"*, *"Candidate Stockist"*).
- Removed raw database IDs, UUIDs, and technical model codes from maker-facing screens.
- Purged all demo badges, fictional metrics (`92/100`), and fabricated stockist records.

</div>

### 2.4 Asymmetric & Symmetric Token Verification

<div align="justify">

- Dynamic JWKS key retrieval via `PyJWKClient` from Supabase with strict audience (`authenticated`), issuer (`{SUPABASE_URL}/auth/v1`), signature, expiry, and UUID `sub` claims validation.
- Symmetric HS256 supported via `SUPABASE_JWT_SECRET`.
- Unconditional rejection of `alg=none`.
- Dev tokens strictly gated behind `ALLOW_DEV_TOKENS=true`.

</div>

### 2.5 Multi-Tenant Data Isolation

<div align="justify">

- Tenant isolation enforced across all database queries (`WHERE owner_id = :caller_id`).
- Attempting to view or mutate another user's product, run, lead, or outreach draft returns HTTP 404.

</div>

---

## 3. Endpoint Implementation Status

<div align="justify">

All endpoints conform strictly to Contract v0.2 wire types and return responses in standard envelopes.

</div>

<div align="justify">

* **System Endpoints:**
  * `GET /health` &bull; Completed &bull; Liveness probe returning `{"status": "ok"}`
  * `GET /api/v1/integrations/status` &bull; Completed &bull; Reports live/mock state for AI, Search, and Taste integrations without exposing secrets
* **Seller Profile:**
  * `GET, PUT /api/v1/profile` &bull; Completed &bull; Seller profile CRUD with automatic account creation on first sign-in
* **Product Catalog:**
  * `GET, POST /api/v1/products` &bull; Completed &bull; Multi-currency product creation (`USD`, `EUR`, `GBP`)
  * `GET, PATCH, DELETE /api/v1/products/{id}` &bull; Completed &bull; Tenant-scoped product updates and cascade deletion
* **Research Runs:**
  * `POST /api/v1/research-runs` &bull; Completed &bull; Queues run; rate-limited (10/min); Idempotency-Key support
  * `GET /api/v1/research-runs`, `GET /api/v1/research-runs/{id}` &bull; Completed &bull; Lists runs and tracks 7-stage pipeline progress
  * `POST /api/v1/research-runs/{id}/rerun` &bull; Completed &bull; Spawns a new research run copying previous input parameters
* **Taste Anchors:**
  * `GET, POST /api/v1/research-runs/{id}/anchors` &bull; Completed &bull; Lists and creates proposed/confirmed cultural anchors
  * `PATCH /api/v1/taste-anchors/{id}` &bull; Completed &bull; Confirms, rejects, or updates anchor rationale
  * `POST /api/v1/research-runs/{id}/confirm-anchors` &bull; Completed &bull; Finalizes anchor review and initiates Phase 2 (Discovery)
* **Market Hypotheses:**
  * `GET /api/v1/research-runs/{id}/hypotheses` &bull; Completed &bull; Returns market hypotheses with attached Qloo taste signals
* **Buyer Leads & Evidence:**
  * `GET /api/v1/leads`, `GET /api/v1/leads/{id}` &bull; Completed &bull; Paged lead list and detail with verified facts and fit scores
  * `PATCH /api/v1/leads/{id}` &bull; Completed &bull; Updates lead workflow status (`reviewed`, `contacted`, `rejected`)
  * `GET /api/v1/leads/{id}/evidence` &bull; Completed &bull; Returns verified store evidence items for a lead
* **Outreach Studio:**
  * `GET, POST /api/v1/leads/{id}/outreach-drafts` &bull; Completed &bull; Lists drafts and generates grounded wholesale draft
  * `PATCH /api/v1/outreach-drafts/{id}` &bull; Completed &bull; Updates subject line, draft body, or manual review status
  * `POST /api/v1/outreach-drafts/{id}/regenerate` &bull; Completed &bull; Re-generates draft using latest verified web evidence

</div>

---

## 4. Verification Commands

```bash
# Backend pytest suite (130 tests)
pytest backend/tests/ -v

# Frontend type check & lint
npm --prefix frontend run typecheck
npm --prefix frontend run lint

# Frontend tests (37 tests)
npm --prefix frontend test
```
