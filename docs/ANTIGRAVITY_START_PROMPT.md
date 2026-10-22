# First Antigravity Prompt

Paste this into Antigravity after opening the Vitrine repository root and completing `npm install`.

---

You are acting as **WS1: Frontend & UX** for this existing repository. The local branch is `ws1/bootstrap` and a React/TypeScript/Vite scaffold now exists under `frontend/`.

Before coding, read these repository sources:

1. `AGENTS.md`
2. `AGENT.md`
3. `contracts/schemas.py`
4. `openapi.json`
5. `docs/decisions.md`
6. `docs/WS2_Spec.md`
7. `docs/WS1_FRONTEND_CONTEXT.md`
8. `docs/DESIGN_SYSTEM.md`
9. `docs/FRONTEND_ARCHITECTURE.md`
10. `docs/FRONTEND_IMPLEMENTATION_PLAN.md`
11. All three skills in `.agents/skills/`
12. Existing `frontend/package.json`, source files and test setup

Do not edit files until you have inspected these sources. Then summarize the actual project boundaries, canonical API rules, visual direction, conflicts/uncertainties, and the smallest sensible first milestone. Do not claim the setup works until you run the checks.

After summarizing, start with **Milestone 1: the frontend shell and reusable design primitives**, not the entire application at once. Keep all implementation changes in `frontend/**` unless explicitly authorized otherwise. Follow the implementation plan in small increments and keep the application running after each increment. The dashboard is not the priority: build the Product Passport and core discovery/lead journey first.

Hard constraints: exact API paths and snake_case wire fields; isolated mock adapter controlled by `VITE_USE_MOCK`; no direct fixture imports in screens; visible “Demo data” whenever `is_demo: true`; `null`/`unknown` score means “Not enough evidence,” never zero; no invented retailer evidence or statistics; no payment/order/invoice functionality; no email sending and no Send button; no provider secrets in frontend. Do not change shared contracts/backend without raising the conflict and getting explicit approval.

Use the `karigar-ui-design` skill for screen design, `karigar-frontend-implementation` for code, and `karigar-ui-review` to review each finished screen. After each milestone, report changed files and actual typecheck/lint/test/build results; distinguish checks not run from passing checks.
