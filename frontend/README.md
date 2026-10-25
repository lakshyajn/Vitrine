# Frontend (WS1) — Vitrine Platform

React 18 + TypeScript + Vite 6 frontend for Vitrine, an evidence-backed retailer discovery and wholesale outreach platform for independent makers and boutique product labels.

## Architectural Overview

- **Design System:** Aubergine (`#4A154B`) and Vermilion (`#CF1E1E`), Deep Plum (`#161117`), Canvas (`#F8F6F7`), and Space Grotesk / Inter typography.
- **Contract Fidelity:** Wire models directly match `contracts/schemas.py` and `openapi.json` (`snake_case`, nullable scores, explicit provenance, and `is_demo` lineage).
- **Public Showcase:** The public landing page (`/`) presents an editorial narrative, brand mark, and interactive 4-stage product walkthrough.
- **Application Shell:** Responsive desktop sidebar and mobile navigation wrapping the core workspace features.

## Application Routes & Features

- `/` — Public editorial landing page with interactive walkthrough.
- `/login` & `/signup` — Branded maker authentication with instant demo access.
- `/app` — Workspace overview dashboard with provider subsystem status (`IntegrationBanner`) and active metrics.
- `/app/products` — Product Passport catalog: search, filtering, wholesale terms, and image previews.
- `/app/products/new` & `/app/products/:id` — Product Passport form with materials provenance tag inputs and AI Attribute Extraction (`ExtractProfileModal`) with field-by-field acceptance review.
- `/app/discovery` — Market Discovery runs: target regions, status tracking, and new run launcher.
- `/app/discovery/:runId` — Discovery Run Workbench: 7-stage `StatusStepper`, polling while active, and interactive Taste Anchor Review panel (`POST /confirm-anchors`).
- `/app/leads` — Discovered Buyer Leads: query, tier filter, status filter, sorting, and priority fit scores (`ScoreBar`).
- `/app/leads/:id` — Buyer Lead Detail: official website verification, dimension assessments, verified web evidence (`EvidenceCard`), cultural affinity signals, and seller notes.
- `/app/outreach` — Outreach Studio directory: organized wholesale pitch drafts and version tracking.
- `/app/outreach/:leadId` — Pitch Workbench: grounded pitch editor, facts-used citations inspector, model alerts, copy actions, and manual status tracking (`draft → ready → contacted`). Strictly no automated email sending or send buttons.
- `/app/insights` — AG Studio Insights: read-only data intelligence across pipeline tiers, boutique territory footprint, and channel format yield.
- Legacy redirects: `/products`, `/discovery`, `/leads`, `/outreach`, `/insights` seamlessly redirect to `/app/*`.

## Verification Commands

From `frontend/`:
```bash
npm run dev        # Launch Vite development server on 127.0.0.1:5173
npm run typecheck  # Run strict TypeScript compiler verification (tsc --noEmit)
npm run lint       # Run ESLint across entire codebase
npm test           # Run Vitest test suite
npm run build      # Compile production bundle
```
