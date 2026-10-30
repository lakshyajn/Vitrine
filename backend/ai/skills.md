# WS3 Operational Playbook (`backend/ai/`, `backend/research/`, `backend/integrations/qloo/`)

> **Owner:** Workstream 3: AI Tasks (Nebius/Nemotron), Tavily Research Pipeline, Deduplication, Counterparty Trust & Qloo Adapter[cite: 5]
> **Contract Authority:** `contracts/schemas.py` (Rank 1), `AGENT.md`, and `docs/decisions.md`[cite: 1, 7]. Always import contract models and enums from `contracts.schemas`[cite: 7].

## 1. Commands (Run from Repository Root)

- **Run full test suite (WS2 + WS3, zero API keys required):**
  `pytest -v`
- **Run only WS3 unit, validation, dedupe, and counterparty-trust tests:**
  `pytest backend/tests/test_ws3_suite.py -v`
- **Run the retailer evaluation harness (`eval/`):**
  `python -m eval.run_eval`

## 2. Provider Keys & Multi-Option Fallbacks

- **`NEBIUS_API_KEY` (`backend/ai/client.py`):** Uses OpenAI-compatible `/chat/completions` JSON mode. Points to Nebius Token Factory (`https://api.tokenfactory.nebius.com/v1`), NVIDIA NIM (`https://integrate.api.nvidia.com/v1`), or local Ollama. In `APP_ENV=dev`, when empty, `get_ai_service()` returns `FixtureAIService`. In `APP_ENV=production`, missing keys strictly raise `AppError("ai_generation_failed", ..., status_code=503)` (Decision D23).
- **`TAVILY_API_KEY` (`backend/research/tavily_client.py`):** Calls Tavily `/search` and `/extract` with caps (`<=8` queries, `<=10` results/query, `<=30` extractions, `20s` timeout, `2` retries). In `APP_ENV=dev`, when empty, `get_research_pipeline()` returns `FixtureResearchPipeline`. In `APP_ENV=production`, missing keys strictly raise `AppError("upstream_unavailable", ..., status_code=503)` (Decision D23).
- **`QLOO_API_KEY` (`backend/integrations/qloo/provider.py`):** Returns `MockTasteProvider` (`is_demo=True`, `demo-...` IDs, plus weak and empty signal cases) in dev when unset, and calls live Qloo Taste Graph API when configured.

## 3. Validation, Claim Checks & Counterparty Safety Rules

1. **Untrusted Web Excerpts:** Wrap all retailer excerpts in `<untrusted_retailer_evidence>` tags so prompt injections inside scraped web pages are ignored[cite: 1, 5].
2. **Single Repair Retry:** Parse JSON -> validate against `contracts.schemas` -> run deterministic claim checks -> on failure, retry once with the validation error message -> if still invalid, raise `AppError(ErrorCode.AI_OUTPUT_INVALID)`[cite: 1, 5, 7].
3. **Counterparty Genuineness & Shared-Bank-Account Ring-Fencing (`backend/research/evidence.py`):**
   - **Buyer (Receiver) Protection:** Deterministic HTTP check + RDAP domain-age lookup (`<180` days flags credit-default risk) + email-to-canonical-domain binding check. Warnings flow into `LeadAssessment.unknowns` and `OutreachDraft.warnings`[cite: 1, 5, 7].
   - **Seller (Source) Protection:** `evaluate_seller_counterparty_trust()` checks GSTIN-to-PAN structure, bank beneficiary name match, and product image `pHash` overlap. If two distinct businesses share a bank account and one had a dispute, the innocent second business is **not** banned; it is placed in `ring_fenced_escrow` (`0%` upfront payout, `70%` released upon verified `IN_TRANSIT` carrier Bill of Lading, `30%` on delivery).
