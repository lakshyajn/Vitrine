VITRINE
Workstream 2
Backend, Data & Workflow
The spine of Vitrine: data, security, research-run orchestration and transparent lead scoring.
Item	Detail
Owner	Backend Engineering Team
Window	Days 1–4 parallel build, plus the Qloo activation work now that the API key has arrived
Scope rule	The Qloo API key has arrived, so real cultural-affinity integration is now in scope. It plugs into the interfaces already built. PayPal remains out of scope.
Contract version	v0.2: v0.1 plus the Qloo-live additions listed in Appendix A.9. Changes need a pull request reviewed by all three owners.
Companion files	WS1 Frontend & UX  |  WS2 Backend, Data & Workflow  |  WS3 AI & Research Integrations

0. Your mission in one page
You build the server that stores everything, protects each seller’s data, and runs the research workflow end to end. By the end of Day 4 a seller can create a product, start a run, have it progress through persisted stages, and read back leads with evidence, scores and outreach drafts, all from a database and not from memory.
You own	You do not touch
backend/app/ (API, DB, auth, jobs, scoring)
Supabase project, migrations, row-level security
Research-run state machine and background runner
Lead scoring and tiering
/integrations/status and configuration
Persistence of AI, Tavily and Qloo outputs	React code (WS1)
Prompts, Nebius calls, Tavily calls, Qloo client (WS3). You call them through the interfaces in Appendix A.6
Model-quality tuning. Report problems to WS3

Unblock the others early
Your first deliverable, due end of Day 1, is a running server whose endpoints exist and return contract-shaped stub data. WS1 can then point at real URLs on Day 2 instead of waiting for Day 3 logic.

1. How the three workstreams fit together
The original roadmap has eight phases. To let three people work at the same time without blocking each other, the work is split by layer, not by phase. Each workstream codes against an agreed contract (Appendix A) and uses fixtures or stubs for whatever the other two have not finished yet.
#	Workstream	Owns	Main stack
1	Frontend & UX	Every screen, navigation, design system, forms, tables, loading/empty/error states, typed API client, and the dedicated mock-data layer.	React + TypeScript
2	Backend, Data & Workflow	FastAPI app, Supabase/PostgreSQL schema, auth and per-user authorization, CRUD, research-run lifecycle and job runner, lead scoring, outreach endpoints, integration-status endpoint.	Python, FastAPI, Supabase
3	AI & Research Integrations	Nebius/Nemotron client and the four AI tasks, Tavily retailer-research pipeline, evidence validation and deduplication, Qloo adapter and mock provider, evaluation set.	Python, Pydantic, Tavily, Nebius

You are Workstream 2
Read your own section in full. Skim the other two only where the Hand-offs table points at them. Everything you need from the other owners is in Appendix A.

1.1 Phase-to-workstream map
Roadmap phase	WS1	WS2	WS3
Phase 1: Product scope and demo scenario	Shared	Shared	Shared
Phase 2: Frontend	Owner	API support	-
Phase 3: Backend and database	Consumer	Owner	-
Phase 4: Nemotron via Nebius	Displays results	Calls the service	Owner
Phase 5: Tavily pipeline	Displays results	Persists + orchestrates	Owner
Phase 6: Qloo integration (key received)	Anchor-review UI, real-signal display	Config, caching, persistence	Real adapter (owner), mock kept for tests
Phase 7: Lead ranking	Detail panel UI	Scoring (owner)	Provides assessment labels
Phase 8: Outreach	Outreach Studio UI	Endpoints + versions	Draft generation (owner)

1.2 Team sync points
When	What happens	Output
Day 1, first 60–90 min	Contract meeting. Walk through Appendix A, resolve disagreements, choose the shared repo layout.	Contract v0.1 committed to contracts/. Nobody renames fields afterwards without a PR.
End of Day 1	Quick demo from each owner.	WS1 runs against mocks. WS2 serves /health and stub endpoints. WS3 has the service interfaces, schemas and fixtures.
End of Day 2	Integration checkpoint 1.	Products CRUD works end to end. Structured product extraction and research planning return validated data.
End of Day 3	Integration checkpoint 2.	Product → research run → leads with evidence → assessment → outreach draft, using Tavily live or fixtures.
Day 4	Hardening and rehearsal.	Failure-case tests, evaluation-set results, readiness report, demo rehearsal with the fixed scenario.
Qloo key arrived (now)	Qloo activation: WS3 builds the real client from official docs, WS2 enables config, caching and persistence, WS1 verifies real signals display honestly. See section 1.4.	Real cultural-affinity signals in an already working app, plus a findings note on what Qloo can and cannot do for home textiles.

1.3 Ground rules for everyone
•	Contract first. If a field, enum or endpoint is not in Appendix A, ask before inventing it. Proposed changes go in a pull request that all three owners review.
•	No secrets in the frontend. Nebius, Tavily and Qloo keys live only in backend environment variables.
•	Demo data is always labelled. Anything from a mock or fixture carries is_demo: true and the UI shows a visible “Demo data” badge. Never present it as a Qloo result, and never label a real Qloo result as demo.
•	Protect the Qloo key. It lives only in the backend environment (QLOO_API_KEY). Never commit it, paste it into chat or tickets, log it, or put it in fixtures. If it leaks, request a new one immediately.
•	Never invent facts. No fabricated retailers, URLs, Qloo identifiers or statistics. Unknown stays unknown.
•	Missing evidence is not a negative result. Use unknown or null, never low or 0, when there is simply no data.
•	No PayPal. No SDK, payment API, invoice, webhook or PayPal-specific component anywhere.
•	No automatic email sending. Outreach is draft, edit, copy and manual status tracking only.
•	Small, frequent pull requests. Merge to main at least twice a day so integration problems show up early. Branch names: ws1/..., ws2/..., ws3/....
•	Do not over-polish. Product Passport, Market Discovery and Buyer Leads demonstrate the core value. They come before dashboard polish.
1.4 Update: the Qloo key has arrived
The app skeleton is built to take Qloo as one more provider behind TasteResearchProvider. Activating it is now the team’s shared priority. The aim is unchanged: add real cultural-affinity capability to a working Vitrine, without letting Qloo output pass for verified retail evidence.
Workstream	What changes now
WS1 Frontend	Verify the anchor-review screen, hypotheses and lead detail panel with real Qloo data, including empty and weak results, provider errors and rate limits. Badge logic: Qloo for real results, Demo only for mock.
WS2 Backend	Set the key, confirm /integrations/status, cache and rate-limit Qloo calls, store provider-call metadata, populate cultural_affinity only through the documented mapping, and keep older demo runs clearly demo.
WS3 AI & Research	Read the official Qloo documentation, run the experiment matrix, build the real client, schemas and mappings from actual responses, and write docs/qloo-findings.md stating what is and is not usable for home textiles.

Suggested activation order
1.	WS3 (first hours): make one authenticated test call, record the real response shape, and share it with WS1 and WS2 as a fixture labelled “recorded real response”.
2.	WS3: run the experiment matrix (WS3 section 5.6) and report a go / partial / no-go view per anchor type.
3.	WS2: switch get_taste_provider() to the real implementation when QLOO_API_KEY is set; confirm taste: live.
4.	WS1: run the demo scenario end to end; fix any display problems found with real data.
5.	All three: a 30-minute review of what Qloo actually returned. Update the demo scenario, anchor wording and hypotheses mapping to match reality, not expectation.
What we know and what we do not
Developer integration notes describe Qloo endpoints for entity search, tag lookup and insights, an X-Api-Key header, and entity types such as brand, place, destination, artist, movie, book, podcast, TV show, video game and person.
The official documentation is at docs.qloo.com. Treat it as the source of truth, and confirm the base URL for your key (`https://api.qloo.com` or `https://hackathon.api.qloo.com`). Do not assume Qloo returns a home-textile market ranking, predicts purchases or covers every entity type we want.

2. Project setup
Concern	Choice	Notes
Framework	Python 3.11+, FastAPI, Uvicorn	Async throughout.
Config	pydantic-settings reading environment variables	Fail fast on missing required settings at startup; optional integration keys may be absent.
Database	Supabase PostgreSQL	Use SQL migrations in backend/app/db/migrations/, committed to the repo.
DB access	SQLAlchemy 2 (async) or supabase-py; pick one on Day 1	The service role key is used only server-side. User-scoped access is enforced by the app and by RLS.
Auth	Verify the Supabase JWT on each request	Dependency current_user() extracts user_id. Never trust a user id sent in a request body.
Validation	Pydantic v2 for every request and response	Response models stop leaking internal fields.
Logging	Structured JSON logs with a request id	Never log keys, tokens or full email bodies.
Tests	pytest + httpx AsyncClient; a test database or transaction rollback	Run in CI on every pull request.

2.1 Environment variables
APP_ENV=dev
SUPABASE_URL=...            SUPABASE_SERVICE_ROLE_KEY=...      SUPABASE_JWT_SECRET=...
DATABASE_URL=...
NEBIUS_API_KEY=             NEBIUS_MODEL_ID=                   (optional until WS3 confirms)
TAVILY_API_KEY=                                                 (optional)
QLOO_API_KEY=                                                   (set locally, never committed)
QLOO_BASE_URL=              QLOO_TIMEOUT_SECONDS=15            QLOO_MAX_CALLS_PER_RUN=20
RUN_MAX_SECONDS=600         STAGE_TIMEOUT_SECONDS=120
CORS_ORIGINS=http://localhost:5173

Provide .env.example with every variable and no values. Missing optional keys mean “use the fixture-backed implementation”, never a crash.
3. Database design
Implement the core model on Day 1 even if not every table is used yet. All tables have id uuid primary key default gen_random_uuid(), created_at, and updated_at where mutable.
Table	Columns beyond id and timestamps	Notes
profiles	user_id (FK auth.users, unique), business_name, country (nullable), website, contact_email, about	One row per seller. Country is optional so the model stays country-agnostic.
products	owner_id, name, category, description, materials text[], style text[], motifs text[], colours text[], price_segment, price_min, price_max, currency, moq, monthly_capacity, target_retailer_types text[], images jsonb	Checks: price_min <= price_max, moq >= 1.
research_runs	owner_id, product_id, status, stage, inputs jsonb, plan jsonb, provider_modes jsonb, error jsonb, started_at, finished_at, heartbeat_at	Status and stage persisted at every transition. heartbeat_at supports stuck-run recovery.
taste_anchors	owner_id, run_id, label, entity_type, external_id (nullable), source, status, rationale, metadata jsonb, is_demo	external_id stays null unless a real provider returned it. Never generate identifiers.
market_hypotheses	owner_id, run_id, title, rationale, region_hint, signals jsonb, status	
leads	owner_id, run_id, product_id, name, website, canonical_domain, location jsonb, retailer_type, website_verified, website_checked_at, tier, scores jsonb, assessment jsonb, cultural_affinity jsonb, review_status, notes, duplicate_of uuid	Unique (owner_id, product_id, canonical_domain); conflicting inserts merge evidence into the existing lead.
lead_evidence	owner_id, lead_id, url, excerpt, source_type, retrieved_at, published_at, domain_matches_lead, provenance	Unique (lead_id, url, md5(excerpt)) to avoid repeats.
outreach_drafts	owner_id, lead_id, product_id, version, subject, body, facts_used jsonb, status, followup_notes, parent_draft_id	Unique (lead_id, version). Edits update the row; regeneration inserts a new version.
ai_call_logs (optional)	task, model_id, latency_ms, validation_ok, tokens_in, tokens_out, error_code, run_id	Add if time allows; WS3 supplies the fields.

3.1 Row-level security and authorization
•	Enable RLS on every table. Policy: owner_id = auth.uid() for select, insert, update and delete.
•	In addition, the API filters by owner_id on every query. RLS is the safety net, not the only control.
•	Child-record endpoints (anchors, evidence, drafts) verify the parent belongs to the caller before reading or writing.
•	Return 404 not_found for another seller’s record, not 403, so existence is not revealed.
•	Background jobs run with the service role but copy owner_id onto every row they write.
4. API implementation
Implement every endpoint in Appendix A.4. Build in this order so the others are unblocked as early as possible.
Order	Endpoints	Target
1	/health, /integrations/status, and stubs for every route returning contract-shaped fixture data	End of Day 1
2	Products CRUD, image upload (Supabase Storage), POST /products/extract-profile (calls structure_product)	Mid Day 2
3	Research runs: create, get, list, rerun; anchors, hypotheses, PATCH /taste-anchors, confirm-anchors	End of Day 2 / early Day 3
4	Leads: list with filters, sort and paging; get; patch; evidence	Day 3
5	Outreach: generate, list, patch, regenerate	Day 3

•	Lead list filters: run_id, product_id, review_status, tier, q (name or domain, case-insensitive), min_score, sort (score_desc, name, newest), page, page_size (max 100). Return the total count.
•	Saved leads: a lead is “saved” when review_status = saved. No separate table.
•	Image upload: accept common image types, enforce a size limit, store in a per-user path, return the URL list.
•	Idempotency: POST /research-runs accepts an optional Idempotency-Key header so a double click does not create two runs.
•	Pagination and ordering must be deterministic (tie-break by id).
5. Research-run workflow and job runner
5.1 State machine
queued -> running -> awaiting_review -> queued -> running -> completed
              \                                         \
               +----------> failed <---------------------+
 
stage: planning -> anchor_proposal -> anchor_review -> discovery -> assessment -> scoring -> done

Transition	Trigger	Action
create → queued	POST /research-runs	Insert run with provider_modes snapshot (which of ai, search, taste are live or fixture).
queued → running (planning)	Runner picks it up	Call plan_research; store plan. Stage planning.
→ running (anchor_proposal)	Plan stored	Create taste_anchors from plan.aesthetic_candidates (source ai_proposed). Ask get_taste_provider() to resolve entities; save returned entities as anchors with the provider’s source and is_demo. Create hypotheses.
→ awaiting_review	Anchors saved	Stage anchor_review. Runner stops. Nothing proceeds without the seller.
awaiting_review → queued	confirm-anchors	Require at least one confirmed anchor (or an explicit “proceed without anchors” flag). Store anchor_ids in inputs.
→ running (discovery)	Runner picks it up	Call ResearchPipeline.run(...). Update stage from the progress callback.
→ running (assessment, scoring)	Candidates returned	For each candidate call assess_lead, then score (section 6) and upsert lead and evidence.
→ completed	All leads written	Stage done; set finished_at. Zero leads is still completed, with a note in plan or outputs explaining empty results.
any → failed	Unrecoverable error	Store error{code, message} and the failing stage. Partial data stays and is marked.

5.2 Runner design
•	Start simple: a single in-process async worker that polls for queued runs, or FastAPI background tasks that write status to the database. The database row is the source of truth either way, so a later move to a proper queue does not change the API.
•	Update heartbeat_at during long stages. On startup, runs left in running with an old heartbeat are marked failed with code internal_error and message “interrupted”.
•	Enforce STAGE_TIMEOUT_SECONDS per stage and RUN_MAX_SECONDS per run.
•	Retry transient upstream errors (timeouts, 429, 5xx) up to two times with exponential backoff and jitter. Never retry validation errors or ai_output_invalid more than the single repair attempt WS3 already performs.
•	Per-lead failures must not abort the run: record the lead with tier: needs_review, an unknowns note and the error, then continue.
•	Keep a hard cap on leads per run (for example 40) so cost and time stay bounded; make it a setting.
6. Transparent lead ranking
This is a prioritization heuristic. It is not a purchase probability and must never be labelled as one. WS3 supplies qualitative labels and reasons; you turn them into numbers using deterministic, testable code.
6.1 Dimension rubric
Dimension	Source	Mapping to 0–100
Category fit	WS3 label	high 100 (explicitly sells relevant home-textile or decor products); medium 60 (adjacent, such as general home decor); low 20; unknown → null.
Aesthetic fit	WS3 label	Same mapping. Based on evidence of style, colour or motif alignment.
Evidence quality	Computed by you from evidence metadata	Start at 0. +40 official-site page present; +20 two or more distinct source URLs; +20 product-listing excerpt present; +10 published or retrieved within 24 months where a date exists (no date adds nothing and subtracts nothing); +10 location or contact verified. Cap 100.
Seller compatibility	WS3 label (price tier, explicit MOQ or wholesale signals)	Match 100; adjacent 60; mismatch 20; no evidence → null. Never penalize a retailer for information that is simply missing.
Cultural affinity	Taste provider, when real	Stored in leads.cultural_affinity. Not included in the overall score. Null until a validated real signal exists.

6.2 Overall score and completeness
•	Weights for the four retail dimensions: category 35, aesthetic 25, evidence 20, compatibility 20.
•	overall = weighted average over the dimensions that are not null, with weights renormalized. If all are null, overall is null.
•	completeness = number of non-null dimensions divided by four. If completeness < 0.75 the UI shows “Preliminary”.
•	Keep weights and mappings in one configuration module with unit tests, so the team can adjust after the manual review without touching logic.
6.3 Tier gates
Tier	Condition
qualified	Website verified AND at least one piece of retail-activity evidence AND category fit is high or medium AND evidence quality ≥ 40.
needs_review	Promising but incomplete: for example website verified with unknown category fit, or evidence quality between 20 and 39, or a per-lead processing error.
unqualified	Website not verifiable, or category fit low with supporting evidence, or domain is a marketplace or wholesaler excluded by rule.

A missing piece of evidence moves a lead toward needs_review, never toward unqualified. Record the reasons that produced each tier in scores so WS1 can display them.
6.4 Scoring tests
•	Unit tests for each mapping, null handling, renormalization and tier gates.
•	A golden set: take at least ten leads from the WS3 evaluation set with manually assigned expected tiers and assert the ranking agrees within the agreed tolerance. Report disagreements to WS3 and the team.
7. Integration with Workstream 3
•	Import only the factories in Appendix A.6. Wrap each call in timeout, retry and error mapping.
•	Persist the full validated output (plan, assessment, facts_used) as JSON so results are never ephemeral.
•	Record in provider_modes whether each run used live or fixture services, and surface it in /integrations/status.
•	When the taste provider reports is_demo: true, copy that flag to every anchor and signal you store.
•	Do not hard-code Qloo response fields anywhere in app/. Only the mapped internal structures reach your code.
7.1 Qloo activation (the key has arrived)
1.	WS3 adds the real provider behind get_taste_provider().
2.	Set QLOO_API_KEY (and QLOO_BASE_URL if the official docs or your key require a specific host) in the backend environment only. Run a health test call; confirm /integrations/status reports taste: live and never reveals the key.
3.	Create a fresh run; confirm anchors have source: qloo, is_demo: false and real external_id values.
4.	Verify that old demo runs remain badged as demo and are not mixed into new results.
7.2 Qloo-specific backend work
Topic	Requirement
Configuration	Add QLOO_API_KEY, optional QLOO_BASE_URL, QLOO_TIMEOUT_SECONDS, QLOO_MAX_CALLS_PER_RUN, QLOO_CACHE_TTL_HOURS. Missing key means mock provider, reported as mock.
Provider-call records	Store for each call: endpoint name, parameters (no secrets), timestamp, status, latency and a reference id. Signals and anchors keep a source_ref to it. Add a table such as provider_calls (owner_id, run_id, provider, endpoint, params jsonb, status, latency_ms, response jsonb, created_at).
Caching	Cache successful responses by (endpoint, normalized params) with a TTL, so reruns and demos do not burn quota. A cached result is still shown as a real Qloo result, with its original retrieved_at.
Quotas and rate limits	Cap Qloo calls per run and per user. On 429, back off and retry within limits, then fail the Qloo stage gracefully with rate_limited.
Failure isolation	If Qloo fails, the run does not fail by default. It records the taste stage as failed or partial, falls back to AI-proposed anchors (source ai_proposed) and continues, unless the seller asked for Qloo-only.
Persisting signals	Write real signals to market_hypotheses.signals and anchors with source: qloo, is_demo: false. Do not write lead.cultural_affinity unless the WS3 mapping defines how a signal applies to that lead (for example a region match); otherwise leave it null.
Score separation	Cultural affinity never enters scores.overall, tiers or completeness.
History	Runs whose provider_modes.taste was mock remain demo. Do not back-fill them with real data.
Security	Redact the key from logs and error messages; add a log-scrubbing test. Never return provider request headers to the client.

8. Error handling and hardening
Case	Required behaviour
Invalid request body	422 mapped to validation_error in the Appendix A.5 format.
Another seller’s record	404 not_found.
Upstream timeout or 5xx	Retry with backoff; if exhausted, upstream_timeout or upstream_unavailable; the run fails with the stage recorded.
ai_output_invalid	Do not save the output. Mark the item needs_review or fail the stage, depending on whether it is per-lead or global.
Tavily returns nothing	Run completes with zero leads and an explanatory note. No invented shops.
Duplicate lead	Merge into the existing lead (same canonical_domain), append new evidence, set duplicate_of only where a second record had already been created through a different identity match.
Server restart mid-run	Stuck-run recovery marks it failed with a clear message; seller can rerun.
Rate limiting	Basic per-user limit on POST /research-runs and outreach generation; return rate_limited.

9. Day-by-day plan
Day 1: Foundation
☐  Contract meeting; freeze Appendix A and commit schemas to contracts/.
☐  Create FastAPI project, settings, logging with request ids, error handlers, CORS, /health.
☐  Create Supabase project; write migrations for all eight core tables; enable RLS and policies.
☐  JWT verification dependency and a test proving an invalid token returns unauthorized.
☐  Stub endpoints returning contract-shaped fixture data; publish /openapi.json for WS1.
☐  .env.example, README with run instructions, and CI running lint and tests.
Day 2: Persistence
☐  Products CRUD with validation and ownership checks; image upload.
☐  POST /products/extract-profile wired to get_ai_service().structure_product (fixture-backed if WS3 is not ready).
☐  Research runs create, get, list; status and stage persisted; runner skeleton processing the planning stage.
☐  Authorization tests: user A cannot read, change or delete user B’s product or run.
☐  Integration checkpoint 1 with WS1 and WS3.
Day 3: Workflow, leads, outreach
☐  Full orchestration: planning, anchor proposal, awaiting_review, confirm-anchors, discovery, assessment, scoring, completion.
☐  Lead and evidence upsert with the uniqueness rules; saved-lead updates.
☐  Scoring module with unit tests.
☐  Outreach endpoints with versioning, edit and regenerate.
☐  Integration checkpoint 2: run the demo scenario from UI to database and back.
Day 4: Hardening and readiness
☐  Timeouts, retries, stuck-run recovery, per-lead failure handling.
☐  Authorization test matrix across every resource.
☐  Failure-injection tests: AI invalid output, Tavily empty, Tavily timeout, taste provider empty.
☐  Seed script that loads the demo scenario clearly marked as demo data.
☐  /integrations/status reflects reality.
☐  Contribute your section to docs/readiness.md: what is live, what is fixture-backed, what is pending.
Qloo activation (now that the key is available)
☐  Add the Qloo settings to .env.example and the settings module; set the real key locally and in the shared dev environment (never in the repo).
☐  Add the provider_calls table migration and the caching layer with TTL.
☐  Wire per-run and per-user Qloo call caps and the 429 handling.
☐  Switch the factory, confirm taste: live, and run the demo scenario end to end.
☐  Confirm anchors saved with source: qloo, real external_id values (null where none), and is_demo: false; confirm old demo runs are untouched.
☐  Failure tests: Qloo timeout, 401, 429, empty result and malformed response. The run must degrade cleanly.
☐  Add a test that no key value appears in logs, API responses or stored params.
☐  Update your section of docs/readiness.md: taste integration live, with known limits.
10. Hand-offs
You provide	To	When
Running server with stub endpoints and OpenAPI document	WS1	End of Day 1
Real products CRUD and auth	WS1	Mid Day 2
Run lifecycle, anchors, hypotheses, leads, evidence, outreach endpoints	WS1	Day 2 end to Day 3
Persisted data and score breakdowns for WS3’s evaluation harness (read-only export)	WS3	Day 4

You need	From	When	Until then
AIService and its Pydantic schemas	WS3	Day 1 skeleton, Day 2 real	Fixture-backed stub in get_ai_service()
ResearchPipeline returning deduplicated candidates	WS3	Day 3	Fixture candidates
TasteResearchProvider interface and mock provider	WS3	End of Day 2	Local stub returning empty list with is_demo: true
Real Qloo provider, mappings and findings note	WS3	During Qloo activation	Mock provider
Assessment labels and reasons per lead	WS3	Day 3	Fixture assessments

11. Definition of done (Workstream 2)
☐  A seller can create a product, save it, start a research job, retrieve status and read persisted results, first with fixtures and then with the live Qloo key.
☐  Run status and stage transitions are persisted and survive a restart.
☐  AI results and their evidence are stored, not returned ephemerally.
☐  Every request and response is validated by Pydantic; errors follow Appendix A.5.
☐  Per-user isolation proven by automated tests for every resource.
☐  Scoring is deterministic, configurable, unit-tested, and never presents a probability.
☐  No Qloo-specific field names appear outside integrations/qloo/.
☐  taste: live with the real key; Qloo calls are cached, capped, recorded in provider_calls, and the key never appears in logs or responses.
☐  A Qloo failure degrades the run instead of breaking it.
☐  No PayPal code, no outbound email sending, no keys in logs or responses.
Risks and mitigations
Risk	Mitigation
WS3 interfaces arrive late	Factories return fixture-backed implementations from Day 1, so the workflow is testable alone.
Long runs block the API	Runner is async and separate from request handlers; status is read from the database.
Duplicate leads inflate results	Unique constraint on canonical domain plus merge logic, covered by tests.
Schema churn	Migrations are append-only after Day 2; contract changes need a PR.
Qloo quota used up during testing	Response cache, per-run call caps and recorded real fixtures for repeat tests.
Key leaks into logs or git	Log scrubbing test, .env in .gitignore, secret scanning in CI; rotate immediately if exposed.


 Appendix A: Shared contract (v0.2)
This appendix is identical in all three files. If the three copies ever differ, the version in contracts/ in the repository wins.
A.1 Repository layout
vitrine/
  contracts/              shared schemas + TypeScript types (PR review by all three)
  frontend/               WS1  React + TypeScript
  backend/
    app/                  WS2  FastAPI: api/, db/, auth/, jobs/, scoring/
    ai/                   WS3  Nebius client, tasks, prompts, schemas
    research/             WS3  Tavily client, query planner, evidence, dedupe
    integrations/qloo/    WS3  client.py, schemas.py, service.py, mappings.py
  fixtures/               WS3  recorded/handwritten fixtures (clearly labelled)
  eval/                   WS3  manually verified retailer evaluation set
  docs/                   everyone  readiness report, decisions log, qloo-findings.md

A.2 Enumerations
Enum	Values	Notes
research_run.status	queued, running, awaiting_review, completed, failed	awaiting_review extends the roadmap’s “such as” list so the seller can confirm anchors mid-run.
research_run.stage	planning, anchor_proposal, anchor_review, discovery, assessment, scoring, done	Human-readable progress. Shown by the UI as a stepper.
lead.review_status	new, saved, rejected, contacted	Seller’s decision about a lead.
lead.tier	qualified, needs_review, unqualified	Computed by WS2 from the gates in WS2 section 6.
outreach_draft.status	draft, ready, contacted	Manual tracking only.
taste_anchor.status	proposed, confirmed, rejected	
taste_anchor.source	ai_proposed, user_added, qloo, demo	qloo is set only from a real Qloo response, now possible because the key has arrived. demo stays for mock data.
Dimension label	high, medium, low, unknown	unknown means no evidence either way.
evidence.source_type	official_site, product_page, social, directory, press, marketplace, other	
Provenance tag	verified_fact, ai_assessment, unknown, demo_data	Every claim shown to the seller carries one.
Integration state	live, mock, pending, disabled	Reported by /integrations/status. Taste should read live once the key is set and a test call succeeds.
price_segment	budget, mid, mid_premium, premium, luxury	

A.3 Core data objects
Field lists below are the agreed minimum. Optional fields may be added without a contract change; renames and removals may not. IDs are UUIDs. Timestamps are ISO 8601 UTC.
Object	Key fields
Product	id, owner_id, name, category, description, materials[], style[], motifs[], colours[], price_segment, price_min, price_max, currency, moq, monthly_capacity, target_retailer_types[], images[], created_at, updated_at
ResearchRun	id, product_id, status, stage, inputs{regions[], retailer_types[], notes, anchor_ids[]}, plan (ResearchPlan JSON), error{code, message} or null, provider_modes{taste, search, ai}, started_at, finished_at
TasteAnchor	id, run_id, label, entity_type, external_id (null unless returned by a real provider), source, status, rationale, metadata{}, is_demo
MarketHypothesis	id, run_id, title, rationale, region_hint or null, signals[{type, text, source, is_demo}], status
Lead	id, run_id, product_id, name, website, canonical_domain, location{city, region, country} or null, retailer_type, website_verified, website_checked_at, tier, scores{category_fit, aesthetic_fit, evidence_quality, seller_compat, overall, completeness}, assessment, cultural_affinity (null or object), review_status, notes, duplicate_of or null
EvidenceItem	id, lead_id, url, excerpt, source_type, retrieved_at, published_at or null, domain_matches_lead, provenance
CulturalAffinity (new in v0.2)	Stored in lead.cultural_affinity, or null: {provider, is_demo, retrieved_at, anchor_ids[], signals[{type, text, source_ref, raw?}]}. source_ref points to the stored provider call. Never merged into scores.overall.
LeadAssessment	For each of category_fit, aesthetic_fit, seller_compat: {label, reasons[], evidence_ids[]}; plus summary, unknowns[], model_id, generated_at
OutreachDraft	id, lead_id, product_id, version, subject, body, facts_used[{fact_id, text, source_url}], status, followup_notes, created_at

A.4 REST API
Base path /api/v1. All routes except /health require a Supabase JWT in the Authorization: Bearer header. WS2 publishes the OpenAPI document at /openapi.json; WS1 generates or hand-mirrors TypeScript types from it.
Method and path	Purpose	Returns
GET /health	Liveness check (no auth).	{status}
GET /integrations/status	State of Nebius, Tavily and Qloo.	{ai, search, taste} each an integration state plus model_id or provider_name
GET /products, POST /products	List and create products.	Product list / Product
GET/PUT/DELETE /products/{id}	Read, update, delete one product.	Product
POST /products/{id}/images	Upload a product image.	Updated images[]
POST /products/extract-profile	AI Task A. Body: free-text description plus any known fields. Not saved until the seller confirms.	ProductAttributes suggestion
POST /research-runs	Create a run. Body: product_id, inputs.	{id, status}
GET /research-runs, GET /research-runs/{id}	List runs; read status, stage, plan, error.	ResearchRun
POST /research-runs/{id}/rerun	New run copied from an old one with changed inputs.	{id, status}
GET /research-runs/{id}/anchors	Candidate and confirmed anchors.	TasteAnchor[]
PATCH /taste-anchors/{id}	Confirm, reject or edit one anchor.	TasteAnchor
POST /research-runs/{id}/confirm-anchors	Resume a run in awaiting_review after anchors are reviewed.	ResearchRun
GET /research-runs/{id}/hypotheses	Market hypotheses with signals.	MarketHypothesis[]
GET /leads	Query: run_id, product_id, review_status, tier, q, min_score, sort, page.	Paged Lead[]
GET /leads/{id}, PATCH /leads/{id}	Read one lead; update review_status and notes.	Lead
GET /leads/{id}/evidence	Evidence items for the lead.	EvidenceItem[]
POST /leads/{id}/outreach-drafts	Generate a new draft (AI Task D).	OutreachDraft
GET /leads/{id}/outreach-drafts	All versions.	OutreachDraft[]
PATCH /outreach-drafts/{id}	Edit subject, body, status, follow-up notes.	OutreachDraft
POST /outreach-drafts/{id}/regenerate	New version from the same lead.	OutreachDraft

A.5 Error format
{ "error": { "code": "validation_error", "message": "Human readable text",
             "details": { "field": "moq", "reason": "must be >= 1" }, "request_id": "..." } }
 
codes: validation_error | unauthorized | forbidden | not_found | conflict |
       upstream_timeout | upstream_unavailable | ai_output_invalid |
       rate_limited | internal_error

The UI shows message and offers a retry for upstream_timeout, upstream_unavailable and rate_limited.
A.6 Python service interfaces (WS3 provides, WS2 calls)
These are the only functions WS2 should call from the AI, research and taste layers. Signatures are indicative; the Pydantic models live in contracts/.
class AIService:
    async def structure_product(self, description: str, known: ProductInput) -> ProductAttributes
    async def plan_research(self, product: Product) -> ResearchPlan
    async def assess_lead(self, product: Product, lead: LeadCandidate,
                          evidence: list[EvidenceItem]) -> LeadAssessment
    async def draft_outreach(self, product: Product, lead: Lead, evidence: list[EvidenceItem],
                             previous: OutreachDraft | None = None) -> OutreachDraft
 
class ResearchPipeline:
    async def run(self, product: Product, plan: ResearchPlan,
                  anchors: list[TasteAnchor],
                  on_progress: Callable[[str, dict], None]) -> list[LeadCandidate]
    # LeadCandidate = name, website, canonical_domain, location, retailer_type,
    #                 website_verified, evidence[]   (already deduplicated)
 
class TasteResearchProvider:
    name: str                     # "mock" or "qloo"
    is_demo: bool                 # True for the mock provider
    async def search_entities(self, query: str) -> list[TasteEntity]
    async def get_insights(self, entity_id: str, options: InsightOptions) -> list[TasteSignal]
 
def get_ai_service() -> AIService                    # fixture-backed if no key
def get_research_pipeline() -> ResearchPipeline      # fixture-backed if no Tavily key
def get_taste_provider() -> TasteResearchProvider    # real Qloo when QLOO_API_KEY is set, else mock

Each factory returns a fixture-backed implementation when credentials are missing, and reports that choice through /integrations/status. This is what lets WS2 and WS1 progress before WS3 finishes.
A.7 Provenance rules
•	verified_fact: extracted from a stored source (URL and excerpt) or checked by deterministic code, such as an HTTP check of the website.
•	ai_assessment: a model’s judgement. Must list the evidence_ids it relied on. A claim with no supporting evidence is rejected before saving.
•	unknown: the information could not be found. Displayed as “Not found”, never as a negative.
•	demo_data: produced by a mock provider or fixture. Always badged, never mixed into a production-looking summary.
A.8 Fixed demo scenario
All three workstreams develop against this one scenario. Values are placeholders for the team to confirm on Day 1; the data model stays country-agnostic.
Item	Value
Seller	“Sample Seller”, a small textile workshop. Origin country is an optional field, not hard-coded.
Catalogue	Block-printed cotton table runner; cushion cover set; table linen set; throw.
Core attributes	Botanical motifs; warm earthy colours (terracotta, indigo, ochre); mid-premium positioning; MOQ 50 sets; capacity 1,500 units per month (placeholder).
Target buyers	Independent home-decor boutiques, home-textile retailers, interior and lifestyle shops.

End-to-end flow:
1.	Seller creates a product and pastes a free-text description.
2.	AI suggests structured attributes; the seller corrects and saves.
3.	Seller starts market research for the product.
4.	Run plans research and proposes aesthetic anchors; status becomes awaiting_review.
5.	Seller confirms or rejects anchors (labelled demo until Qloo is live).
6.	Discovery finds candidate boutiques, verifies websites, stores evidence and merges duplicates.
7.	Each lead is assessed and scored; the seller sees tiers, reasons and source links.
8.	Seller saves three leads and opens one in the detail panel.
9.	Seller generates an outreach draft, edits it, marks it ready, copies it, then marks it contacted with a follow-up note.
A.9 Changes in v0.2 (Qloo live)
Change	Reason
CulturalAffinity object shape defined (A.3)	So WS1 can build the display and WS2 can persist it before real response details are known.
taste_anchor.source = qloo may now be written	Real provider results are available.
get_taste_provider() returns the real provider when the key is set	Activation switch.
Provider-call metadata is stored (source_ref)	Auditability and debugging; ties each signal to the call that produced it.
No change to enums, endpoints or existing fields	Backward compatible with all work done under v0.1.

