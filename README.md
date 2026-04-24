# Full Stack FastAPI Template

A full-stack application template with a FastAPI backend, React frontend,
Postgres database, and Fly.io deployment target.

## Architecture

- Backend: FastAPI, SQLModel, Pydantic settings, Alembic migrations, Supabase
  Auth bearer-token verification, and Pytest.
- Frontend: React, TypeScript, Vite, TanStack Router/Query, Tailwind CSS,
  shadcn/ui, generated OpenAPI client, and Playwright.
- Local development: Supabase CLI for local Auth, Docker Compose for app
  services and integration tests, Compose watch for backend/container changes,
  and host-run Vite for frontend hot reload.
- Staging and production: Fly.io apps using immutable CI-built images, Fly
  secrets, Fly proxy/TLS, and Supabase-managed Postgres.

The local Compose stack is not a deployment target.

## Developer Interface

Use `just` from the repository root:

```bash
just --list
just dev-watch
just backend-dev
just frontend-dev
just check
```

`just dev-watch` is backend/container watch. Use `just frontend-dev` for
frontend hot reload.

See [development.md](./development.md) for local setup, commands, quality gates,
environment file policy, and local service URLs.

## Deployment

Deployment is Fly-native. Supabase provides Auth and managed Postgres,
including backups and point-in-time recovery where supported by the active plan.

See [deployment.md](./deployment.md) for Fly app setup, secrets, domains,
connection budgeting, CI/CD expectations, rollback, and database restore notes.

## Configuration

The committed root `.env` contains local development defaults for this template.
Staging and production configuration belongs in Fly secrets.

Generate secret values with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

At minimum, deployed environments need non-default values for:

- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- `SUPABASE_SECRET_KEY`
- `FIRST_SUPERUSER_PASSWORD`
- `DATABASE_URL`
- `DATABASE_URL_DIRECT`

## Project Docs

- Backend details: [backend/README.md](./backend/README.md)
- Frontend details: [frontend/README.md](./frontend/README.md)
- Development workflow: [development.md](./development.md)
- Deployment workflow: [deployment.md](./deployment.md)

## License

The Full Stack FastAPI Template is licensed under the terms of the MIT license.
