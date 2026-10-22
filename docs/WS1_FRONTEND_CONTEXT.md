# WS1 Frontend & UX Context

This document complements, not replaces, `AGENT.md`, `contracts/schemas.py`, `openapi.json` and `docs/decisions.md`. The current contract/schema wins if an older copied spec differs.

## Mission and ownership
Build a complete React + TypeScript app for seller profile, Product Passport, retailer discovery, anchor review, evidence-backed Buyer Leads and Outreach Studio. WS1 owns `frontend/**`, UI, routes, forms/tables, design system, typed API client, isolated mock layer, loading/empty/error states, responsiveness and accessibility. WS1 does not own backend endpoints/auth rules, scoring math, prompts, model calls or provider clients.

## Priority and routes
Priority order: **Product Passport → Market Discovery/anchor review → Buyer Leads → Outreach Studio → lean Dashboard → auth/session integration.**
Routes: `/login`, `/signup`, `/`, `/products`, `/products/new`, `/products/:id`, `/discovery`, `/discovery/:runId`, `/leads`, `/leads/:id`, `/outreach`, `/outreach/:leadId`. Use a desktop sidebar and mobile drawer/bottom navigation, highlight active routes and provide a friendly not-found page.

## Product Passport
Create/edit/delete with confirmation and reload. Fields: name, category, description, materials, style, motifs, colours, price_segment, price_min/max, currency, moq, monthly_capacity, target_retailer_types and multiple images with previews/removal. The WS1 spec says name 2–80 chars, category/description required, at least one material, positive prices, price_min ≤ price_max, MOQ integer ≥ 1, monthly_capacity ≥ MOQ (warn, not block, if lower); verify exact request schemas before implementation. `POST /products/extract-profile` suggestions must be reviewed field-by-field and never auto-saved. Extraction errors preserve unsaved form values. Product list includes search, thumbnail, category, segment, MOQ, empty state and Start research action.

## Market Discovery
Choose product plus optional regions, retailer types and notes; create a run with `Idempotency-Key`. Poll `GET /research-runs/{id}` every 2–3 seconds only while `queued` or `running`. Show all contract states/stages, elapsed time and failures. For `awaiting_review`, show anchors with source/provenance; support confirm, reject, edit, custom anchor and Continue using the actual contract. Display hypotheses/signals and links to leads. Empty/weak signals must be stated plainly, never replaced with invented data. Reruns keep old runs in history.

## Buyer Leads
Search/filter/sort/paginate per actual backend query contract. Show name, location, safe website link, retailer type, tier, priority score/completeness, review status and evidence count. Save/reject/note/open outreach; optimistic updates roll back on failure. If `duplicate_of` exists, mark “Possible duplicate” and link to the primary. Detail shows score dimensions/reasons, unknowns, evidence, site verification/date and cultural affinity separately. Say **priority score**, never likelihood to buy/probability/conversion. Null/unknown scores display “Not enough evidence”, never zero.

## Outreach Studio
Generate draft, edit subject/body, PATCH edits, inspect versions, show `facts_used`/source links/warnings, copy and manually track status. No email-sending capability and no Send button. Copying does not mean contacted.

## Dashboard and shared components
Dashboard is lean: data-derived counts, recent runs, quick links; visibly label mock/sample data and support zero records. Shared components: `DemoBadge`, `ProvenanceTag`, `StatusStepper`, `ScoreBar`, `EvidenceCard`, `EmptyState`, `ErrorState`, `LoadingSkeleton`, `IntegrationBanner`.

## Mock layer
Views call feature hooks/API modules, never fixtures directly. `VITE_USE_MOCK` switches adapter without component edits. Mock shapes match the actual contract: snake_case, exact enums, null/provenance and `is_demo`. Simulate 300–800 ms latency and occasional failure. Include completed/running/failed/no-results, weak/unknown evidence and duplicate lead cases. Mock anchors use `source: "demo"`, never pretend to be Qloo.

## Done means
Product CRUD/reload; AI suggestion success/invalid-output/timeout preserving form; all run states/rerun; anchor review; lead filters/actions/details/evidence/duplicates; null/demo states; draft edits/versions/copy/manual status; loading/empty/error states; responsive and keyboard/a11y pass; switching mock to live needs no view changes; no secret leakage, payments or sending.
