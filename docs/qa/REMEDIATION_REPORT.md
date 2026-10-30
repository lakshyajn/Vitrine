# Vitrine: Comprehensive UX, Data Integrity, Modal, and Workflow Remediation Report

**Date of Audit & Remediation**: October 2026  
**Author**: Vitrine Engineering Team  
**Branch**: `main`  
**Test Suites**:
- Frontend: Vitest 3.2 (37/37 passed), TypeScript 5.7 (`tsc --noEmit`, 0 errors), ESLint 9 (`eslint .`, 0 errors/warnings), Vite 6 Production Build (`vite build`, clean)
- Backend: Pytest 9.2 (130/130 passed, 140s)

---

## 1. Executive Summary

This remediation report documents the systematic investigation, root-cause resolution, and cross-platform verification of all usability gaps, positioning defects, data integrity issues, and architectural remnants across the Vitrine platform.

### Summary of Major Accomplishments:
1. **Global Viewport-Centered Modal Architecture (P1)**: Resolved the critical CSS transform containing-block bug where popups were trapped inside scrolling ancestors. Implemented a centralized, accessible portal modal framework (`Modal.tsx` and `ConfirmationModal.tsx`) mounted to `document.body` with focus trapping, background scroll-locking, and native `Escape` key handling across all 7 application dialogs.
2. **Complete Removal of AG Studio (P1)**: Fully excised `ag-studio` and `ag-studio-react` packages, related navigation links, routes (`/app/insights`), and mock analytics canvases, refocusing the application entirely on genuine maker workflows.
3. **Production Safeguards Against Fixture Fallback (P1)**: Hardened `backend/research/pipeline.py` and `backend/ai/service.py` to prevent silent fallback to fake fixtures in production environments (`APP_ENV=production`), raising explicit HTTP 503 errors (`upstream_unavailable`, `ai_generation_failed`). Added dedicated test suite `backend/tests/test_production_safeguards.py` (2/2 passing).
4. **Data Integrity & Maker-First Tone (P2)**: Purged all demo badges, demo login pills, fictional match scores (`92/100`), and internal AI/Qloo jargon in favor of authentic craft-oriented terminology.
5. **Product Passport Polish (P2)**: Added multi-currency pricing (`USD`, `EUR`, `GBP`), removed arbitrary default prices/images, and enabled direct "Start Discovery" creation from product cards.
6. **Buyer Leads & Outreach Studio Enhancements (P2)**: Replaced blur-on-reject with `ConfirmationModal`, added structured layout loading skeletons (`OutreachWorkspaceSkeleton`), generation duration timers (>15s guidance), and draft revision notices.
7. **100% Passing Verification Suite**: Verified 130 backend pytest tests, 37 frontend vitest tests, strict TypeScript compilation, ESLint, and production Vite bundling.

---

## 2. Issue-by-Issue Remediation Register

### Issue REM-01: Global Modal and Popup Viewport Positioning Failure
* **Priority**: **P1 (Critical UX / Global Defect)**
* **Root Cause**:
  1. Ancestor `.animate-page-enter` in `Shell.tsx` applied `@keyframes enter-up` which ended at `transform: translateY(0)`. Under CSS Transforms specification, any non-none `transform` establishes a new containing block for all `position: fixed` descendants, constraining them to the document rather than the browser viewport.
  2. Dialogs were rendered inline inside nested scroll containers (`<main className="overflow-y-auto">`) without a React portal.
* **Resolution**:
  - Implemented [`frontend/src/components/shared/Modal.tsx`](../../frontend/src/components/shared/Modal.tsx) exporting `Modal` and `ConfirmationModal` mounted via `createPortal(..., document.body)`.
  - Configured fixed backdrop `fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/60 backdrop-blur-xs`.
  - Added background scroll-lock (`document.body.style.overflow = 'hidden'`), keyboard focus trap (`Tab`), and native `Escape` key handling with focus restoration.
  - Corrected `@keyframes enter-up` in [`frontend/src/index.css`](../../frontend/src/index.css) to end at `transform: none`.
  - Migrated all application dialogs:
    1. Product Deletion (`ProductListPage.tsx`)
    2. Buyer Leads List Rejection (`LeadsListPage.tsx`)
    3. Buyer Lead Detail Rejection (`LeadDetailPage.tsx`)
    4. Outreach Regeneration (`OutreachWorkspacePage.tsx`)
    5. Product AI Specification Extraction (`ExtractProfileModal.tsx`)
    6. Market Discovery New Run (`NewRunModal.tsx`)
    7. Studio Onboarding (`OnboardingModal.tsx`)

### Issue REM-02: Complete Removal of AG Studio
* **Priority**: **P1 (Architectural Integrity)**
* **Root Cause**: Unneeded third-party analytical canvas and agent packages added bloat and developer-dashboard UI to an artisan craft tool.
* **Resolution**:
  - Deleted `frontend/src/features/insights/AgStudioInsights.tsx` and `InsightsPage.tsx`.
  - Uninstalled `ag-studio` and `ag-studio-react` from `package.json`.
  - Removed Insights navigation items from `nav-items.ts`, `Sidebar.tsx`, `MobileNav.tsx`, and route definitions in `App.tsx`.

### Issue REM-03: Production Safeguard Against Silent Fixture Fallbacks
* **Priority**: **P1 (Data Truth & Production Hardening)**
* **Root Cause**: When API keys were unset in production, `get_research_pipeline()` and `get_ai_service()` silently instantiated `FixtureResearchPipeline` and `FixtureAIService`, serving fabricated demo stockists and canned copy.
* **Resolution**:
  - In `backend/research/pipeline.py` and `backend/ai/service.py`, added environment checks: if `settings.app_env in ("production", "prod")` and required keys are missing, raise `AppError("upstream_unavailable", ...)` or `AppError("ai_generation_failed", ...)`.
  - Preserved fixture fallback for offline development (`APP_ENV=dev`) and test suites (`APP_ENV=test`).
  - Added test suite `backend/tests/test_production_safeguards.py` (2/2 passing).

### Issue REM-04: Maker Tone & Terminology Transformation
* **Priority**: **P2 (UX / Product Polish)**
* **Root Cause**: User-facing screens exposed raw database UUIDs, internal provider codes, and engineering terminology.
* **Resolution**:
  - Replaced internal jargon with maker-centric concepts:
    - *"Cultural affinity mapping"* $\rightarrow$ *"Shopper affinity matching"*
    - *"Retailer alignment vector"* $\rightarrow$ *"Store curation alignment"*
    - *"Discovered candidate"* $\rightarrow$ *"Candidate Stockist"*
  - Masked raw database IDs and UUIDs across tables and detail views.
  - Removed demo badges, demo login shortcuts, and fake match scores (`92/100`).

### Issue REM-05: Product Passport Multi-Currency & Initial States
* **Priority**: **P2 (Domain Modeling)**
* **Root Cause**: Product form assumed USD currency and prepopulated arbitrary prices and mock imagery.
* **Resolution**:
  - Added currency dropdown (`USD`, `EUR`, `GBP`) to `ProductFormPage.tsx`.
  - Removed arbitrary defaults ("85", "140") and default mock image URLs in favor of clean initial states.
  - Corrected tag badge wrapping and button sizing in Material and Aesthetic profiles.
  - Enabled direct "Start Discovery" creation from product cards.

### Issue REM-06: Buyer Leads Rejection Workflow
* **Priority**: **P2 (UX Clarity)**
* **Root Cause**: Rejecting a lead blurred the card inline without clear feedback or confirmation.
* **Resolution**:
  - Replaced inline blur with `ConfirmationModal`.
  - Rejection submits status update, removes item on success, and updates pagination counts cleanly.

### Issue REM-07: Outreach Studio Loading & Regeneration States
* **Priority**: **P2 (UX Polish)**
* **Root Cause**: Outreach workbench lacked structured loading skeletons and clear duration feedback during long generation calls.
* **Resolution**:
  - Implemented `OutreachWorkspaceSkeleton` matching the workbench grid.
  - Added elapsed duration timer with guidance helper (>15s retry options).
  - Added persistent revision banner when regenerating an existing draft.
  - Wired regeneration confirmation to `ConfirmationModal`.

---

## 3. Verification Summary

<div align="justify">

* **Backend Pytest (`pytest backend/tests/ -v`):** 130 / 130 tests passing (100% pass rate).
* **Frontend Vitest (`npm test`):** 37 / 37 tests passing (100% pass rate).
* **TypeScript Strict (`npm run typecheck`):** 0 errors.
* **ESLint Check (`npm run lint`):** 0 errors, 0 warnings.
* **Vite Production Build (`npm run build`):** Clean bundle output in `dist/`.

</div>
