# FastAPI Project - Deployment

This project deploys to Fly.io with managed Postgres from Supabase.

Docker Compose is only for local development and local integration testing.
Staging and production must use Fly-native deployment so staging exercises the
same image, secret, release-command, proxy, TLS, and database path that
production uses.

## Target Architecture

- Frontend: a Fly app serving the built React application.
- Backend: a Fly app running FastAPI behind the Fly proxy.
- Database: Supabase Postgres, with SSL required.
- Images: built by CI, pushed to the Fly registry, and deployed by immutable digest.
- Migrations: run once per deploy with the backend Fly `release_command`.
- Secrets: stored in Fly secrets for staging and production.

Use one Fly organization for all apps that need to read images from the Fly
registry.

## One-Time Supabase Setup

Create a Supabase project in a region close to the Fly primary region. For
example, use a Supabase US East region with Fly `iad`.

Create application database roles instead of using the Supabase `postgres`
superuser for the app. Use separate credentials for runtime traffic and
migrations so the web process cannot perform schema changes.

Example runtime role:

```sql
create role app_runtime login password '<runtime-password>';
grant usage on schema public to app_runtime;
grant select, insert, update, delete on all tables in schema public to app_runtime;
grant usage, select, update on all sequences in schema public to app_runtime;
alter default privileges in schema public
  grant select, insert, update, delete on tables to app_runtime;
alter default privileges in schema public
  grant usage, select, update on sequences to app_runtime;
```

Example migration role:

```sql
create role app_migrator login password '<migration-password>';
grant usage, create on schema public to app_migrator;
grant all privileges on all tables in schema public to app_migrator;
grant all privileges on all sequences in schema public to app_migrator;
alter default privileges in schema public
  grant all privileges on tables to app_migrator;
alter default privileges in schema public
  grant all privileges on sequences to app_migrator;
```

Adjust grants for existing schemas or stricter Supabase policies before
production.

From Supabase, collect two SSL-enabled connection strings:

- `DATABASE_URL`: app runtime connection using the runtime role. Use the
  session-mode pooler on port `5432` or a direct connection. Do not use
  transaction-mode pooling on port `6543` for SQLAlchemy web traffic.
- `DATABASE_URL_DIRECT`: direct connection for Alembic migrations using the
  migration role.

Both URLs must include `sslmode=require`.

Verify Fly-to-Supabase connectivity before the first deploy. Direct Supabase
connections can require IPv6; if the selected Fly region cannot connect
reliably, use the supported Supabase pooler path for runtime traffic and keep
`DATABASE_URL_DIRECT` for migrations.

## Connection Budget

Set database concurrency from the Supabase plan limit before production traffic.
Use this formula:

```text
max_connections_used =
  backend_machine_count * WEB_CONCURRENCY * (SQLALCHEMY_POOL_SIZE + SQLALCHEMY_MAX_OVERFLOW)
  + release_command_connections
  + admin/manual connections
```

Start conservatively:

```text
WEB_CONCURRENCY=1
SQLALCHEMY_POOL_SIZE=2
SQLALCHEMY_MAX_OVERFLOW=0
```

These defaults trade throughput for predictable connection usage. Raise them
only after checking the Supabase connection limit and load-test results.

## One-Time Fly Setup

Create four runtime apps and two registry apps. Pick a project-specific app
slug first; the `myapp-*` values below are examples, not finalized app names.

```bash
APP_SLUG="myapp"
FLY_ORG="<org>"

fly apps create "${APP_SLUG}-backend-staging" --org "$FLY_ORG"
fly apps create "${APP_SLUG}-backend-prod" --org "$FLY_ORG"
fly apps create "${APP_SLUG}-frontend-staging" --org "$FLY_ORG"
fly apps create "${APP_SLUG}-frontend-prod" --org "$FLY_ORG"
fly apps create "${APP_SLUG}-backend-builds" --org "$FLY_ORG"
fly apps create "${APP_SLUG}-frontend-builds" --org "$FLY_ORG"
```

The Fly config files should live under `fly/`:

```text
fly/backend-staging.toml
fly/backend-prod.toml
fly/frontend-staging.toml
fly/frontend-prod.toml
```

Backend configs should define a migration-only `release_command`. Frontend
configs should pass runtime public config through environment variables that the
container writes to `env.js` at startup.

The checked-in `fly/*.toml` files may contain template `app = "myapp-*"` values.
Replace those values for manual Fly commands, or rely on CI passing the target
app explicitly with `fly deploy --app "$APP_NAME"`.

## Fly Secrets

Set backend secrets per environment. Pydantic settings read environment variables
directly; do not add an application prefix.

```bash
fly secrets set -a myapp-backend-staging \
  ENVIRONMENT="staging" \
  PROJECT_NAME="Full Stack FastAPI Project" \
  FRONTEND_HOST="https://app-staging.example.com" \
  BACKEND_CORS_ORIGINS="https://app-staging.example.com" \
  DATABASE_URL="postgresql+psycopg://app_runtime:<runtime-password>@<host>:5432/postgres?sslmode=require" \
  DATABASE_URL_DIRECT="postgresql+psycopg://app_migrator:<migration-password>@<direct-host>:5432/postgres?sslmode=require" \
  SECRET_KEY="<generated-secret>" \
  FIRST_SUPERUSER="admin@example.com" \
  FIRST_SUPERUSER_PASSWORD="<generated-password>" \
  WEB_CONCURRENCY="1" \
  SQLALCHEMY_POOL_SIZE="2" \
  SQLALCHEMY_MAX_OVERFLOW="0"
```

Set optional backend secrets when the service is configured to use them:

```bash
fly secrets set -a myapp-backend-staging \
  SMTP_HOST="<smtp-host>" \
  SMTP_USER="<smtp-user>" \
  SMTP_PASSWORD="<smtp-password>" \
  EMAILS_FROM_EMAIL="info@example.com" \
  SENTRY_DSN="<sentry-dsn>"
```

Set frontend runtime config separately:

```bash
fly secrets set -a myapp-frontend-staging \
  API_BASE_URL="https://api-staging.example.com"
```

Repeat the same shape for production with production hosts, database URLs, and
secrets.

Generate secret values with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Do not set `GIT_SHA` as a Fly secret. CI should pass it as build metadata so the
image carries the revision it was built from.

## Domains

Fly provides `*.fly.dev` hostnames by default. Add custom domains after the apps
exist:

```bash
fly certs add -a myapp-frontend-staging app-staging.example.com
fly certs add -a myapp-backend-staging api-staging.example.com
fly certs add -a myapp-frontend-prod app.example.com
fly certs add -a myapp-backend-prod api.example.com
```

Create DNS records as instructed by `fly certs show`.

## CI/CD

CI should build backend and frontend images once, push them to the Fly registry,
and deploy exact image digests. The staging deploy should depend on the quality
gate and both image builds.

Production promotion takes a successful `CI/CD` workflow run ID, downloads the
`backend-digest` and `frontend-digest` artifacts from that run, validates that
both artifacts are Fly registry `sha256` digest refs, and deploys those exact
digests. Do not type image digests into the production workflow by hand.

Required GitHub Actions secrets:

- `FLY_API_TOKEN_BUILDS`
- `FLY_API_TOKEN_STAGING`
- `FLY_API_TOKEN_PROD`
- Any release or coverage service tokens used by the quality gate.

Required GitHub Actions variables:

- `BACKEND_REGISTRY_APP`
- `FRONTEND_REGISTRY_APP`
- `STAGING_BACKEND_APP`
- `STAGING_FRONTEND_APP`
- `PROD_BACKEND_APP`
- `PROD_FRONTEND_APP`

Optional GitHub Actions variables:

- `STAGING_BACKEND_URL`
- `STAGING_FRONTEND_URL`

`BACKEND_REGISTRY_APP` and `FRONTEND_REGISTRY_APP` should be repository-level
variables because the build jobs do not run in a deployment environment.
Runtime app names and public smoke-test URLs can be environment-level variables.
If `STAGING_BACKEND_URL` or `STAGING_FRONTEND_URL` is omitted, CI derives the
default Fly hostname from the corresponding staging app variable.

Promote a successful staging run to production with:

```bash
gh workflow run deploy-production.yml -f ci_cd_run_id=<successful-ci-cd-run-id>
```

The deployment workflow must use GitHub-hosted runners. Remote-server deploys,
build-on-server deploys, and the local Compose stack are not supported
deployment targets.

## Manual Deploys

Prefer CI for normal deploys. For a manual deploy with an already-built image:

```bash
fly deploy \
  --app "$STAGING_BACKEND_APP" \
  --config fly/backend-staging.toml \
  --image "registry.fly.io/${BACKEND_REGISTRY_APP}@sha256:<digest>"
```

Deploy frontend the same way with the frontend app, config, and image digest.

## Rollback

Rollback application code by redeploying the previous image digest:

```bash
fly deploy \
  --app "$PROD_BACKEND_APP" \
  --config fly/backend-prod.toml \
  --image "registry.fly.io/${BACKEND_REGISTRY_APP}@sha256:<previous-digest>"
```

Use the matching frontend digest if the rollback includes frontend changes.

Database migrations must follow expand-then-contract discipline because Fly runs
the backend release command before replacing old machines. Alembic `downgrade`
can exist for local and emergency use, but the normal rollback path is to deploy
code that remains compatible with the already-applied schema.

For data loss or corruption, restore the database through Supabase point-in-time
recovery or the backup/restore process available on the active Supabase plan.
Validate the restored database before pointing production traffic at it.

## Legacy Environment Cutover

Any old remote-server staging environment is transition-only. Do not add new
deploy instructions for it, and remove the old environment once Fly staging is
provisioned and validated.
