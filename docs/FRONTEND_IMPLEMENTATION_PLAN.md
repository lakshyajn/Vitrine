# WS1 Implementation Plan: Completed Status

## Milestone 0: Setup
- [x] Add frontend workspace configuration and scripts.
- [x] Configure workspace developer environment and project skills.
- [x] Document contracts/API boundaries, design language and architecture.
- [x] Clone repo locally and run `npm install`.
- [x] Verify typecheck/lint/test/build on the local machine.

## Milestone 1: Design foundation
- [x] Agree final layout using a wireframe/reference before broad implementation.
- [x] Add shell, navigation and responsive behavior across 5 viewports.
- [x] Build ProvenanceTag, StatusStepper, ScoreBar, EvidenceCard, EmptyState, ErrorState, LoadingSkeleton, and Modal.
- [x] Run in browser and inspect screenshots before expanding.

## Milestone 2: Product Passport
- [x] List/search/empty/loading/error.
- [x] Create/edit/delete form, image preview, multi-currency terms (`USD`, `EUR`, `GBP`) and validation.
- [x] AI-suggestion review/diff (`ExtractProfileModal`) which preserves unsaved state.
- [x] Contract-shaped mock adapter and failure fixtures.
- [x] Live Products API adapter without view changes.
- [x] Direct "Start Discovery" creation from product cards.

## Milestone 3: Market Discovery
- [x] Start research with idempotency key, progress polling and all states/stages.
- [x] Anchor review, confirm/reject/edit/custom anchor with accessible undo recovery.
- [x] Hypotheses/signals, weak/empty results, error and rerun.
- [x] Integration status and live adapter.

## Milestone 4: Buyer Leads
- [x] Search/filter/sort/pagination.
- [x] Save/reject/note with accessible `ConfirmationModal` and accurate count updates.
- [x] Detail evidence, score reasons, unknowns, site verification and duplicate link.
- [x] Separate cultural affinity vectors.

## Milestone 5: Outreach Studio
- [x] Generate/edit/version history with workbench layout skeletons.
- [x] Facts-used citations inspector and model warnings.
- [x] Generation elapsed duration timer (>15s guidance) and draft revision notice.
- [x] Copy and manual status tracking only (`draft` → `ready` → `contacted`).

## Milestone 6: Auth and hardening
- [x] Supabase session + FastAPI JWT.
- [x] Lean data-driven Dashboard and not-found route.
- [x] Loading/empty/error/zero states; responsive/accessibility review.
- [x] Strict removal of unneeded AG Studio and developer-demo badges.

## Milestone 7: Production UX & Modal Hardening
- [x] Resolved CSS transform containing-block bug on ancestor animations (`@keyframes enter-up`).
- [x] Centralized portal modal architecture (`Modal.tsx` and `ConfirmationModal.tsx`) with keyboard focus trap, body scroll-lock, and viewport centering.
- [x] Production safeguards in `pipeline.py` and `service.py` blocking fake fixtures when API keys are absent in production.
- [x] 100% test pass: 130 backend pytest tests + 37 frontend vitest tests + 0 lint errors + 0 type errors.
