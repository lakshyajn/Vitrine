# Frontend (WS1): Vitrine Platform

<div align="justify">

React 18 + TypeScript 5.7 + Vite 6 client for **Vitrine**, an evidence-backed boutique discovery, cultural taste evaluation, and wholesale outreach preparation platform designed for independent makers and artisanal product brands.

</div>

---

## Architectural Overview

<div align="justify">

- **Design System:** Aubergine (`#4A154B`), Vermilion (`#CF1E1E`), Deep Plum (`#161117`), Warm Canvas (`#F8F6F7`), and Space Grotesk / Inter typography.
- **Contract Fidelity:** Wire models directly match `contracts/schemas.py` and `openapi.json` (`snake_case`, nullable fit scores, explicit provenance, and typed error envelopes).
- **Public Showcase:** The public landing page (`/`) presents an editorial narrative, brand identity, and an interactive 4-stage product walkthrough.
- **Application Shell:** Responsive desktop sidebar and mobile navigation wrapping the core workspace features.
- **Centralized Viewport Modal Architecture:** Accessible portal-based dialogs (`src/components/shared/Modal.tsx`) rendering via `createPortal(..., document.body)` with background scroll-locking, focus trapping, and native `Escape` key listeners. Resolves the CSS transform containing-block issue so popups always center precisely within the visible viewport.

</div>

---

## Application Routes & Feature Workbenches

<div align="justify">

- `/`: Public editorial landing page with interactive walkthrough and craft narrative.
- `/login` & `/signup`: Maker authentication and account onboarding (1-step signup, Supabase session integration).
- `/app`: Workspace overview dashboard with pipeline metrics and quick navigation.
- `/app/products`: Product Passport catalog: multi-currency wholesale terms (`USD`, `EUR`, `GBP`), craft specifications, category filters, and image previews.
- `/app/products/new` & `/app/products/:id`: Product Passport form with materials provenance tag inputs and AI Attribute Extraction (`ExtractProfileModal`) with field-by-field acceptance review.
- `/app/discovery`: Market Discovery runs: target regions, status tracking, and new run launcher.
- `/app/discovery/:runId`: Discovery Run Workbench: 7-stage `StatusStepper`, live status polling, and interactive Taste Anchor Review panel (`POST /research-runs/{id}/confirm-anchors`) with instant undo recovery.
- `/app/leads`: Discovered Buyer Leads: query, qualification tier filter (`Qualified`, `Needs Review`, `Unqualified`), review status filter, sorting, and multi-dimensional fit scores (`ScoreBar`).
- `/app/leads/:id`: Buyer Lead Detail: official website verification, dimension assessments, verified web evidence (`EvidenceCard`), cultural affinity signals, and seller notes.
- `/app/outreach`: Outreach Studio directory: organized wholesale pitch drafts and version tracking.
- `/app/outreach/:leadId`: Pitch Workbench: grounded pitch editor, facts-used citations inspector, layout loading skeletons, duration timer (>15s guidance), copy-to-clipboard action, and manual status tracking (`draft` -> `ready` -> `contacted`). Strictly no automated email sending or send buttons.
- Legacy redirects: `/products`, `/discovery`, `/leads`, `/outreach` seamlessly redirect to `/app/*`.

</div>

---

## Verification & Build Commands

All commands run from the `frontend/` directory:

```bash
# Launch Vite development server on http://localhost:5173
npm run dev

# Run strict TypeScript compiler verification (tsc --noEmit)
npm run typecheck

# Run ESLint across entire codebase
npm run lint

# Run Vitest unit & integration test suite (37 tests passing)
npm test

# Compile optimized production bundle into dist/
npm run build
```

---

## Data Truth & Maker Integrity Rules

<div align="justify">

1. **Null Score Truth:** Missing or unverified metrics evaluate to `null` and render as **"Not enough evidence"**, never coerced to zero.
2. **Untrusted Web Isolation:** Scraped store evidence renders as sanitized plain text, never via raw HTML injection.
3. **Direct Seller Control:** Vitrine is a draft and preparation tool. No email-sending APIs exist in the client.
4. **Honest Initial States:** No prepopulated demo imagery or arbitrary price defaults in product forms.
5. **No Secret Leakage:** Client only receives public publishable keys (`VITE_SUPABASE_ANON_KEY`); all provider keys and service secrets remain strictly backend-only.

</div>
