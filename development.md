# FastAPI Project - Development

Use `just` as the local developer interface. The recipes keep local commands
consistent with CI and avoid relying on staging or production deployment files.

## Prerequisites

- Docker and Docker Compose for local database and full-stack runs. Compose
  watch support is required for `just dev-watch`.
- Supabase CLI for local Supabase Auth.
- `uv` for backend dependency and command execution.
- Bun for frontend development and tests.
- `just` for repo-level commands.

Install `just` with your package manager, for example:

```bash
brew install just
```

## Local Development Modes

### Host-Run Hot Reload

Use this mode for day-to-day frontend work and for the fastest feedback loop.
Start Supabase Auth and the database, then run the backend and frontend on the
host:

```bash
supabase start
bash scripts/docker-compose-local.sh up -d --wait db
(cd backend && uv run bash scripts/prestart.sh)
just backend-dev
just frontend-dev
```

Open:

- Frontend: <http://localhost:5173>
- Backend API: <http://localhost:8000>
- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- Supabase Studio: <http://localhost:55323>
- Supabase Mailpit: <http://localhost:55324>

### Compose Backend/Container Watch

Use this mode when you want every service in containers while iterating on the
backend or container-owned files:

```bash
just dev-watch
```

`just dev-watch` uses Docker Compose watch for the backend service only. The
frontend container serves the built nginx image, so frontend source edits do not
hot reload there. For frontend hot reload, use the host-run workflow above, or
stop the Compose frontend before starting Vite on the host:

```bash
bash scripts/docker-compose-local.sh stop frontend
just frontend-dev
```

Open:

- Frontend: <http://localhost:5173>
- Backend API: <http://localhost:8000>
- Swagger UI: <http://localhost:8000/docs>
- Supabase Studio: <http://localhost:55323>
- Supabase Mailpit: <http://localhost:55324>
- Adminer, when the local profile is enabled: <http://localhost:8080>

To start the non-watch container stack:

```bash
just dev
```

Stop the stack:

```bash
just down
```

## Database Commands

Reset the local database volume, run migrations, and perform first
superuser/bootstrap setup:

```bash
just dev-reset-db
```

Create a migration after changing SQLModel models:

```bash
just migrate-create "describe the schema change"
```

Apply migrations locally:

```bash
just migrate
```

Seed optional demo data separately:

```bash
just seed-demo
```

The production deployment path runs migrations through the backend Fly
`release_command`, not from app startup.

## Quality Gate

Run the read-only validation gate before opening a pull request:

```bash
just check
```

Run mutating fixers explicitly:

```bash
just fix
```

Backend-only checks:

```bash
just backend-lint
just backend-test
```

Frontend-only checks:

```bash
cd frontend
bun run lint:ci
bun run build
bun run test
```

## Supabase Auth

Supabase owns signup, login, sessions, password recovery, and password changes.
The local Supabase CLI stack runs on dedicated ports to avoid the default
Supabase CLI port range:

- API: <http://localhost:55321>
- Studio: <http://localhost:55323>
- Mailpit: <http://localhost:55324>

Password recovery emails sent by local Supabase Auth appear in Mailpit.

## Environment Files

The root `.env` file is committed for this template and contains local
development defaults only. Staging and production configuration belongs in Fly
secrets.

The local Postgres container listens on `127.0.0.1:55432` from the host and on
`db:5432` from other Compose services. Supabase Auth runs from the Supabase CLI
on `127.0.0.1:55321`.

Local frontend API calls use the Vite `/api` proxy configured in
`frontend/vite.config.ts`. Playwright defaults to
`MAILPIT_HOST=http://localhost:55324` for host-run tests, while the Compose
Playwright service sets `MAILPIT_HOST=http://host.docker.internal:55324`.
Runtime frontend configuration in deployed environments is generated from Fly
environment variables at container startup.

After changing local environment values, restart affected services:

```bash
just down
just dev-watch
```

Local Compose commands run through `scripts/docker-compose-local.sh`, which
selects the native Docker image platform for the current machine. Set
`LOCAL_DOCKER_PLATFORM` only when you intentionally need to override that
platform.

## API Client

Regenerate the frontend client after backend OpenAPI changes:

```bash
just generate-client
```

If the repo has a read-only API client drift check in `just check`, use that
before committing to make sure generated files are current.

## Pre-Commit Hooks

This repo uses `prek`, a modern pre-commit runner. Install both commit-time and
push-time hooks from the backend environment:

```bash
uv run --project backend prek install --config .pre-commit-config.yaml --hook-type pre-commit --hook-type pre-push -f
```

Run commit-time hooks manually:

```bash
uv run --project backend prek run --config .pre-commit-config.yaml --all-files
```

Run the read-only pre-push gate manually:

```bash
uv run --project backend prek run --config .pre-commit-config.yaml --all-files --stage pre-push
```

Some hooks may modify files. Use `just check` for read-only validation and
`just fix` for intentional formatting or generated-code updates.

## Local URLs

- Frontend: <http://localhost:5173>
- Backend API: <http://localhost:8000>
- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- Supabase Studio: <http://localhost:55323>
- Supabase Mailpit: <http://localhost:55324>
- Adminer, when enabled locally: <http://localhost:8080>
