# Vitrine Authentication & Local Setup Guide

This guide documents how to configure, run, and verify authentication and database persistence across the Vitrine platform (Frontend WS1 and Backend WS2).

---

## 1. Operating Modes Overview

Vitrine supports two primary local operating modes:

| Mode | Backend Auth & DB | Frontend Client | Best For |
| :--- | :--- | :--- | :--- |
| **Offline Mock Mode** | SQLite in-memory or file (`vitrine.db`); no Supabase required | `VITE_USE_MOCK=true`; pre-seeded demo user (`studio@ateliersolenne.com`) | Rapid frontend development, UI/UX prototyping, offline demos |
| **Live Supabase Mode** | Asymmetric (ES256) or symmetric (HS256) token verification; SQLite file (`vitrine.db`) | Supabase auth client with real signup, login, password recovery, session refresh | Production, staging, team multi-tenant testing |

---

## 2. Environment Variables Specification

> **SECURITY NOTICE:** Never commit `.env` or `frontend/.env` to source control. Never place `SUPABASE_SERVICE_ROLE_KEY` or JWT secrets in client-side code or `VITE_*` variables.

### Backend (`.env`)

| Variable Name | Required In | Description & Format |
| :--- | :--- | :--- |
| `APP_ENV` | All | Application environment (`dev`, `test`, `production`). In `production`, demo seeding is disabled (returns 404). |
| `ALLOW_DEV_TOKENS` | Testing only | Boolean flag (`true` or `false`). When `false`, all tokens must be cryptographically verified. Must be `false` outside unit tests. |
| `SUPABASE_URL` | Live mode | Supabase project URL (e.g. `https://<project-ref>.supabase.co`). Used for JWKS public key retrieval and issuer claim verification. |
| `SUPABASE_JWT_SECRET` | HS256 mode | Symmetric HMAC signing secret from Supabase Dashboard (API settings). Used as fallback for legacy HS256 tokens. |
| `SUPABASE_SERVICE_ROLE_KEY` | Admin only | Backend-only service role secret. NEVER expose to the browser or frontend. |
| `DATABASE_URL` | All | Database connection string. For persistent local data across restarts, set to `sqlite+aiosqlite:///./vitrine.db`. For stateless test suites, use `sqlite+aiosqlite:///:memory:`. |
| `CORS_ORIGINS` | All | Comma-separated list of permitted frontend origins (e.g. `http://localhost:5173,http://127.0.0.1:5173`). |

### Frontend (`frontend/.env`)

| Variable Name | Required In | Description & Format |
| :--- | :--- | :--- |
| `VITE_USE_MOCK` | Mock mode | Set to `"true"` to run offline without Supabase. Bypasses remote network requests and uses mock data stores. |
| `VITE_SUPABASE_URL` | Live mode | Public Supabase project URL (matches backend `SUPABASE_URL`). |
| `VITE_SUPABASE_ANON_KEY` | Live mode | Public anon key (publishable client key) from Supabase Dashboard. Safe for browser distribution. |
| `VITE_DEV_AUTH_BYPASS` | Dev debug only | Explicit frontend dev bypass flag. Must remain `"false"` in normal operation and production. |

---

## 3. Asymmetric (ES256 / RS256) vs Symmetric (HS256) JWT Verification

### Supabase Signing Architecture
Modern Supabase projects default to asymmetric token signing using elliptic curve cryptography (**ES256**) or RSA (**RS256**). Older instances used symmetric HMAC (**HS256**) with a shared secret.

### Backend Verification Mechanism (`backend/app/auth/deps.py`)
1. **Header Inspection:** Reads unverified JWT header algorithm (`alg`).
2. **Algorithm Enforcement:**
   - Strictly permits only `HS256`, `ES256`, or `RS256`.
   - Explicitly rejects `alg=none` with HTTP 401.
3. **Asymmetric Verification (`ES256` / `RS256`):**
   - Fetches public keys from Supabase's standard JWKS endpoint: `{SUPABASE_URL}/auth/v1/.well-known/jwks.json`.
   - Uses PyJWKClient with in-memory key caching (`cache_keys=True`).
   - Rejects token with HTTP 401 if `SUPABASE_URL` is unset or JWKS cannot be retrieved.
4. **Symmetric Verification (`HS256`):**
   - Verifies against `SUPABASE_JWT_SECRET`. Rejects with HTTP 401 if secret is not configured.
5. **Strict Claim Validation:**
   - `aud`: Must equal `"authenticated"`.
   - `iss`: Must match `{SUPABASE_URL}/auth/v1` whenever `SUPABASE_URL` is configured.
   - `exp`: Token must not be expired.
   - `sub`: Must be present and parse as a valid RFC 4122 UUID. No fallback to demo owner.
6. **Error Sanitization:** All failures return standard Appendix A.5 envelopes with generic messages to prevent token/secret leakage in responses or logs.

---

## 4. Dev Token Bypass Safeguards (`ALLOW_DEV_TOKENS` vs `VITE_DEV_AUTH_BYPASS`)

- **Backend `ALLOW_DEV_TOKENS`:**
  - When `false` (default in `.env.example` and production), dev aliases (`dev-token`, etc.) and unsigned tokens are unconditionally rejected with HTTP 401.
  - When enabled in isolated test suites, a single warning is emitted on startup.
- **Frontend `VITE_DEV_AUTH_BYPASS`:**
  - Must remain `false` by default.
  - Hardcoded tokens (such as legacy `DEV_DEFAULT_TOKEN`) have been completely removed from `client.ts`.
  - When a 401 occurs in live mode, `setUnauthorizedHandler` triggers `supabase.auth.refreshSession()` once; if refresh fails, the user is redirected to `/login?next=...`.

---

## 5. Local Database Persistence & Demo Scenario Seeding

### SQLite File Persistence
Set `DATABASE_URL=sqlite+aiosqlite:///./vitrine.db` in `.env`.
- Database tables are automatically initialized during startup via FastAPI lifespan.
- Database files (`*.db`, `*.sqlite*`) are excluded from Git via `.gitignore`.

### Seeding a New Workspace (`POST /api/v1/demo/seed`)
When a new user signs up or starts with an empty catalog, they can populate a full demo scenario:
- **API Endpoint:** `POST /api/v1/demo/seed`
- **Security:** Requires an authenticated session; records are scoped exclusively to the calling maker (`owner_id = user.id`).
- **Environment Gate:** Returns HTTP 404 in `APP_ENV=production`.
- **Idempotency:** Safe to call multiple times; checks `(owner_id, product_id, canonical_domain)` before inserting to prevent duplicate records.
- **UI Trigger:** On the Products List and Dashboard, when no products exist, an action button labeled **"Load demo catalogue"** automatically invokes this endpoint, notifies the user upon completion, and invalidates TanStack Query caches.

---

## 6. How to Run Locally

### Option A: Running in Mock Mode (No Supabase setup needed)
1. Backend:
   ```bash
   # In root directory
   python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
2. Frontend:
   ```bash
   cd frontend
   # Ensure VITE_USE_MOCK=true is in frontend/.env
   npm run dev
   ```
3. Open `http://localhost:5173`. Click **"Try the demo workspace"** on the login page to enter immediately.

### Option B: Running with Real Supabase
1. Configure `.env`:
   ```bash
   APP_ENV=dev
   ALLOW_DEV_TOKENS=false
   SUPABASE_URL=https://<your-project>.supabase.co
   SUPABASE_JWT_SECRET=<your-jwt-secret>
   DATABASE_URL=sqlite+aiosqlite:///./vitrine.db
   ```
2. Configure `frontend/.env`:
   ```bash
   VITE_USE_MOCK=false
   VITE_SUPABASE_URL=https://<your-project>.supabase.co
   VITE_SUPABASE_ANON_KEY=<your-anon-publishable-key>
   ```
3. Start backend and frontend:
   ```bash
   # Terminal 1:
   python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

   # Terminal 2:
   npm --prefix frontend run dev
   ```
4. Visit `http://localhost:5173/signup`, register your studio, and confirm your email (or auto-confirm if enabled in Supabase Dashboard).

---

## 7. Troubleshooting Guide

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **Token rejected: 401 Unauthorized** | Token expired, wrong audience (`aud != "authenticated"`), or missing/wrong issuer claim. | Ensure your token was issued by the Supabase project matching `SUPABASE_URL`. If using HS256, ensure `SUPABASE_JWT_SECRET` matches your project. |
| **JWKS fetch failure: 401** | Backend cannot reach `{SUPABASE_URL}/auth/v1/.well-known/jwks.json` or `SUPABASE_URL` is malformed. | Verify network connectivity to Supabase and verify `SUPABASE_URL` begins with `https://` without a trailing path. |
| **SQLite DB locked (`database is locked`)** | Multiple processes accessing the SQLite file simultaneously or an open transaction. | Ensure you are using `sqlite+aiosqlite://` driver. Stop any orphaned uvicorn or script instances holding a file lock. |
| **Schema mismatch / 500 error on restart** | Database file schema out of date with current SQLAlchemy models. | Delete the local `vitrine.db` file and restart uvicorn; tables will be cleanly recreated on startup. |
| **Open redirect warning on login** | `?next=` parameter points to an external or untrusted URL. | Vitrine enforces same-origin `/app/*` redirect targets only. Check the query parameter format. |
| **401 loop on token refresh** | Supabase refresh token is invalid or session was revoked. | `setUnauthorizedHandler` automatically clears the query cache and redirects to `/login`. Sign in again to obtain a fresh session. |
