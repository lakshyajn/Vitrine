# Workspace instructions for the coding agent

You are working on **WS1: Frontend & UX** unless the user explicitly says otherwise.

## Read before editing
Read in this order: `contracts/schemas.py`, `openapi.json`, `docs/decisions.md`, `AGENT.md`, `docs/WS2_Spec.md`, `docs/WS1_FRONTEND_CONTEXT.md`, `docs/DESIGN_SYSTEM.md`, `docs/FRONTEND_ARCHITECTURE.md`, then `docs/FRONTEND_IMPLEMENTATION_PLAN.md`.

`contracts/` and `openapi.json` are authoritative for wire fields, enums and payload shapes. Accepted decisions in `docs/decisions.md` supersede older draft/spec copies. If sources conflict, explain it and propose a recorded decision instead of guessing.

## Ownership
- WS1 changes belong in `frontend/**`.
- Do not edit backend, shared contracts, scoring, prompts, provider clients or DB/auth rules without explicit permission and team review.
- Pages/components must not import fixture files or call `fetch` directly. Data access goes through `frontend/src/api/` and feature hooks.
- Keep branding in `frontend/src/config/brand.ts` only.

## Hard rules
- No payment providers, payment flows, invoices, orders/quotes or payment UI.
- No email sending/integration and no Send button. Outreach is draft, edit, copy and manual status tracking only.
- Provider secrets, Supabase service-role key and JWT signing secret are backend-only. Never put them in `VITE_*` variables.
- API payloads, TypeScript wire types, validation and mock records use `snake_case`.
- Mock/fixture data preserves `is_demo: true` and displays a visible “Demo data” label.
- Preserve `unknown → null → “Not enough evidence”`. Never coerce missing scores to zero.
- Missing evidence is not a negative finding. Never fabricate retailers, URLs, provider IDs, statistics, facts or citations.
- Keep market hypotheses and cultural affinity separate from verified retailer facts and fit scores.
- Render extracted web text as plain text, never via `dangerouslySetInnerHTML`. External links use `target="_blank"` and `rel="noopener noreferrer"`.
- Retry UI only for `upstream_timeout`, `upstream_unavailable`, and `rate_limited`; handle 401 in the auth/session layer.

## Workflow and quality bar
Inspect before editing, state the milestone before large edits, work in small increments, preserve existing code, and report actual typecheck/lint/test/build outcomes. Verify the running UI in a browser at desktop/tablet/mobile; compilation alone is not a UI review. Every visible control must work or explain why disabled. Prioritize Product Passport, Market Discovery/anchor review and Buyer Leads over dashboard polish. Avoid generic AI-dashboard templates, fake metrics, decorative charts and unnecessary card grids.
