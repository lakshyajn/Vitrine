---
name: karigar-ui-review
description: Review running frontend screens for visual polish, interactions, responsiveness/accessibility and data-truth issues.
---

# Karigar UI review skill

1. Run the frontend and inspect desktop, tablet and narrow mobile in a browser.
2. Compare to docs/DESIGN_SYSTEM.md; flag generic template layouts, excess cards, gradients, poor spacing/type and pointless charts.
3. Exercise every control; no-op controls or fake success are defects.
4. Check loading, empty, errors/retryable errors, disabled, demo and null states.
5. Inspect network/API payloads: snake_case, auth, error envelope; no secrets.
6. `is_demo` is visibly badged; null/unknown scores say “Not enough evidence”.
7. Scraped excerpts render as text; external links are safe.
8. Check keyboard, focus, labels, dialogs and touch targets.
9. Run typecheck, lint, tests, build and relevant E2E checks. Distinguish not-run from pass.
10. Report severity and fix high-impact defects before expanding scope.
