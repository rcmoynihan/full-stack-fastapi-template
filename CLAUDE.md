# CLAUDE.md

## Project Overview
Full-stack web application: FastAPI backend + React/TypeScript frontend.

## Quick Reference
- Quality gate (run before committing): `just check`
- Start backend/container watch: `just dev-watch`
- Start frontend hot reload: `just frontend-dev`
- Run backend tests only: `just backend-test`
- Run backend lint only: `just backend-lint`
- Generate API client: `just generate-client`
- Create migration: `just migrate-create "description"`
- Run e2e tests: `just test-e2e`

## Architecture
- Backend: FastAPI + SQLModel + Alembic (Python 3.14, managed by uv)
- Frontend: React 19 + TanStack Router/Query + Radix UI + Tailwind (Bun)
- Database: Postgres (local: Docker Compose; deployed target: Supabase managed)
- Auth: JWT-based custom auth
- Config: Pydantic Settings in the backend, `/env.js` runtime config in the frontend
- Deployment: Fly.io for application images; Supabase managed Postgres for deployed databases; local Docker Compose remains for development and testing

## Key Directories
- `backend/app/` - FastAPI application code
- `backend/app/core/config.py` - Backend configuration
- `backend/app/models.py` - SQLModel table and schema definitions
- `backend/app/api/routes/` - API endpoint modules
- `backend/tests/` - pytest test suite requiring Postgres
- `frontend/src/` - React application
- `.github/workflows/` - CI/CD pipelines

## Testing
- Backend tests require a running Postgres instance
- Coverage threshold: 92% (hard gate in `just check` and CI)
- E2E: Playwright via `just test-e2e`

## Code Style
- Backend: ruff (lint + format), mypy + ty (type checking)
- Frontend: Biome (lint + format)
- Pre-commit hooks via prek

## Migration Policy
- All database migrations must be backward-compatible using expand/contract discipline
- No column drops, renames, or type changes in the same deploy as the code change
- Keep old and new app versions compatible during deploys
