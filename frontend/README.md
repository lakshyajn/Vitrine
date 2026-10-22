# Frontend (WS1)

React + TypeScript frontend. Root contracts/OpenAPI/backend live one directory above.

## Prerequisites
Node.js 22.12+ and npm 10+, Git, VS Code or Antigravity IDE.

## Install and run
From the repository root:
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```
Open the localhost URL Vite prints.

## Environment
`.env.local` is ignored by Git. Start in mock mode:
```dotenv
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_USE_MOCK=true
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
```
Only these four frontend variables are permitted. Nebius, Tavily, Qloo, service-role and JWT secrets remain backend-only. Do not copy root `.env.example` into the frontend.

## Commands
`npm run dev`, `npm run typecheck`, `npm run lint`, `npm test`, `npm run build`, `npm run api:types`.

`npm run api:types` generates `src/api/generated.ts` from root `openapi.json`; do not hand-edit generated output.

This is an initial scaffold, not the finished UI. Follow `../docs/FRONTEND_IMPLEMENTATION_PLAN.md` and build one screen at a time. Views must never import fixtures directly.
