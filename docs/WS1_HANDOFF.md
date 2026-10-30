# Vitrine: Complete Frontend & Integration Developer Handoff

<div align="justify">

**Application Stack**: React 18, TypeScript 5.7, Vite 6, Tailwind CSS 4, React Router 6.28 (with v7 future flags), TanStack Query 5, Vitest 3.2  
**Target Environment**: `http://127.0.0.1:5173/`

</div>

---

## 1. Frontend Executive Overview

### What Vitrine Does & Who It Serves

<div align="justify">

Vitrine is an evidence-backed boutique discovery, cultural taste evaluation, and wholesale outreach workspace designed specifically for independent makers, craft studios, and physical-product brands. Wholesale discovery for independent product brands has historically been plagued by speculative lists, generic scraping, and cold email spam. Vitrine enforces **grounded data truth**: every suggested boutique stockist is verified against live web evidence, cultural affinity signals, and authentic price/aesthetic compatibility.

</div>

### End-to-End User Workflow

<div align="center">
  <img src="../diagrams/01-vitrine-maker-journey.png" alt="Vitrine End-to-End Maker Journey" width="100%" />
</div>

<div align="justify">

1. **Product Passport (`/app/products`)**: The maker defines product specifications, wholesale pricing ranges (`USD`, `EUR`, `GBP`), minimum order quantities (MOQ), monthly capacities, and materials provenance. Unstructured studio notes or product URLs can be parsed using AI Attribute Extraction with mandatory human verification before saving. Direct "Start Discovery" action triggers a research run immediately.
2. **Market Discovery (`/app/discovery`)**: Research runs are launched with target regions and categories. Discovery identifies candidate boutiques through web search (Tavily) and cultural affinity modeling (Qloo). The maker reviews **Taste Anchors** with one-click confirmation, rejection, custom additions, and accessible undo recovery.
3. **Buyer Leads (`/app/leads`)**: An explorer of discovered stockists categorized into qualification tiers (`Qualified`, `Needs Review`, `Unqualified`). Each profile cleanly separates verified retailer facts from AI match hypotheses. Unscored metrics strictly evaluate to `null` ("Not enough evidence") rather than misleading zeroes. Rejection uses an accessible confirmation dialog.
4. **Outreach Studio (`/app/outreach`)**: A grounded email pitch workbench. Generates tailored buyer pitch drafts citing verified retailer facts. Features structured layout loading skeletons, a duration timer (>15s guidance), facts-used citations inspector, editing, version history, and one-click copying. **Strictly no automated email sending or Send button exists** (compliance boundary).

</div>

---

## 2. Shared Architecture & Hardening Highlights

### A. Centralized Viewport-Centered Modal Architecture (`src/components/shared/Modal.tsx`)

<div align="justify">

- **Root Cause Resolved:** Addressed the CSS transform containing-block issue where ancestor animations (`@keyframes enter-up`) trapped `position: fixed` modals inside scrollable containers. Concluded `@keyframes enter-up` at `transform: none`.
- **Portal Rendering:** All dialogs mount exclusively to `document.body` via `createPortal`.
- **Accessibility & Focus:** Includes native `Escape` key handling, background scroll-lock (`document.body.style.overflow = 'hidden'`), keyboard focus trap (`Tab`), and focus restoration to the triggering element upon closure.
- **Components:** Exports reusable `Modal` and `ConfirmationModal` used across all 7 application dialogs.

</div>

### B. Maker Tone & Trustworthiness

<div align="justify">

- Purged all internal AI/Qloo jargon in favor of maker-centric terminology (*"Shopper affinity matching"*, *"Store curation alignment"*, *"Candidate Stockist"*).
- Removed raw database IDs, UUIDs, and technical model codes from user-facing screens.
- Purged demo badges, demo login shortcuts, and fake qualification scores.

</div>

---

## 3. Route Map & Component Hierarchy

<div align="justify">

* **`/` &bull; `LandingPage.tsx`:** Editorial public showcase with interactive 4-stage walkthrough.
* **`/login` &bull; `LoginPage.tsx`:** Maker login with Supabase session integration.
* **`/signup` &bull; `SignupPage.tsx`:** 1-step registration with studio profile configuration.
* **`/app` &bull; `DashboardPage.tsx`:** Workspace overview, pipeline counts, and recent runs.
* **`/app/products` &bull; `ProductListPage.tsx`:** Product catalog, multi-currency terms, and deletion modal.
* **`/app/products/new` &bull; `ProductFormPage.tsx`:** New product form with craft specifications and AI extraction.
* **`/app/products/:id` &bull; `ProductFormPage.tsx`:** Product edit form with image management.
* **`/app/discovery` &bull; `DiscoveryListPage.tsx`:** Research runs list, run status, and new run modal.
* **`/app/discovery/:runId` &bull; `RunDetailPage.tsx`:** 7-stage status stepper, polling, and interactive taste-anchor review.
* **`/app/leads` &bull; `LeadsListPage.tsx`:** Paged leads table, tier filters, status filters, and rejection modal.
* **`/app/leads/:id` &bull; `LeadDetailPage.tsx`:** In-depth retailer profile, verified store evidence, and affinity vectors.
* **`/app/outreach` &bull; `OutreachListPage.tsx`:** Directory of generated wholesale drafts.
* **`/app/outreach/:leadId` &bull; `OutreachWorkspacePage.tsx`:** Grounded pitch editor, facts-used inspector, and clipboard actions.

</div>

---

## 4. Verification Metrics

- **Backend Pytest:** 130 tests passing (100%).
- **Frontend Vitest:** 37 tests passing (100%).
- **TypeScript:** 0 type errors (`tsc --noEmit`).
- **ESLint:** 0 lint errors or warnings (`eslint .`).
- **Vite Build:** Production bundle generated cleanly.
