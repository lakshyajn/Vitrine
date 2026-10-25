---
trigger: always_on
---
# WS1 frontend rules

- Work in `frontend/**` unless explicitly authorized otherwise.
- Read AGENT.md, contracts/schemas.py, openapi.json, docs/decisions.md and frontend docs first.
- Exact contract field/enum names; wire payloads use snake_case.
- No fixture imports in views; no direct `fetch` outside API layer.
- Mock data preserves `is_demo: true` and visibly shows “Demo data”.
- Null/unknown scores say “Not enough evidence”, never zero.
- No payment/order/invoice features, email sending or Send button.
- No provider/service-role secrets in client code or browser environment.
- One component system: shadcn/ui + Tailwind, Lucide icons.
- Product/discovery/leads before dashboard polish.
- Every control works; loading/empty/error/mobile states required.
- Review in browser and report actual test results.
