# Architecture Decisions & Contract v0.2 Log (`docs/decisions.md`)

This document records the foundational architecture decisions, technology selections, and cross-workstream contracts agreed upon across WS1 (Frontend & UX), WS2 (Backend, Data & Workflow), and WS3 (AI & Research Integrations).

---

## 1. Contract v0.2 Overview

- **Contract Precedence:**
  1. `contracts/` schemas (Pydantic v2 schemas and TypeScript definitions)
  2. Workstream specifications (`docs/WS2_Spec.md`, etc.)
  3. `AGENT.md` integration contract
- **Key Enhancements in Contract v0.2:**
  - Full support for live Qloo cultural-affinity integration (`CulturalAffinity` schema, `taste_anchor.source = qloo`, `provider_calls` audit logging).
  - Strict preservation of the `unknown -> null -> "Not enough evidence"` chain across all layers.
  - Strict preservation of the `is_demo: true -> <DemoBadge/>` lineage across all layers.
  - Full `snake_case` wire serialization for all JSON models, query params, and enums.

---

## 2. Technical Stack & Backend Architecture Choices

### 2.1 Database & ORM: SQLAlchemy 2.0 (Async)
- **Decision:** Use SQLAlchemy 2.0 with asynchronous engine (`create_async_engine`) and `async_sessionmaker[AsyncSession]`.
- **Driver:** `asyncpg` for PostgreSQL production/Supabase instances, with test isolation support via transactions or SQLite async (`aiosqlite`) during offline testing.
- **Migrations:** Sequential raw SQL migration scripts committed in `backend/app/db/migrations/` (`001_initial_schema.sql`, etc.), ensuring full portability and alignment with Supabase SQL editor / CLI.

### 2.2 Background Job Runner: In-Process Asynchronous Runner
- **Decision:** Implement an in-process asynchronous runner using asyncio worker tasks and PostgreSQL rows as the sole source of truth.
- **Rationale:** Keeps Day 1–4 deployment lightweight and self-contained with zero Celery/Redis infrastructure requirements, while preserving a clean decoupled state machine where every status and stage transition is immediately committed to PostgreSQL. Moving to a dedicated queue in a future phase requires zero API or schema modifications.

---

## 3. Resolved Cross-Workstream Decisions (`DECISION-D1` through `DECISION-D20`)

### DECISION-D1: Integration State Enum & `is_demo` Flag Lineage
- **Resolution:** Use `live | mock | pending | disabled` everywhere for integration status.
- **Lineage:** Explicitly add `is_demo: bool = False` to `Lead`, `EvidenceItem`, and `OutreachDraft` models so demo/fixture flags survive all serialization hops to the frontend.

### DECISION-D2: Run-Lead Associations on Rerun & Conflict Merge
- **Resolution:** When a rerun encounters a conflict on `(owner_id, product_id, canonical_domain)`, update `leads.run_id` to the latest `run_id` (and merge new evidence), ensuring that `GET /leads?run_id=<new_run>` reliably returns all leads discovered or refreshed in that run.

### DECISION-D3: Custom Anchor Creation Endpoint
- **Resolution:** Implement `POST /api/v1/research-runs/{id}/anchors` accepting `{label, entity_type, rationale?}`. Creates an anchor row with `source="user_added"`, `status="confirmed"`, and `is_demo=False`.

### DECISION-D4: Anchor Confirmation Request Body
- **Resolution:** `POST /api/v1/research-runs/{id}/confirm-anchors` accepts an optional JSON payload `{"proceed_without_anchors": bool}` (defaults to `false`). If `false`, requires at least one confirmed anchor.

### DECISION-D5: Outreach Draft Warnings Field
- **Resolution:** Include `warnings: list[str] = []` in the `OutreachDraft` Pydantic model and `warnings jsonb DEFAULT '[]'` in the `outreach_drafts` PostgreSQL table to capture model fact-checking alerts.

### DECISION-D6: Lead Tier Reasons and Evidence Definitions
- **Resolution:**
  - Add `tier_reasons: list[str] = []` inside `LeadScores` (`lead.scores`).
  - **Retail-activity evidence** is defined as at least one `EvidenceItem` with `source_type` in `("official_site", "product_page")`.
  - **Location/contact verified** is defined as non-null `lead.location` or verified contact/location details cited in an evidence excerpt.

### DECISION-D7: Standardized Lead Pagination, Sorting & Filtering
- **Resolution:**
  - `GET /api/v1/leads` returns a paginated envelope: `{items: list[Lead], total: int, page: int, page_size: int}`.
  - Standardize sort keys on `score_desc | name | newest` (UI maps "Date" to `newest`).
  - Add optional `location: str` query parameter.
  - When `min_score` filter is specified, leads with `overall == null` are excluded.

### DECISION-D8: Evidence UUID Generation Ordering
- **Resolution:** During discovery and assessment, WS2 **first** upserts the `Lead` and its `lead_evidence` rows into PostgreSQL to generate persistent database UUIDs. **Then**, WS2 passes those persisted `EvidenceItem` objects with valid UUID `id`s to `AIService.assess_lead()`, ensuring model citations match real database IDs.

### DECISION-D9: Secondary Duplicate Match Handling
- **Resolution:** Add `possible_duplicate_of_domain: str | None = None` to `LeadCandidate`. WS2 resolves that domain to the primary lead's UUID and stores it in `lead.duplicate_of`. The UI renders a "Possible duplicate" badge linking to the primary lead.

### DECISION-D10: Bounded Retries & Active Execution Timer
- **Resolution:**
  - WS3 handles per-call retries (max 2) with exponential backoff and jitter, and executes Tavily extractions concurrently with an `asyncio.Semaphore`.
  - WS2 does not re-retry within a stage except once on transient process crashes.
  - `RUN_MAX_SECONDS=600` strictly measures active execution time and **excludes** time spent waiting for seller review in `awaiting_review`.

### DECISION-D11: Atomic Outreach Contacted Status Sync
- **Resolution:** When `PATCH /api/v1/outreach-drafts/{id}` updates a draft's status to `"contacted"`, WS2 atomically updates the parent lead's review status: `lead.review_status = "contacted"`.

### DECISION-D12: Product Mutation Cascading & Historical Immutability
- **Resolution:**
  - `DELETE /api/v1/products/{id}` cascades to related runs, anchors, hypotheses, leads, evidence, and drafts.
  - Updating a product via `PUT /api/v1/products/{id}` mutates product metadata only and **never** mutates historical research runs or existing lead records.

### DECISION-D13: Market Hypothesis Status Enum & Mock Cultural Affinity
- **Resolution:**
  - `MarketHypothesis.status` enum values are `proposed | confirmed | rejected` (default `proposed`).
  - In runs without a live Qloo key, WS2 stores `lead.cultural_affinity = null` (mock taste signals attach to anchors/hypotheses with `is_demo: true`).

### DECISION-D14: Unified Dimension Label Wire Enum
- **Resolution:**
  - Wire format is strictly `high | medium | low | unknown` across all three dimensions (`category_fit`, `aesthetic_fit`, `seller_compat`).
  - WS2 maps `high -> 100`, `medium -> 60`, `low -> 20`, `unknown -> null`.
  - Aliases (`match`, `adjacent`, `mismatch`) are defensively accepted by WS2 parsers if received.

### DECISION-D15: Unified Taste Proposal & Resolution Flow
- **Resolution:**
  1. *Before `awaiting_review` (`anchor_proposal` stage):* AI Task B generates `ai_proposed` anchors (`status: proposed`) and initial hypotheses. WS2 queries `get_taste_provider().search_entities()` to attach entity candidates so matches are visible during review.
  2. *On `confirm-anchors`:* For all `confirmed` anchors (including user additions), WS2 calls `get_taste_provider().get_insights()`, attaches returned signals to `market_hypotheses`, and passes confirmed anchors into `ResearchPipeline.run()`.

### DECISION-D16: Seller Profile Endpoints
- **Resolution:** Implement `GET /api/v1/profile` and `PUT /api/v1/profile` authenticated via Supabase JWT. Auto-creates an initial profile record on the first `GET` if one does not exist.

### DECISION-D17: Global Outreach Drafts Listing Endpoint
- **Resolution:** Implement `GET /api/v1/outreach-drafts` supporting optional query parameters `status`, `product_id`, and `lead_id`, returning `list[OutreachDraft]` ordered by `updated_at desc`.

### DECISION-D18: Product Image Storage & Management
- **Resolution:**
  - `Product.images` is `list[str]` (public/signed URLs).
  - `POST /api/v1/products/{id}/images` accepts `multipart/form-data` (`file`), uploads the asset to storage, appends the URL to `Product.images`, and returns the updated array.
  - Reordering or removing images is performed by sending the updated array via `PUT /api/v1/products/{id}`.

### DECISION-D19: AI Task A Product Attributes Output Model
- **Resolution:** `ProductAttributes` returns core lists (`style`, `materials`, `motifs`, `colours`, `price_segment`, `target_retailer_types`, `uncertain_fields`, `assumptions`), plus optional fields (`category`, `price_min`, `price_max`, `currency`, `moq`, `monthly_capacity`) populated when explicitly identified in the seller's input text.

### DECISION-D20: Persistent Timestamps & Outreach Lineage Fields
- **Resolution:**
  - Add `created_at` timestamp to `ResearchRun` and `Lead`.
  - Add `parent_draft_id: UUID | None` and `updated_at: datetime` to `OutreachDraft` to support version history navigation.

### DECISION-D21: Complete Removal of AG Studio & Insights in Favor of Lean Maker Workbenches
- **Resolution:**
  - Excised `ag-studio` and `ag-studio-react` packages, related navigation links, routes (`/app/insights`), and mock analytics canvases.
  - Vitrine focuses exclusively on core maker-led workflows: Product Passport, Market Discovery, Buyer Leads, and Outreach Studio.
  - Eliminates developer-dashboard bloat and heavy third-party canvas bundles in favor of lean, responsive, craft-focused UI.

### DECISION-D22: Centralized Viewport-Centered Portal Modal Architecture
- **Resolution:**
  - Resolved CSS transform containing-block bug where ancestor animations (`@keyframes enter-up`) trapped `position: fixed` modals inside scrollable containers. Concluded `@keyframes enter-up` at `transform: none`.
  - Built centralized `Modal.tsx` and `ConfirmationModal.tsx` rendering exclusively via `createPortal(..., document.body)` with keyboard focus trapping, background scroll-lock (`document.body.style.overflow = 'hidden'`), and native `Escape` key handling.
  - Migrated all application dialogs (Product deletion, Lead rejection, Outreach regeneration, AI extraction, New Run, Onboarding) to this shared component.

### DECISION-D23: Production Safeguard Against Silent Fixture Fallbacks
- **Resolution:**
  - When running in production (`APP_ENV=production` or `APP_ENV=prod`), if `QLOO_API_KEY` or `NEBIUS_API_KEY` are unset or empty, the backend must **not** silently fall back to `FixtureResearchPipeline` or `FixtureAIService`.
  - Missing credentials in production immediately raise `AppError("upstream_unavailable", ..., status_code=503)` or `AppError("ai_generation_failed", ..., status_code=503)`.
  - Offline development and testing (`APP_ENV=dev` or `APP_ENV=test`) continue to support fixture fallbacks.

### DECISION-D24: Multi-Currency Pricing & Honest Initial States
- **Resolution:**
  - Added multi-currency selector (`USD`, `EUR`, `GBP`) to the Product Passport form.
  - Eliminated arbitrary prepopulated price defaults ("85", "140") and default mock imagery in favor of clean, honest empty states.
  - Enabled direct "Start Discovery" creation from product cards.

### DECISION-D25: Purge of Demo Data & Demo Badges from User-Facing Surfaces
- **Resolution:**
  - Removed demo badges, demo login pills, and hardcoded demo credentials across the frontend application.
  - Removed fictional match scores (`92/100`) and fake retailer names from the public landing page walkthrough to maintain 100% evidence-grounded credibility.

