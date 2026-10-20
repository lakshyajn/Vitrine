# WS2 Backend Operational Recipes (`backend/app/skills.md`)

> **Golden Rule (AGENT.md Section 15):** Never copy enum lists, scoring weights, or API tables into `skills.md` (they will drift from `contracts/`). Always point to `contracts/` and `AGENT.md`. Use this file **strictly** for local operational recipes, coding patterns, and CLI commands.

---

## 1. Operational Commands

- **Install dependencies:**
  ```powershell
  pip install -r backend/requirements.txt
  ```
- **Run FastAPI dev server:**
  ```powershell
  uvicorn backend.app.main:app --reload --port 8000
  ```
- **Run all WS2 tests:**
  ```powershell
  pytest backend/tests -v
  ```
- **Run specific test file:**
  ```powershell
  pytest backend/tests/test_contracts.py -v
  ```
- **Export OpenAPI spec for WS1:**
  ```powershell
  python -c "import json; from backend.app.main import app; print(json.dumps(app.openapi(), indent=2))" > openapi.json
  ```
- **Run database migrations:**
  Apply raw SQL migrations sequentially from `backend/app/db/migrations/` using the database migration runner or psql/asyncpg.

---

## 2. Database Stack: SQLAlchemy 2.0 (Async)

- **Engine & Session:**
  Use `create_async_engine()` with `async_sessionmaker[AsyncSession]`, `expire_on_commit=False`.
- **Session Dependency:**
  ```python
  async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
      async with async_session_factory() as session:
          try:
              yield session
              await session.commit()
          except Exception:
              await session.rollback()
              raise
  ```
- **Migrations:**
  Raw SQL migration scripts in `backend/app/db/migrations/` named `001_initial_schema.sql`, `002_...sql`. Committed to repo.

---

## 3. Auth & Per-User Isolation Recipe

### 3.1 JWT Verification (`current_user()`)
- Extracted via FastAPI dependency: `current_user(token: HTTPAuthorizationCredentials = Depends(auth_scheme))`.
- Validates Supabase JWT using `SUPABASE_JWT_SECRET` (HS256).
- Extracts `sub` claim as `UUID(user_id)`.
- Never trust `owner_id` or `user_id` passed in request payloads or query params.

### 3.2 Mandatory Query Isolation & 404 Not Found
- **Every single query** must filter by `owner_id == current_user.id` (or `user_id == current_user.id` on `profiles`).
- **Child records** (`/taste-anchors/{id}`, `/leads/{id}/...`, `/outreach-drafts/{id}`): Verify parent record ownership before reading or writing.
- **Defense in depth:**
  If a record is not found OR belongs to another seller, return **404 `not_found`** (NEVER 403 `forbidden`), preventing seller ID enumeration.

---

## 4. Error Envelope Recipe (`backend/app/core/errors.py`)

Every error response must match the Contract v0.2 error envelope:
```json
{
  "error": {
    "code": "validation_error",
    "message": "Human readable explanation",
    "details": { "field": "moq", "reason": "must be >= 1" },
    "request_id": "00000000-0000-0000-0000-000000000000"
  }
}
```

- Allowed codes: `validation_error`, `unauthorized`, `forbidden`, `not_found`, `conflict`, `upstream_timeout`, `upstream_unavailable`, `ai_output_invalid`, `rate_limited`, `internal_error`.
- FastAPI `RequestValidationError` (422) is intercepted and rewritten to return `code="validation_error"` in this exact envelope.
- Global exception handler catches unhandled exceptions and returns `500` with `code="internal_error"` and a unique `request_id`.

---

## 5. Background Job Runner & Execution Rules

- **Execution Model:** In-process asynchronous background worker polling/executing queued runs, using database rows as the sole source of truth.
- **State Persistence:**
  - Persist `status` and `stage` to PostgreSQL at **every single transition**.
  - Update `heartbeat_at` frequently during long stages.
- **Startup Recovery:**
  - On server startup, mark any run left in `status == running` with a stale `heartbeat_at` as `failed` (`code: internal_error`, message: `"interrupted"`).
  - Leave runs in `awaiting_review` completely untouched.
- **Active Timer (`DECISION-D10`):**
  - Time spent in `awaiting_review` does **not** count towards `RUN_MAX_SECONDS=600`.
- **Evidence UUID Persistence Ordering (`DECISION-D8`):**
  - During discovery/assessment, WS2 **first** upserts the `Lead` and its `lead_evidence` rows into PostgreSQL to generate real UUIDs.
  - **Then**, pass those persisted `EvidenceItem` objects with populated UUID `id`s to `AIService.assess_lead()`.
- **Per-Lead Fault Tolerance:**
  - A failure assessing or scoring an individual lead must **never** abort the research run. Save the lead with `tier: needs_review`, record an error note in `unknowns`, and continue.
- **Qloo Integration & Graceful Degradation:**
  - When `QLOO_API_KEY` is set, query real provider and cache successful responses by `(endpoint, normalized_params)` in `provider_calls` within `QLOO_CACHE_TTL_HOURS`.
  - Cap Qloo calls per run (`QLOO_MAX_CALLS_PER_RUN=20`).
  - Redact secret keys from logs, request bodies, and error envelopes.
  - If Qloo fails or times out, degrade gracefully to `ai_proposed` anchors without crashing the run.
