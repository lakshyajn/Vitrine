# Frontend & Backend Integration Handoff (`docs/frontend-backend-handoff.md`)

This document records the completed WS1 Frontend architecture, endpoints integration status, and contracts alignment for the Vitrine wholesale platform.

---

## 1. Workstream Status Summary

- **Frontend Core:** Complete, typed, tested, and building for production with Vite 6 + React 18 + Tailwind CSS.
- **Contract Fidelity:** 100% compliant with `contracts/schemas.py`, `openapi.json`, and `docs/decisions.md` (Contract v0.2).
- **Public Landing Page (`/`):** Frozen, fully approved, editorial boutique art direction with restored native cursor, Vermilion `#CF1E1E` CTAs, and interactive product walkthrough.
- **Workspace Routes (`/app/*`):** Fully operational across all 5 core workbenches:
  - **Overview Dashboard (`/app`):** Lean, data-derived metrics and provider status banner (`IntegrationBanner`).
  - **Product Passport (`/app/products`, `/app/products/new`, `/app/products/:id`):** CRUD, image upload, and AI Attribute Extraction (`ExtractProfileModal`) with field-by-field accept/reject review.
  - **Market Discovery (`/app/discovery`, `/app/discovery/:runId`):** Run initiation, status stepper, polling every 2.5s during `queued`/`running`, and interactive Taste Anchor Review panel (`POST /research-runs/{id}/confirm-anchors`).
  - **Buyer Leads (`/app/leads`, `/app/leads/:id`):** Paged filtering, sorting, tier breakdown, priority fit score (`ScoreBar` with "Not enough evidence" for unknown scores), domain verification, and secondary duplicate markers (`duplicate_of`).
  - **Outreach Studio (`/app/outreach`, `/app/outreach/:leadId`):** Evidence-grounded drafting, facts-used inspector, version history, copy actions, and manual status tracking (`draft → ready → contacted`). Atomic synchronization to parent lead review status on contacted status update.
  - **AG Studio Insights (`/app/insights`):** Read-only data intelligence across pipeline tiers, boutique territory footprint, and channel format yield.
  - **Auth Integration (`/login`, `/signup`):** Branded artisan sign-in with instant demo access.

---

## 2. API Endpoints Map & Implementation Status

| Feature Area | HTTP Method & Path | Wire Contract & Request Model | Response Model / Types | Integration Mode (`VITE_USE_MOCK`) |
|---|---|---|---|---|
| **Health** | `GET /api/v1/health` | None | `{ status: "ok" }` | Live / Handled |
| **Integrations** | `GET /api/v1/integrations/status` | None | `IntegrationStatusResponse` | Live via client / Mock fallback |
| **Profile** | `GET /api/v1/profile`<br>`PUT /api/v1/profile` | `ProfileUpdate` | `Profile` | In-memory mock & Supabase JWT client |
| **Product Passport** | `GET /api/v1/products`<br>`POST /api/v1/products`<br>`GET /api/v1/products/{id}`<br>`PUT /api/v1/products/{id}`<br>`DELETE /api/v1/products/{id}`<br>`POST /api/v1/products/{id}/images` | `ProductCreate`<br>`ProductUpdate`<br>`multipart/form-data` | `Product`<br>`list[Product]`<br>`list[str]` (images) | Full session mock mutations & API client |
| **AI Task A** | `POST /api/v1/products/extract-profile` | `ExtractProfileRequest` | `ProductAttributes` | Supported in `ExtractProfileModal` |
| **Market Discovery** | `GET /api/v1/research-runs`<br>`POST /api/v1/research-runs`<br>`GET /api/v1/research-runs/{id}`<br>`POST /api/v1/research-runs/{id}/rerun` | `CreateResearchRunRequest` | `ResearchRun`<br>`list[ResearchRun]` | Full state machine support with polling |
| **Taste Anchors** | `GET /api/v1/research-runs/{id}/anchors`<br>`POST /api/v1/research-runs/{id}/anchors`<br>`PATCH /api/v1/taste-anchors/{id}`<br>`POST /api/v1/research-runs/{id}/confirm-anchors` | `CreateAnchorRequest`<br>`UpdateAnchorRequest`<br>`ConfirmAnchorsRequest` | `TasteAnchor`<br>`list[TasteAnchor]` | Interactive review panel & resumption |
| **Hypotheses** | `GET /api/v1/research-runs/{id}/hypotheses` | None | `list[MarketHypothesis]` | Qloo cultural vectors & Tavily extraction signals |
| **Buyer Leads** | `GET /api/v1/leads`<br>`GET /api/v1/leads/{id}`<br>`PATCH /api/v1/leads/{id}`<br>`GET /api/v1/leads/{id}/evidence` | `UpdateLeadRequest` (status, notes)<br>QueryParams: `product_id`, `run_id`, `tier`, `review_status`, `min_score`, `location`, `q`, `sort`, `page`, `page_size` | `LeadPagedResponse`<br>`Lead`<br>`list[EvidenceItem]` | Paged filtering with optimistic status updates |
| **Outreach Studio** | `GET /api/v1/outreach-drafts`<br>`GET /api/v1/leads/{id}/outreach-drafts`<br>`POST /api/v1/leads/{id}/outreach-drafts`<br>`GET /api/v1/outreach-drafts/{id}`<br>`PATCH /api/v1/outreach-drafts/{id}`<br>`POST /api/v1/outreach-drafts/{id}/regenerate` | `UpdateOutreachDraftRequest` | `OutreachDraft`<br>`list[OutreachDraft]` | Grounded facts used, copy actions, manual status |

---

## 3. Data Integrity & Hard Constraints Enforcement

1. **Strictly No Email Sending:** No automated send actions, SMTP connections, or Send buttons. Pitch correspondence is copyable (`Copy Full Email Pitch`, `Copy Subject`, `Copy Body`) and manually tracked.
2. **Strictly No Payment UI:** No checkout flows, payment gateways, invoices, or billing mechanisms.
3. **Preservation of Null Scores:** Unknown or incomplete evidence strictly renders as `"Not enough evidence"`, never coerced to zero or false negative findings.
4. **Lineage of `is_demo`:** Sample and demonstration records preserve `is_demo: true` and visibly render `<DemoBadge label="Demo data" />`.
5. **Plain Text Web Citations:** Web excerpt citations are strictly rendered as sanitized plain text, never using `dangerouslySetInnerHTML`. External links enforce `target="_blank" rel="noopener noreferrer"`.
6. **Maker Control:** AI Task A extraction suggestions require field-by-field acceptance and are never silently auto-saved.

