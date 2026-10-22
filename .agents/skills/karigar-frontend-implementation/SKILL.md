---
name: karigar-frontend-implementation
description: Implement WS1 React and TypeScript features using the API contract, feature hooks and isolated mock adapter.
---

# Karigar frontend implementation skill

1. Read root AGENTS.md, AGENT.md, contracts/schemas.py, openapi.json, docs/decisions.md and relevant frontend docs.
2. Work only in frontend/** unless explicitly told otherwise.
3. API calls belong in src/api; hooks own loading/cache/mutations; pages never fetch directly or import fixtures.
4. Use generated OpenAPI types or central mirrors. Never invent endpoint/field/enum names; wire keys are snake_case.
5. Use React Router, TanStack Query, React Hook Form, Zod, shadcn/ui + Tailwind and Lucide; no second component library.
6. Mock/live adapters return the same shapes. VITE_USE_MOCK is the switch. Mock records keep is_demo and show DemoBadge.
7. Preserve null/unknown. Don't infer negativity from missing evidence; keep cultural affinity out of retailer-fit math.
8. AI suggestions stay uncommitted until accepted; extraction errors preserve form values.
9. Use stable query keys, invalidate after mutations and roll back optimistic failures. Poll only queued/running research runs.
10. Outreach means draft/edit/copy/manual status; no send action. No payments/orders.
11. Test happy/error/loading/empty/unknown/demo cases. Run typecheck/lint/test/build and report actual outcomes.
