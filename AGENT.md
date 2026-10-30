
# AGENT.md: Shared Project Context (Read Before Touching Any Code)

> **Product name:** Not final (working options: *Stockist*, *Vitrine*, *Shelfmark*, *Serai*, *Weft*).
> Call it **"the product"** in code comments, docs, and UI-copy drafts.
> The three workstream specs carry an earlier placeholder title in their headers, file names, a repo-folder example, and one UI note. **Never use that old placeholder name.** Never hard-code any product name into package names, env vars, DB names, repo paths, or scattered UI strings.
>
> - **Frontend:** Use ONE constant (`frontend/src/config/brand.ts` exporting `BRAND_NAME`).
> - **Backend / AI / Repo:** Stay completely name-agnostic.

---

## 0. How to use this file

Give your LLM: **this file + your own workstream spec + `contracts/` once it exists**.
Tell it which workstream you own:

- **WS1:** Frontend & UX (`frontend/**`)
- **WS2:** Backend, Data & Workflow (`backend/app/**`, `supabase/**`)
- **WS3:** AI & Research Integrations (`backend/ai/**`, `backend/research/**`, `backend/integrations/qloo/**`, `fixtures/**`, `eval/**`)

If your LLM does not know which workstream it is acting for, **it must ask before writing code**.

### Precedence when sources disagree

* **Rank 1: `contracts/` in the repo + committed schemas:** Wins for exact paths, field names, enums, payload shapes, and error codes.
* **Rank 2: Your workstream spec (Appendix A is identical in all three):** Wins for your layer's internal architecture, day-by-day plan, and acceptance criteria.
* **Rank 3: This `AGENT.md` file:** Wins for cross-workstream integration rules, resolving spec contradictions, edge cases, and debugging.

This file is the cross-workstream integration contract and guardrail digest[cite: 1]. If it contradicts `contracts/`, `contracts/` wins and this file needs a fix PR[cite: 1]. If two sources conflict and the answer is not already resolved in **Section 11** of this file, **do not pick silently**: state the conflict, propose a resolution, and record it in `docs/decisions.md`[cite: 1].

---

## 1. What we are building

An AI-assisted **retailer-discovery and outreach-preparation tool** for small physical-product brands that want to sell wholesale to independent overseas retailers[cite: 1]. The demo seller is a small block-printed home-textile workshop; the data model and code stay **100% country-agnostic and category-agnostic**[cite: 1].

**Core promise:** Evidence-backed prospect discovery and seller-controlled outreach drafts[cite: 1].
**Not:** Guaranteed sales, autonomous selling, or proof that cultural taste predicts purchase[cite: 1].

### Seller journey (contract v0.1)

1. **Sign up / Profile:** Seller signs in and sets basic workshop/seller profile details[cite: 2, 3].
2. **Product Passport:** Create a structured product record (AI Task A may suggest attributes from free text; seller reviews and confirms before saving)[cite: 1, 3, 4].
3. **Start Research Run:** Seller selects a product and optional region/retailer hints[cite: 1, 3]. The run plans research (AI Task B) and proposes taste/aesthetic **anchors** and initial **market hypotheses**[cite: 1, 2, 4].
4. **Anchor Review (`awaiting_review`):** Seller reviews anchors (confirm / reject / edit / add custom) and clicks Continue[cite: 1, 3].
5. **Taste Resolution & Discovery:** Confirmed anchors resolve through the Taste Provider (mock until Qloo key arrives)[cite: 1, 4], signals attach to hypotheses[cite: 4], and the Research Pipeline finds real retailers via Tavily web search, verifies websites deterministically, extracts evidence, and deduplicates[cite: 1, 4].
6. **Assess & Score:** Each candidate lead is assessed by AI (Task C, strictly citing stored `evidence_ids`) and scored by deterministic code (WS2) into a priority score and tier (`qualified`, `needs_review`, `unqualified`)[cite: 1, 2, 4].
7. **Lead Inspection:** Seller filters/reviews leads (save / reject / add note) and inspects evidence excerpts, source links, provenance tags, and explicit `unknowns`[cite: 1, 3].
8. **Outreach Studio:** Seller generates a grounded B2B outreach draft (AI Task D, citing `facts_used`), edits it (auto-saved), regenerates versions if needed, copies to clipboard, and tracks status **manually** (`draft` -> `ready` -> `contacted`)[cite: 1, 3, 4].

### Scope fence (HARD RULES)

**In scope for v0.1:** Everything in the 8-step journey above[cite: 1].

**Out of scope: Do NOT build, stub, scaffold, "prepare for", or add dependencies for:**

- **Any payment provider (PayPal or other):** No SDK, invoice, webhook, payment-state, or payment UI anywhere.
- **Orders & quotes:** No order tracking, quote builders, buyer-reply parsing, or "Orders & Payments" screens.
- **Outbound email sending:** No SMTP/SendGrid/Resend, no `send` endpoint, and **no Send button** in the UI. Outreach is draft, edit, copy to clipboard, and manual status tracking only.
- **Bloat:** No large agent frameworks (LangChain/CrewAI/AutoGen), fine-tuning, computer vision, voice, or multi-tenant admin portals.
- **Scraping abuse:** Never bypass logins, paywalls, robots restrictions, or anti-bot walls.
- **Guessed Qloo schemas:** Never invent Qloo API endpoints, parameter names, or response fields before real API docs/responses are in hand. Use the internal `TasteResearchProvider` interface and `MockTasteProvider` (`is_demo: true`) until the key arrives.

If a task seems to require anything above, **stop and ask**. A later phase can only start after an explicit team decision, a reviewed contract PR, and a recorded owner.

### Fixed demo scenario (all three workstreams build and test against this)

- **Seller:** "Sample Seller" (small textile workshop; origin country is an optional field, never hard-coded).
- **Catalogue:** Block-printed cotton table runner; cushion cover set; table linen set; throw.
- **Core attributes:** Botanical motifs; warm earthy colours (`terracotta`, `indigo`, `ochre`); `mid_premium` positioning; MOQ `50` sets; monthly capacity `1500` units (placeholders).
- **Target buyers:** Independent home-decor boutiques, home-textile retailers, interior and lifestyle shops.
- **Truth rule:** Seeded seller/product data is fictional and **labelled demo** (`is_demo: true`); retailer claims and URLs shown as live results must be real and verifiable.

---

## 2. Ownership and dependency direction

* **WS1 (Frontend & UX):**
  * **Owns:** `frontend/**`: screens, routing, design system, forms, Zod schemas, typed API client, mock-data layer (`VITE_USE_MOCK`), loading/empty/error states, responsive layout, and accessibility.
  * **Never touches:** DB, auth verification rules, backend endpoints, scoring math, prompts, provider clients, or secret API keys.
* **WS2 (Backend, Data & Workflow):**
  * **Owns:** `backend/app/**` (API, DB and SQL migrations, auth, background jobs, deterministic scoring), Supabase and RLS, run state machine and async runner, persistence of AI/Tavily/taste outputs, and `/integrations/status`.
  * **Never touches:** React code, prompt templates, direct Nebius/Tavily/Qloo HTTP calls (must call WS3 factories only), or model tuning.
* **WS3 (AI & Research):**
  * **Owns:** `backend/ai/**`, `backend/research/**`, `backend/integrations/qloo/**`, `fixtures/**`, `eval/**`, model call logging.
  * **Never touches:** FastAPI endpoints, DB queries/writes, auth, job runner, scoring math/weights, React code, or invented Qloo schemas.
* **Shared:**
  * **Owns:** `contracts/`, `docs/decisions.md`, `docs/readiness.md`.
  * **Governance:** Changes require a PR reviewed by all three owners.

### Direction of calls (no shortcuts)

`WS1 (React/TS) --HTTP/JSON (snake_case)--> WS2 (FastAPI/DB) --Python Interfaces--> WS3 (AI/Tavily/Taste) --HTTPS--> Nebius / Tavily / Qloo`[cite: 1]

1. **WS1** never imports from `backend/` or `fixtures/` directly; pages call hooks in `frontend/src/api/` which switch between `frontend/src/mocks/` and HTTP via `VITE_USE_MOCK`[cite: 1, 3].
2. **WS2** never imports a provider SDK/client or prompt[cite: 1, 2]. WS2 calls **only** the three WS3 factory functions[cite: 1, 2]:
   - `get_ai_service() -> AIService`[cite: 1, 2, 3, 4]
   - `get_research_pipeline() -> ResearchPipeline`[cite: 1, 2, 3, 4]
   - `get_taste_provider() -> TasteResearchProvider`[cite: 1, 2, 3, 4]
3. **WS3** never reads or writes the database or defines HTTP endpoints[cite: 1, 4]. It accepts Pydantic models and returns validated Pydantic models[cite: 4].
4. **Every WS3 factory returns a fixture-backed implementation when credentials are missing**, and WS2 surfaces that state via `/integrations/status` and `research_run.provider_modes`[cite: 1, 2, 4]. Missing optional keys must **never** crash the server[cite: 1, 2].
5. **The model proposes; deterministic code verifies**[cite: 1, 4]. URL liveness checks, canonical domain extraction, deduplication, date checks, scoring arithmetic, auth, ownership, and state transitions are never delegated to an LLM[cite: 1, 4].
6. **The database is the source of truth**[cite: 1, 2]. No in-memory workflow state[cite: 1, 2].

---

## 3. End-to-end flow: exact hand-offs at each step

<div align="justify">

* **Step 0: Auth & Profile:**
  * *WS1 (UI):* Supabase sign-in; first-time seller profile form (`GET/PUT /profile`).
  * *WS2 (API/DB):* Verifies Supabase JWT (`user_id` from token); upserts `profiles` row.
  * *WS3 (AI/Taste):* None.
* **Step 1: Create Product:**
  * *WS1 (UI):* Product Passport form (Zod mirrors contract); `POST /products`, `POST /products/{id}/images`.
  * *WS2 (API/DB):* Validates (`price_min <= price_max`, `moq >= 1`), sets `owner_id` from JWT, persists.
  * *WS3 (AI/Taste):* None.
* **Step 2: AI Suggest:**
  * *WS1 (UI):* Sends description + known fields to `POST /products/extract-profile`; renders side-by-side diff review panel; nothing saved until seller accepts; form survives any error.
  * *WS2 (API/DB):* Calls `get_ai_service().structure_product(...)`; returns suggestion without writing to DB.
  * *WS3 (AI/Taste):* Task A (`structure_product`) -> `ProductAttributes` (+ `uncertain_fields[]`, `assumptions[]`).
* **Step 3: Start Run:**
  * *WS1 (UI):* Start panel; sends `POST /research-runs` with `Idempotency-Key` header.
  * *WS2 (API/DB):* Creates `research_runs` row (`status: queued`, `stage: planning`), snapshots `provider_modes` (`live` vs `mock`).
  * *WS3 (AI/Taste):* None.
* **Step 4: Plan & Propose Anchors:**
  * *WS1 (UI):* StatusStepper polls `GET /research-runs/{id}` every 2-3s while `queued` or `running`.
  * *WS2 (API/DB):* Runner calls `plan_research(product)`; saves `plan`; creates `taste_anchors` (`source: ai_proposed`, `status: proposed`) and initial `market_hypotheses`; sets `status: awaiting_review`, `stage: anchor_review`.
  * *WS3 (AI/Taste):* Task B (`plan_research`) -> `ResearchPlan` (proposals only; never claims a provider returned data).
* **Step 5: Anchor Review:**
  * *WS1 (UI):* Lists anchors with source/demo badges; confirm, reject, edit (`PATCH /taste-anchors/{id}`), or add custom (`POST /research-runs/{id}/anchors`); clicks Continue (`POST .../confirm-anchors`).
  * *WS2 (API/DB):* Updates anchors; `confirm-anchors` requires `>= 1` confirmed anchor (or `proceed_without_anchors: true`); transitions run to `status: queued`.
  * *WS3 (AI/Taste):* None.
* **Step 6: Taste Resolution & Discovery:**
  * *WS1 (UI):* Stepper shows `discovery` stage and elapsed time.
  * *WS2 (API/DB):* Runner resolves confirmed anchors via `get_taste_provider()` (`search_entities` + `get_insights`), copies `source` & `is_demo` to anchors/hypothesis signals; calls `ResearchPipeline.run(..., on_progress)`; enforces lead cap (default 40).
  * *WS3 (AI/Taste):* Taste provider (`MockTasteProvider` until Qloo key) -> entities/signals; Tavily search -> extract -> deterministic HTTP verify -> domain match -> dedupe -> `LeadCandidate[]`.
* **Step 7: Assess & Score:**
  * *WS1 (UI):* Stepper shows `assessment` -> `scoring` -> `done`.
  * *WS2 (API/DB):* First upserts lead + `lead_evidence` rows so each `EvidenceItem` has a real UUID; then calls `assess_lead(product, candidate, evidence_items)`; then runs deterministic scoring + tiering and updates the lead.
  * *WS3 (AI/Taste):* Task C (`assess_lead`) -> `LeadAssessment` (labels, reasons, cited `evidence_ids[]`, `unknowns[]`); post-checks reject any claim citing a non-existent `evidence_id`.
* **Step 8: Buyer Leads:**
  * *WS1 (UI):* Table with search/filters/sort/pagination; detail drawer with `ScoreBar`s, `tier_reasons`, `unknowns`, `EvidenceCard`s, separate Cultural Affinity box; Save/Reject/Note with optimistic update.
  * *WS2 (API/DB):* `GET /leads` (filtered/paged), `GET/PATCH /leads/{id}`, `GET /leads/{id}/evidence`.
  * *WS3 (AI/Taste):* None.
* **Step 9: Outreach Studio:**
  * *WS1 (UI):* Shows product facts & lead evidence; Generate (`POST /leads/{id}/outreach-drafts`), edit subject/body (auto-save via `PATCH`), view version history, Regenerate (`POST /outreach-drafts/{id}/regenerate`), copy to clipboard.
  * *WS2 (API/DB):* Persists drafts with `version` incrementing per lead; regeneration inserts a new version row (never overwrites); `PATCH` updates subject/body/status/notes.
  * *WS3 (AI/Taste):* Task D (`draft_outreach`) -> builds numbered fact list from approved product fields + stored evidence -> returns `OutreachDraft` (`subject`, `body`, `facts_used[]`, `warnings[]`); post-checks block hallucinated URLs/numbers.
* **Step 10: Manual Status:**
  * *WS1 (UI):* Seller switches `draft -> ready -> contacted` and writes follow-up notes. No send button.
  * *WS2 (API/DB):* When `PATCH /outreach-drafts/{id}` sets `status = contacted`, WS2 atomically sets parent `lead.review_status = contacted`.
  * *WS3 (AI/Taste):* None.

</div>

---

## 4. Contract digest (v0.1: verify against `contracts/`)

- **Format:** IDs are UUIDs. Timestamps are ISO 8601 UTC strings. Base path `/api/v1`.
- **Auth:** Every route except `GET /health` requires `Authorization: Bearer <Supabase JWT>`.
- **Wire case:** **`snake_case` end-to-end** (`is_demo`, `review_status`, `price_min`, `facts_used`). Frontend TypeScript interfaces, Zod schemas, and mock fixtures **must use `snake_case`** to match the API exactly. Do not use `isDemo` in frontend mocks.
- **Evolution:** Optional fields may be added via coordinated update; **renames and removals require a PR approved by all three owners**.

### 4.1 Enumerations (Exact Values)

<div align="justify">

* `research_run.status`: `queued`, `running`, `awaiting_review`, `completed`, `failed`. Runner stops at `awaiting_review` until seller confirms.
* `research_run.stage`: `planning`, `anchor_proposal`, `anchor_review`, `discovery`, `assessment`, `scoring`, `done`. Updated at every transition.
* `lead.review_status`: `new`, `saved`, `rejected`, `contacted`. "Saved leads" equals `review_status == 'saved'` (no separate table).
* `lead.tier`: `qualified`, `needs_review`, `unqualified`. Missing evidence pushes toward `needs_review`, never `unqualified`.
* `outreach_draft.status`: `draft`, `ready`, `contacted`. Manual tracking only.
* `taste_anchor.status`: `proposed`, `confirmed`, `rejected`.
* `taste_anchor.source`: `ai_proposed`, `user_added`, `qloo`, `demo`. Note that `qloo` is only set from a real Qloo API response.
* `market_hypothesis.status`: `proposed`, `confirmed`, `rejected`. Default `proposed`.
* Dimension labels (`category_fit`, `aesthetic_fit`, `seller_compat`): `high`, `medium`, `low`, `unknown`. Note that `unknown` indicates no evidence either way.
* `evidence.source_type`: `official_site`, `product_page`, `social`, `directory`, `press`, `marketplace`, `other`. Classified deterministically where possible.
* Provenance tags: `verified_fact`, `ai_assessment`, `unknown`, `demo_data`. Every claim in the UI carries one.
* Integration states: `live`, `mock`, `pending`, `disabled`. Used by `/integrations/status` and `provider_modes`.
* `price_segment`: `budget`, `mid`, `mid_premium`, `premium`, `luxury`.

</div>

### 4.2 Core Data Objects (Agreed Minimum Fields)

- **Profile (D16):** `id, user_id, business_name, country (null|str), website (null|str), contact_email (null|str), about (null|str), created_at, updated_at`[cite: 2]
- **Product:** `id, owner_id, name, category, description, materials[], style[], motifs[], colours[], price_segment, price_min, price_max, currency, moq, monthly_capacity, target_retailer_types[], images[] (string URLs, see D18), is_demo (optional bool), created_at, updated_at`[cite: 1, 2, 3, 4]
- **ProductAttributes (Task A output, D19):** `style[], materials[], motifs[], colours[], price_segment (null|str), target_retailer_types[], category (optional), price_min (optional), price_max (optional), currency (optional), moq (optional), monthly_capacity (optional), uncertain_fields[], assumptions[]`[cite: 3, 4]
- **ResearchRun:** `id, product_id, status, stage, inputs{regions[], retailer_types[], notes, anchor_ids[]}, plan (ResearchPlan|null), error{code, message}|null, provider_modes{taste, search, ai}, started_at (null|str), finished_at (null|str), heartbeat_at (null|str), created_at`[cite: 1, 2, 3, 4]
- **TasteAnchor:** `id, run_id, label, entity_type, external_id (null unless real provider returned it), source, status, rationale, metadata{}, is_demo (bool)`[cite: 1, 2, 3, 4]
- **MarketHypothesis:** `id, run_id, title, rationale, region_hint (null|str), signals[{type, text, source, is_demo}], status`[cite: 1, 2, 3, 4]
- **Lead:** `id, run_id, product_id, name, website, canonical_domain, location{city, region, country}|null, retailer_type, website_verified (bool), website_checked_at (null|str), tier, scores{category_fit, aesthetic_fit, evidence_quality, seller_compat, overall, completeness, tier_reasons[]}, assessment (LeadAssessment|null), cultural_affinity (null|object), review_status, notes, duplicate_of (null|uuid), is_demo (bool), created_at`[cite: 1, 2, 3, 4]
- **EvidenceItem:** `id, lead_id, url, excerpt, source_type, retrieved_at, published_at (null|str), domain_matches_lead (bool), provenance, is_demo (optional bool)`[cite: 1, 2, 3, 4]
- **LeadAssessment:** `category_fit{label, reasons[], evidence_ids[]}, aesthetic_fit{label, reasons[], evidence_ids[]}, seller_compat{label, reasons[], evidence_ids[]}, summary, unknowns[], model_id, generated_at`[cite: 1, 2, 3, 4]
- **OutreachDraft:** `id, lead_id, product_id, version (int), subject, body, facts_used[{fact_id, text, source_url}], warnings[] (string[], D5), status, followup_notes, parent_draft_id (null|uuid), is_demo (optional bool), created_at, updated_at`[cite: 1, 2, 3, 4]

### 4.3 REST API Endpoints (`/api/v1`)

- **System & Profile:** `GET /health` (no auth)[cite: 1, 2, 3, 4] · `GET /integrations/status`[cite: 1, 2, 3, 4] · `GET /profile` (D16) · `PUT /profile` (D16) · `GET /dashboard/summary` (optional helper, D17)
- **Products:** `GET /products`[cite: 1, 2, 3, 4] · `POST /products`[cite: 1, 2, 3, 4] · `GET /products/{id}`[cite: 1, 2, 3, 4] · `PUT /products/{id}`[cite: 1, 2, 3, 4] · `DELETE /products/{id}`[cite: 1, 2, 3, 4] · `POST /products/{id}/images`[cite: 1, 2, 3, 4] · `POST /products/extract-profile`[cite: 1, 2, 3, 4]
- **Research Runs & Anchors:** `POST /research-runs` (supports `Idempotency-Key` header)[cite: 1, 2, 3, 4] · `GET /research-runs`[cite: 1, 2, 3, 4] · `GET /research-runs/{id}`[cite: 1, 2, 3, 4] · `POST /research-runs/{id}/rerun`[cite: 1, 2, 3, 4] · `GET /research-runs/{id}/anchors`[cite: 1, 2, 3, 4] · `POST /research-runs/{id}/anchors` (custom anchor, D3)[cite: 1] · `PATCH /taste-anchors/{id}`[cite: 1, 2, 3, 4] · `POST /research-runs/{id}/confirm-anchors` (accepts `{"proceed_without_anchors": bool}`, D4)[cite: 1, 2, 3, 4] · `GET /research-runs/{id}/hypotheses`[cite: 1, 2, 3, 4]
- **Leads & Evidence:** `GET /leads` (query: `run_id, product_id, review_status, tier, q, location, min_score, sort=score_desc|name|newest, page, page_size<=100`; returns `{items, total, page, page_size}`, D7)[cite: 1, 2, 3, 4] · `GET /leads/{id}`[cite: 1, 2, 3, 4] · `PATCH /leads/{id}`[cite: 1, 2, 3, 4] · `GET /leads/{id}/evidence`[cite: 1, 2, 3, 4]
- **Outreach Drafts:** `GET /outreach-drafts` (optional top-level list filtered by `status, lead_id, product_id`, D17) · `POST /leads/{id}/outreach-drafts`[cite: 1, 2, 3, 4] · `GET /leads/{id}/outreach-drafts`[cite: 1, 2, 3, 4] · `PATCH /outreach-drafts/{id}`[cite: 1, 2, 3, 4] · `POST /outreach-drafts/{id}/regenerate`[cite: 1, 2, 3, 4]

*Note:* There is **no cancel-run endpoint** in v0.1[cite: 1]. UI offers Retry / Rerun only[cite: 1, 3].

### 4.4 Error Envelope

- **Shape:** `{"error": {"code": "validation_error", "message": "Human readable text", "details": {"field": "moq", "reason": "must be >= 1"}, "request_id": "..."}}`[cite: 1, 2, 3, 4]
- **Allowed codes:** `validation_error | unauthorized | forbidden | not_found | conflict | upstream_timeout | upstream_unavailable | ai_output_invalid | rate_limited | internal_error`[cite: 1, 2, 3, 4]
- **UI Retry button shown ONLY for:** `upstream_timeout`, `upstream_unavailable`, `rate_limited`[cite: 1, 2, 3, 4].
- **`unauthorized`:** Redirect to `/login` (preserving unsaved form state where practical)[cite: 1, 3].

---

## 5. Run state machine (WS2 owns; WS1 renders; WS3 feeds progress)

- **Status flow:** `queued -> running -> awaiting_review -> (confirm-anchors) -> queued -> running -> completed` (any unrecoverable stage error transitions to `failed`)[cite: 1, 2].
- **Stage progression:** `planning -> anchor_proposal -> anchor_review -> discovery -> assessment -> scoring -> done`[cite: 1, 2, 3, 4].
- Status and stage are **persisted to PostgreSQL at every transition**[cite: 1, 2]. `heartbeat_at` updates during long stages[cite: 1, 2].
- The runner **stops completely at `awaiting_review`**[cite: 1, 2]. Time spent in `awaiting_review` **does not count** toward `RUN_MAX_SECONDS` (D10)[cite: 1].
- `completed` with **zero leads is a valid completion** and stores an explanatory note in `plan`/outputs[cite: 1, 2].
- On server startup, any run left in `running` with a stale `heartbeat_at` is marked `failed` (`code: internal_error`, `message: "interrupted"`)[cite: 1, 2]. Runs in `awaiting_review` are untouched[cite: 1].
- Per-lead assessment/scoring failures **never abort the run**: the lead is saved with `tier: needs_review`, an `unknowns` note, and the error recorded[cite: 1, 2].
- **Configurable defaults:** `STAGE_TIMEOUT_SECONDS=120`, `RUN_MAX_SECONDS=600`, lead cap `40`, transient retries `2` with exponential backoff + jitter, Tavily caps: `<= 8` queries/run, `10` results/query, `30` page extractions/run, `20s` per-call timeout[cite: 1, 2, 4].

---

## 6. Scoring and tiering (WS2 is the ONLY place this math lives)

A lead score is a **prioritisation heuristic for human review**, never a purchase probability[cite: 1, 2]. UI labels it **"Priority score"** (never "probability", "likelihood to buy", or "conversion")[cite: 1, 2, 3].

<div align="justify">

* **`category_fit` (Source: WS3 `LeadAssessment.category_fit.label`):** `high` -> `100`, `medium` -> `60`, `low` -> `20`, `unknown` -> **`null`**.
* **`aesthetic_fit` (Source: WS3 `LeadAssessment.aesthetic_fit.label`):** `high` -> `100`, `medium` -> `60`, `low` -> `20`, `unknown` -> **`null`**.
* **`evidence_quality` (Source: Computed deterministically by WS2 from `lead_evidence`):** Start at `0`. `+40` `official_site` page present; `+20` `>= 2` distinct source URLs; `+20` `product_page` excerpt present; `+10` published or retrieved within 24 months; `+10` location/contact verified in excerpt. Capped at `100`.
* **`seller_compat` (Source: WS3 `LeadAssessment.seller_compat.label`):** `high` (match) -> `100`, `medium` (adjacent) -> `60`, `low` (mismatch) -> `20`, `unknown` (no evidence) -> **`null`**.
* **`cultural_affinity` (Source: Taste provider, real Qloo only):** Stored separately in `lead.cultural_affinity`. Excluded from `overall` score. Remains `null` until a validated real Qloo signal exists.

</div>

- **Weights:** `category_fit: 35`, `aesthetic_fit: 25`, `evidence_quality: 20`, `seller_compat: 20`[cite: 1, 2]. Keep weights and mappings in one config module with unit tests[cite: 1, 2].
- **`overall`:** Weighted average over **non-null** dimensions with weights renormalised to 100%[cite: 1, 2]. If all four are `null`, `overall` is `null`[cite: 1, 2].
- **`completeness`:** `(count of non-null dimensions) / 4.0`[cite: 1, 2]. If `completeness < 0.75`, the UI shows a **"Preliminary"** badge[cite: 1, 2].
- **Tier gates:**
  - `qualified`: `website_verified == true` AND `>= 1` retail-activity evidence item (`official_site` or `product_page`) AND `category_fit` in (`high`, `medium`) AND `evidence_quality >= 40`[cite: 1, 2].
  - `unqualified`: `website_verified == false`, OR (`category_fit == low` WITH supporting `evidence_ids`), OR domain excluded as a marketplace/wholesaler/chain[cite: 1, 2].
  - `needs_review`: Everything else (e.g., verified site with `unknown` category fit, `evidence_quality` 20–39, or per-lead AI error)[cite: 1, 2]. **Missing evidence always moves a lead toward `needs_review`, never `unqualified`**[cite: 1, 2].
- Store human-readable `tier_reasons: string[]` inside `scores` so WS1 can display why the lead landed in its tier (D6)[cite: 1, 2].

---

## 7. Truth rules and the null chain (#1 source of integration bugs)

1. **The `unknown` -> `null` chain must survive every hop unchanged:**
   `WS3 outputs label: "unknown"` -> `WS2 stores score: null (never 0, never 20)` -> `WS1 ScoreBar renders "Not enough evidence" (never a 0% bar)`[cite: 1, 2, 3, 4].
   *Watch out for:* Python `score or 0`, TypeScript `score || 0`, Pydantic `0` defaults, SQL `COALESCE(score, 0)`, or chart bars treating `null` as `0`[cite: 1].
2. **The `is_demo` chain must survive every hop unchanged:**
   `WS3 sets is_demo: true / "_fixture": true` -> `WS2 copies is_demo onto stored anchors, signals, leads, and drafts and preserves it in Pydantic response models` -> `WS1 renders <DemoBadge/>`[cite: 1, 2, 3, 4].
   Mock taste IDs must use unmistakable prefixes (`demo-...`)[cite: 1, 4].
3. **Strict evidence citations:**
   - In Task C (`assess_lead`), every reason for a `high`, `medium`, or `low` label must cite at least one valid `evidence_id` from the input list[cite: 1, 4]. Claims with empty `evidence_ids` or hallucinated IDs are rejected by WS3's post-check before returning to WS2[cite: 1, 4].
   - In Task D (`draft_outreach`), product claims come only from seller-confirmed `Product` fields and retailer claims come only from stored `EvidenceItem`s[cite: 1, 4]. Every used fact is listed in `facts_used[{fact_id, text, source_url}]`[cite: 1, 4]. Any body text introducing outside URLs, prices, or numbers is rejected or flagged in `warnings[]`[cite: 4].
4. **Qloo separation:** Qloo provides cultural/taste context only[cite: 1, 4]. It is not a retailer directory, demand proof, or conversion predictor[cite: 1, 4]. UI keeps "Market hypothesis" visually distinct from "Verified retailer fact", and cultural affinity distinct from retail scores[cite: 1, 3].

---

## 8. Security & untrusted-content rules (all workstreams)

- **Secrets isolation:** `NEBIUS_API_KEY`, `TAVILY_API_KEY`, `QLOO_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, and `SUPABASE_JWT_SECRET` exist **only** in backend environment variables[cite: 1, 2, 3, 4]. Never in frontend code, `VITE_*` vars, git commits, fixtures, responses, or logs[cite: 1, 2, 3, 4].
- **Allowed frontend env vars:** `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` (public by design), `VITE_USE_MOCK`[cite: 1, 3].
- **Per-user isolation (Defense in depth):**
  1. PostgreSQL RLS enabled on every table (`owner_id = auth.uid()`, or `user_id = auth.uid()` on `profiles`)[cite: 1, 2].
  2. WS2 explicitly filters by `owner_id = current_user.id` on every query[cite: 1, 2].
  3. Child endpoints (`/taste-anchors/{id}`, `/leads/{id}/...`, `/outreach-drafts/{id}`) verify parent record ownership before reading or writing[cite: 1, 2].
  4. Accessing another seller's resource returns **404 `not_found`** (never 403)[cite: 1, 2].
  5. Background runner uses the service role key but explicitly copies `owner_id` onto every inserted row[cite: 1, 2].
- **Prompt injection defense:** Scraped retailer web pages are **untrusted data**[cite: 1, 4]. WS3 wraps excerpts in strict data delimiters so instructions inside a webpage are ignored (tested via a hostile-excerpt unit test)[cite: 1, 4]. WS1 renders all excerpts as plain text (never `dangerouslySetInnerHTML`) and opens external links with `target="_blank" rel="noopener noreferrer"`[cite: 1].
- **Logging:** Structured JSON logs with `request_id`[cite: 1, 2]. Model calls log `task`, `model_id`, prompt version, latency, validation outcome, token counts, and `error_code`[cite: 1, 4]. Never log API keys, tokens, or full email bodies[cite: 1, 2, 4].

---

## 9. Edge-case matrix: what each layer must do

<div align="justify">

* **Optional API key missing:**
  * *WS3 (AI/Research):* Factory returns fixture-backed service (`is_demo=True`).
  * *WS2 (Backend/Runner):* Run succeeds; `/integrations/status` & `provider_modes` report `mock`.
  * *WS1 (Frontend/UI):* `IntegrationBanner` shows `Mock (demo data)`; `<DemoBadge/>` shown on items.
* **Tavily returns 0 results:**
  * *WS3 (AI/Research):* Return `[]` + reason; never invent shops.
  * *WS2 (Backend/Runner):* Run finishes as `completed` with 0 leads + explanatory note in `plan`.
  * *WS1 (Frontend/UI):* `EmptyState` explains why and offers "Edit inputs & Rerun".
* **Model returns invalid JSON or unsupported claim:**
  * *WS3 (AI/Research):* 1 automatic repair retry passing validation errors; if still bad, raise `ai_output_invalid`.
  * *WS2 (Backend/Runner):* Do not save invalid output. Global task (Task A/B/D) -> return error / fail stage. Per-lead (Task C) -> set lead `tier: needs_review` + error note, continue run.
  * *WS1 (Frontend/UI):* Show error message (no Retry button for `ai_output_invalid`); preserve user form data.
* **Assessment cites unknown `evidence_id`:**
  * *WS3 (AI/Research):* Rejected by deterministic claim check.
  * *WS2 (Backend/Runner):* Never persisted.
  * *WS1 (Frontend/UI):* None.
* **Provider timeout / 429 / 5xx:**
  * *WS3 (AI/Research):* Bounded retries with exponential backoff + jitter; raise `upstream_timeout` or `upstream_unavailable`.
  * *WS2 (Backend/Runner):* Map to A.5 error format; if in runner, fail run and record failing `stage`.
  * *WS1 (Frontend/UI):* Show `ErrorState` with Retry / Rerun button.
* **Taste provider returns empty or weak signals:**
  * *WS3 (AI/Research):* Return empty/weak list as-is (`MockTasteProvider` includes these cases).
  * *WS2 (Backend/Runner):* Store as returned; run continues; no fabricated score.
  * *WS1 (Frontend/UI):* Show `"No signals returned for this anchor"`; do not hide section or pad with fake data.
* **Seller clicks Continue with 0 confirmed anchors:**
  * *WS3 (AI/Research):* None.
  * *WS2 (Backend/Runner):* Return `422 validation_error` unless body has `{"proceed_without_anchors": true}`.
  * *WS1 (Frontend/UI):* Disable Continue button until `>= 1` anchor confirmed, or offer explicit "Proceed without anchors" toggle.
* **Duplicate lead: same `canonical_domain`:**
  * *WS3 (AI/Research):* Merge evidence in pipeline.
  * *WS2 (Backend/Runner):* `ON CONFLICT (owner_id, product_id, canonical_domain)` merges new evidence into existing lead.
  * *WS1 (Frontend/UI):* Single lead row shown with combined evidence count.
* **Duplicate lead: same normalized name + city, different domain:**
  * *WS3 (AI/Research):* Flag via `possible_duplicate_of_domain` (D9).
  * *WS2 (Backend/Runner):* Insert lead and set `duplicate_of = primary_lead.id`.
  * *WS1 (Frontend/UI):* Render `"Possible duplicate"` badge linking to the primary lead; never silently hide.
* **Marketplace storefront URL (e.g. Etsy shop):**
  * *WS3 (AI/Research):* Key canonical identity by full shop path, not root marketplace domain.
  * *WS2 (Backend/Runner):* Persist with shop-path canonical key or exclude if root marketplace.
  * *WS1 (Frontend/UI):* Displays shop URL accurately.
* **Server restarts mid-run:**
  * *WS3 (AI/Research):* None.
  * *WS2 (Backend/Runner):* Startup hook marks stale `running` rows (`heartbeat_at` expired) as `failed` (`"interrupted"`); leaves `awaiting_review` alone.
  * *WS1 (Frontend/UI):* Shows failed stage with Rerun button.
* **Double-click on Start Research:**
  * *WS3 (AI/Research):* None.
  * *WS2 (Backend/Runner):* `Idempotency-Key` header prevents duplicate run creation.
  * *WS1 (Frontend/UI):* Sends `Idempotency-Key` header and disables button while submitting.
* **Qloo key arrives:**
  * *WS3 (AI/Research):* Enable real provider behind `get_taste_provider()` per runbook.
  * *WS2 (Backend/Runner):* Set `QLOO_API_KEY`; confirm `taste: live`; new runs get `source: qloo`, `is_demo: false`, real `external_id`.
  * *WS1 (Frontend/UI):* Verify real signals render; old runs keep demo badges and are never mixed.

</div>

---

## 10. Influence map: "If I change X, who must know?"

<div align="justify">

* **Rename or remove any field or enum value:** Impacts WS1, WS2, WS3. Required Action: PR to `contracts/` approved by all 3 owners.
* **Add an optional field:** Impacts WS1, WS2, WS3. Required Action: Add to `contracts/`; update WS2 Pydantic + migration, WS1 TS types + mocks, WS3 schemas + fixtures.
* **Score weights, label mappings, or tier gates:** Impacts WS2, WS1, WS3. Required Action: Update WS2 scoring config module + unit tests + log in `docs/decisions.md`.
* **Progress callback stage names:** Impacts WS3, WS2, WS1. Required Action: Must match `research_run.stage` enum values word-for-word.
* **Fixture files in `fixtures/` or `frontend/src/mocks/`:** Impacts WS1, WS2, WS3. Required Action: Must validate against `contracts/` schemas and carry `is_demo: true`.

</div>

---

## 11. Resolved & proposed defaults for all 20 spec gaps (`DECISION-D1` to `D20`)

Comparing the WS1, WS2, and WS3 specs revealed 20 places where a field, endpoint, or workflow step was mismatched or missing. **Use the proposed defaults below so all three workstreams code to the exact same shape from Day 1**. Tag implementations `# DECISION-Dn` and confirm at the Day 1 meeting.

<div align="justify">

* **DECISION-D1 (Integration states & demo flags):**
  * *Affects:* All workstreams.
  * *Resolution:* Use the A.2 enum (`live | mock | pending | disabled`) everywhere. Add `is_demo: bool = False` to `Lead`, `EvidenceItem`, and `OutreachDraft`.
* **DECISION-D2 (Lead run affiliation on rerun):**
  * *Affects:* WS2, WS1.
  * *Resolution:* Update `leads.run_id` to the latest `run_id` on conflict merge (or maintain a `run_leads(run_id, lead_id)` join table) so `GET /leads?run_id=` always returns all leads found or updated in that run.
* **DECISION-D3 (Custom taste anchor creation):**
  * *Affects:* WS1, WS2.
  * *Resolution:* Add `POST /api/v1/research-runs/{id}/anchors` accepting `{label, entity_type, rationale?}` and creating a row with `source="user_added"`, `status="confirmed"`, and `is_demo=False`.
* **DECISION-D4 (Proceed without anchors payload):**
  * *Affects:* WS1, WS2.
  * *Resolution:* `POST /api/v1/research-runs/{id}/confirm-anchors` accepts optional JSON body `{"proceed_without_anchors": false}`.
* **DECISION-D5 (Outreach warnings field):**
  * *Affects:* All workstreams.
  * *Resolution:* Add `warnings jsonb default '[]'` to `outreach_drafts` table and `warnings: list[str] = []` to `OutreachDraft`.
* **DECISION-D6 (Tier reasons & evidence criteria):**
  * *Affects:* All workstreams.
  * *Resolution:* Add `tier_reasons: list[str]` inside `Lead.scores`. Define retail-activity evidence as at least one `EvidenceItem` with `source_type` in `("official_site", "product_page")`. Define location/contact verified as `lead.location` is non-null or contact info is cited in an evidence excerpt.
* **DECISION-D7 (Leads pagination, sorting & filters):**
  * *Affects:* WS1, WS2.
  * *Resolution:* `GET /leads` returns `{items: Lead[], total: int, page: int, page_size: int}`. Add optional `location: str` query param to `GET /leads`. Standardize sort values on `score_desc | name | newest` (WS1 maps UI "Date" label to `newest`). When `min_score` is set, leads with `overall == null` are excluded.
* **DECISION-D8 (EvidenceItem UUID generation for AI citations):**
  * *Affects:* WS2, WS3.
  * *Resolution:* During discovery/assessment, WS2 first upserts the `Lead` and its `lead_evidence` rows into PostgreSQL to generate real UUIDs, then passes those persisted `EvidenceItem` objects (with `id` populated) to `AIService.assess_lead()`.
* **DECISION-D9 (Duplicate lead resolution):**
  * *Affects:* WS2, WS3.
  * *Resolution:* Add `possible_duplicate_of_domain: str | None = None` to `LeadCandidate`. WS2 resolves that domain to the primary lead's `id` and stores it in `lead.duplicate_of`.
* **DECISION-D10 (Retry isolation & timeouts):**
  * *Affects:* WS2, WS3.
  * *Resolution:* WS3 handles per-call retries (max 2) and runs Tavily extractions concurrently (`asyncio.gather` with semaphore). WS2 does not re-retry inside a stage except once on a transient stage crash. `RUN_MAX_SECONDS` measures active execution time only (excludes time spent in `awaiting_review`).
* **DECISION-D11 (Outreach status sync to lead review):**
  * *Affects:* WS1, WS2.
  * *Resolution:* WS2 handles this atomically on the backend inside `PATCH /outreach-drafts/{id}`: when `draft.status` becomes `"contacted"`, WS2 updates the parent `lead.review_status = "contacted"`.
* **DECISION-D12 (Product deletion cascade):**
  * *Affects:* WS1, WS2.
  * *Resolution:* `DELETE /products/{id}` cascades with a clear confirmation dialog in WS1. Editing a product never mutates historical runs or leads.
* **DECISION-D13 (Market hypothesis status & taste affinity):**
  * *Affects:* All workstreams.
  * *Resolution:* `MarketHypothesis.status` enum is `proposed | confirmed | rejected` (default `proposed`). In backend runs without a live Qloo key, WS2 keeps `lead.cultural_affinity = null` (mock taste signals attach to anchors/hypotheses with `is_demo: true`). WS1 unit tests and mocks may pass a mock `cultural_affinity` object with `is_demo: true` to test the UI component.
* **DECISION-D14 (Three-dimension label wire format):**
  * *Affects:* All workstreams.
  * *Resolution:* Wire format is strictly `high | medium | low | unknown` across all 3 dimensions (`category_fit`, `aesthetic_fit`, `seller_compat`). WS2 maps `high -> 100, medium -> 60, low -> 20, unknown -> null` (and defensively accepts `match/adjacent/mismatch` aliases).
* **DECISION-D15 (Taste provider sequencing & two-phase review):**
  * *Affects:* WS1, WS2, WS3.
  * *Resolution:* (1) Before `awaiting_review` (`anchor_proposal` stage): Task B generates `ai_proposed` anchors (`status: proposed`) and initial hypotheses; WS2 calls `get_taste_provider().search_entities()` on candidate labels so entity matches are visible during review. (2) On `confirm-anchors`: for all `confirmed` anchors, WS2 resolves missing entity IDs, calls `get_insights()`, attaches returned signals to `market_hypotheses`, and initiates `ResearchPipeline.run()`.
* **DECISION-D16 (Seller profile endpoints):**
  * *Affects:* WS1, WS2.
  * *Resolution:* Add `GET /api/v1/profile` and `PUT /api/v1/profile` (authenticated by JWT; auto-creates an empty profile row on first `GET` if none exists).
* **DECISION-D17 (Outreach drafts listing endpoint):**
  * *Affects:* WS1, WS2.
  * *Resolution:* Add `GET /api/v1/outreach-drafts` supporting optional query params `status`, `product_id`, `lead_id` (returns `OutreachDraft[]` ordered by `updated_at desc`).
* **DECISION-D18 (Product image management):**
  * *Affects:* WS1, WS2.
  * *Resolution:* `Product.images` is `list[str]` (array of public or signed URLs). `POST /products/{id}/images` accepts `multipart/form-data`, uploads to storage, and returns updated `images: list[str]`. Removing or reordering images is performed via `PUT /products/{id}`.
* **DECISION-D19 (AI product attribute suggestions):**
  * *Affects:* WS1, WS3.
  * *Resolution:* `ProductAttributes` always returns `style[], materials[], motifs[], colours[], price_segment, target_retailer_types[], uncertain_fields[], assumptions[]`, plus optional fields when explicitly mentioned.
* **DECISION-D20 (Timestamps & draft lineage):**
  * *Affects:* WS1, WS2.
  * *Resolution:* Include `created_at` on `ResearchRun` and `Lead`, and `parent_draft_id: UUID | None` + `updated_at` on `OutreachDraft`.

</div>

---

## 12. Debugging playbook: symptom -> where to look first

<div align="justify">

* **Field is `undefined` in UI:**
  * *Likely Layer:* WS1 / WS2.
  * *First Check:* Check raw network JSON against `contracts/`. Look for `camelCase` vs `snake_case` drift or a Pydantic response model dropping a field.
* **Works on mocks, breaks on real backend:**
  * *Likely Layer:* WS1 mocks.
  * *First Check:* Diff `frontend/src/mocks/` against `/openapi.json`. Fix the mock to match the contract, not the UI component.
* **`422 validation_error` on submit:**
  * *Likely Layer:* WS1 / WS2.
  * *First Check:* Compare request payload against Zod schema and FastAPI Pydantic model (`error.details`).
* **`401 unauthorized` on every API call:**
  * *Likely Layer:* Config / Auth.
  * *First Check:* Check `VITE_SUPABASE_URL` matches backend `SUPABASE_URL`, verify `SUPABASE_JWT_SECRET`, and ensure `Authorization: Bearer <access_token>` is sent.
* **Newly created record returns `404`:**
  * *Likely Layer:* WS2.
  * *First Check:* Background job or insert forgot to set `owner_id = current_user.id`, or RLS policy is blocking read.
* **Score bar shows `0` instead of `"Not enough evidence"`:**
  * *Likely Layer:* Any.
  * *First Check:* A `null` score was coerced to `0` (`x or 0`, `value || 0`, or fallback formatting).
* **Crash or `null` on `seller_compat` score:**
  * *Likely Layer:* WS2 / WS3.
  * *First Check:* Check D14: ensure both layers use `high / medium / low / unknown`.
* **Demo badge missing on mock outputs:**
  * *Likely Layer:* WS2 / WS1.
  * *First Check:* `is_demo` was stripped by a Pydantic response model or ignored by the component.
* **Run stuck in `awaiting_review` after clicking Continue:**
  * *Likely Layer:* WS1 / WS2.
  * *First Check:* Check if `POST /research-runs/{id}/confirm-anchors` succeeded (needs `>= 1` confirmed anchor or `proceed_without_anchors: true`).
* **Duplicate leads visible in table:**
  * *Likely Layer:* WS3 / WS2.
  * *First Check:* Check canonical domain normalisation, `www.` stripping, public-suffix handling, and `(owner_id, product_id, canonical_domain)` upsert logic.

</div>

---

## 13. Integration timeline and checkpoints

<div align="justify">

* **Contract Freeze (Day 1 - first 90 min):** Confirm `contracts/` v0.1 schemas, resolve Section 11 (D1 to D20) in `docs/decisions.md`, select UI library for WS1, confirm DB driver for WS2.
* **End of Day 1 (Day 1 EOD):** WS1 runs on mocks (`VITE_USE_MOCK=true`) with shell, Dashboard, and Product Passport form. WS2 serves `/health`, `/integrations/status`, `/openapi.json`, and contract-shaped stub routes. WS3 commits interfaces, factories, and labelled fixtures in `fixtures/`. App runs end-to-end with zero secret keys.
* **Checkpoint 1 (Day 2 EOD):** Real Auth + Products CRUD + Image upload working between WS1 and WS2. WS3 Task A (`structure_product`), Task B (`plan_research`), and `MockTasteProvider` integrated. Runs reach `awaiting_review` and anchors can be reviewed.
* **Checkpoint 2 (Day 3 EOD):** Full pipeline working: Confirm anchors -> Tavily discovery (live or fixture) -> Evidence persistence -> Task C (`assess_lead`) -> Deterministic scoring & tiering -> Buyer Leads UI -> Task D (`draft_outreach`) -> Outreach Studio UI.
* **Hardening & Demo (Day 4):** Failure-injection tests (invalid JSON, timeouts, empty Tavily, hostile webpage excerpt), RLS isolation test matrix, 20-30 retailer eval run, Playwright smoke test, `docs/readiness.md`.
* **Live Key Activation:** Real provider enabled behind `get_taste_provider()` per runbook; WS2 sets API keys (`taste: live`); WS1 verifies real signals render while old demo runs stay badged demo data.

</div>

---

## 14. How an LLM must behave in this repository

1. **Identify your workstream first** (`WS1`, `WS2`, or `WS3`)[cite: 1]. Never modify files owned by another workstream without explicit user instruction[cite: 1].
2. **Inspect before assuming:** Check `contracts/`, `docs/decisions.md`, and existing repo files before writing code[cite: 1].
3. **Never break the contract silently:** If you need a new field, endpoint, or enum change, state it explicitly and propose a `contracts/` update[cite: 1].
4. **Enforce the truth & safety rules automatically:**
   - Preserve `unknown` -> `null` -> `"Not enough evidence"`[cite: 1, 2, 3, 4].
   - Preserve `is_demo: true` -> `<DemoBadge/>`[cite: 1, 2, 3, 4].
   - Never add PayPal, payment code, or email-sending functionality[cite: 1, 2, 3, 4].
   - Never put backend API keys into frontend files or logs[cite: 1, 2, 3, 4].
5. **Report clearly after every task:** List files changed, tests run (and actual pass/fail output), any environment variables added (names only), and any hand-off notes for the other two workstreams[cite: 1].

---

## 15. How each teammate should write their own `skills.md`

Each developer (WS1, WS2, WS3) should create a workstream-specific `skills.md` (e.g., `frontend/skills.md`, `backend/app/skills.md`, `backend/ai/skills.md`) for their LLM[cite: 1].
**Golden rule:** Never copy enum lists, scoring weights, or API tables into `skills.md` (they will drift from `contracts/`)[cite: 1]. Instead, point to `contracts/` and `AGENT.md`, and use `skills.md` **only** for local operational recipes[cite: 1]:

- **WS1 (`frontend/skills.md`) should contain:**
  - Exact dev/test/lint commands (`npm run dev`, `npm run test`, `npx playwright test`)[cite: 1, 3].
  - The chosen UI component library rules (e.g., shadcn/ui conventions, theme token names, how to use `<DemoBadge/>`, `<ProvenanceTag/>`, `<ScoreBar/>`)[cite: 1, 3].
  - How to add a new API hook in `frontend/src/api/` and its matching mock handler in `frontend/src/mocks/` using `VITE_USE_MOCK`[cite: 1, 3].
- **WS2 (`backend/app/skills.md`) should contain:**
  - Exact commands to run FastAPI, pytest, and database migrations[cite: 1, 2].
  - The chosen DB pattern (SQLAlchemy 2 async session or `supabase-py`), the `current_user()` JWT dependency pattern, and the mandatory `owner_id` query filter pattern[cite: 2].
  - How the background job runner polls/transitions `research_runs` and updates `heartbeat_at`[cite: 2].
- **WS3 (`backend/ai/skills.md`) should contain:**
  - Exact commands to run offline fixture unit tests (`pytest -m "not live"`) vs. live API tests, plus `python eval/run_eval.py`[cite: 1, 4].
  - The confirmed Nebius `model_id`, base URL, JSON-mode settings, and prompt template versioning convention in `backend/ai/prompts/`[cite: 1, 4].
  - How the validation + 1-repair-retry wrapper and claim-checker work (`evidence_ids` verification for Task C, `facts_used` verification for Task D, and prompt-injection delimiters for scraped Tavily excerpts)[cite: 4].
