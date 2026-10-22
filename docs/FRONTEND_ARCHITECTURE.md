# Frontend Architecture

## Structure
`frontend/src/` contains `api/` (HTTP client/resources/generated OpenAPI types), `components/`, `config/`, `features/{auth,dashboard,products,discovery,leads,outreach}/`, cross-feature `hooks/`, `lib/`, `mocks/`, `routes.tsx` and `main.tsx`. Feature-owned components/hooks stay beside their feature until truly reusable.

## Data flow
`Route/page → feature hook → resource module → adapter boundary → mock adapter (VITE_USE_MOCK=true) or fetch client → FastAPI /api/v1`.

Views do not call `fetch` directly or import fixtures. Mock and live adapters return the same contract-shaped types. TanStack Query manages server state/invalidation and run polling; form edits remain local. Use React Hook Form + Zod. Wire keys stay snake_case.

Generate TS types from root `openapi.json` using `npm run api:types` from `frontend/`; do not manually edit generated output. Check `contracts/schemas.py` and `docs/decisions.md` when the API evolves.

## API client
Centralize base URL, access-token injection, JSON/multipart, error envelope parsing and request IDs in `src/api/client.ts`. Error shape is `{error:{code,message,details,request_id}}`. Retry only `upstream_timeout`, `upstream_unavailable`, `rate_limited`. Network errors mean connectivity trouble. Auth/session layer handles 401.

## Browser environment
Allowed: `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` (public by design), `VITE_USE_MOCK`. Supabase JS is for sign-in/session. Data calls go through FastAPI using bearer JWT. Provider secrets, service-role and JWT-signing secrets remain backend-only.

## Testing
Vitest + React Testing Library; cover loading, empty, error, unknown/null and demo cases. Add a Playwright smoke flow after the core UX exists. Before calling ready run `npm run typecheck`, `npm run lint`, `npm test` and `npm run build`.
