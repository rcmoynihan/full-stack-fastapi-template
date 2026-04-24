# Default recipe: show available commands.
default:
    @just --list

# Start the local stack with Docker Compose.
dev:
    docker compose up -d --wait

# Start the local stack with Docker Compose watch for backend/container changes.
dev-watch:
    docker compose -f compose.yml -f compose.override.yml -f compose.watch.yml watch

# Stop local services.
down:
    docker compose down

# Reset the local database, then run migrations and bootstrap data.
dev-reset-db:
    docker compose down -v --remove-orphans
    docker compose up -d --wait db
    cd backend && uv run bash scripts/prestart.sh

# Run the backend development server on the host.
backend-dev:
    cd backend && uv run fastapi dev app/main.py

# Run backend tests.
backend-test:
    cd backend && uv run bash scripts/tests-start.sh

# Run backend linting and type checks.
backend-lint:
    cd backend && uv run bash scripts/lint.sh

# Run backend formatting.
backend-fmt:
    cd backend && uv run bash scripts/format.sh

# Run the frontend development server on the host.
frontend-dev:
    cd frontend && bun run dev

# Run frontend linting as a read-only check.
frontend-lint:
    cd frontend && bun run lint:ci

# Run frontend formatting and safe fixes.
frontend-fmt:
    cd frontend && bun run lint

# Apply backend migrations locally.
migrate:
    cd backend && uv run alembic upgrade head

# Create a backend migration from SQLModel metadata changes.
migrate-create name:
    cd backend && uv run alembic revision --autogenerate -m "{{name}}"

# Regenerate the frontend API client from backend OpenAPI spec.
generate-client:
    bash scripts/generate-client.sh

# Run the full read-only validation gate.
check:
    #!/usr/bin/env bash
    set -euo pipefail

    PROJECT_ROOT="$(pwd)"
    SERVICES_TO_STOP=""
    SERVICES_TO_REMOVE=""
    FRONTEND_BUILD_DIR=""

    require_docker() {
        if ! command -v docker >/dev/null 2>&1; then
            echo "Docker is required for 'just check' because backend tests need local Postgres and mailcatcher." >&2
            echo "Install Docker Desktop or another Docker Engine with Compose v2, then retry." >&2
            exit 1
        fi

        if ! docker info >/dev/null 2>&1; then
            echo "Docker is installed, but the Docker daemon is not reachable." >&2
            echo "Start Docker Desktop or your Docker Engine, then retry 'just check'." >&2
            exit 1
        fi

        if ! docker compose version >/dev/null 2>&1; then
            echo "Docker Compose v2 is required for 'just check'." >&2
            echo "Install or enable the 'docker compose' plugin, then retry." >&2
            exit 1
        fi
    }

    is_service_running() {
        local service="$1"
        local container_id

        container_id="$(docker compose ps --status running -q "$service" 2>/dev/null || true)"
        [ -n "$container_id" ]
    }

    plan_service_cleanup() {
        local service="$1"
        local container_id

        container_id="$(docker compose ps -aq "$service" 2>/dev/null || true)"
        if ! is_service_running "$service"; then
            SERVICES_TO_STOP="$SERVICES_TO_STOP $service"
            if [ -z "$container_id" ]; then
                SERVICES_TO_REMOVE="$SERVICES_TO_REMOVE $service"
            fi
        fi
    }

    cleanup() {
        if [ -n "$SERVICES_TO_STOP" ]; then
            docker compose stop $SERVICES_TO_STOP
        fi
        if [ -n "$SERVICES_TO_REMOVE" ]; then
            docker compose rm -f $SERVICES_TO_REMOVE
        fi
        if [ -n "$FRONTEND_BUILD_DIR" ]; then
            rm -rf "$FRONTEND_BUILD_DIR"
        fi
    }

    export DATABASE_URL=""
    export DATABASE_URL_DIRECT=""
    export ENVIRONMENT="local"
    export POSTGRES_SERVER="localhost"
    export POSTGRES_PORT="5432"
    export POSTGRES_DB="app"
    export POSTGRES_USER="postgres"
    export POSTGRES_PASSWORD="changethis"

    require_docker
    plan_service_cleanup db
    plan_service_cleanup mailcatcher
    trap cleanup EXIT

    echo "=== Lockfile check ==="
    uv lock --locked
    (cd "$PROJECT_ROOT/frontend" && bun install --frozen-lockfile)

    echo "=== Local service setup ==="
    docker compose up -d --wait db mailcatcher
    (cd "$PROJECT_ROOT/backend" && uv run bash scripts/prestart.sh)

    echo "=== Backend lint + typecheck ==="
    (cd "$PROJECT_ROOT/backend" && uv run bash scripts/lint.sh)

    echo "=== Backend tests + coverage (92% gate) ==="
    (cd "$PROJECT_ROOT/backend" && uv run bash scripts/test-gate.sh)

    echo "=== Frontend lint (read-only) ==="
    (cd "$PROJECT_ROOT/frontend" && bun run lint:ci)

    echo "=== Frontend typecheck ==="
    FRONTEND_BUILD_DIR="$(mktemp -d)"
    (cd "$PROJECT_ROOT/frontend" && bunx tsc -p tsconfig.build.json && bunx vite build --outDir "$FRONTEND_BUILD_DIR" --emptyOutDir)

    echo "=== API client drift check ==="
    bash "$PROJECT_ROOT/scripts/check-client-drift.sh"

    echo "=== Read-only pre-commit hooks ==="
    uv run --project "$PROJECT_ROOT/backend" prek run --config "$PROJECT_ROOT/.pre-commit-config.yaml" --all-files --stage pre-push

    echo ""
    echo "All checks passed"

# Run mutating formatters/fixers.
fix:
    cd backend && uv run bash scripts/format.sh
    bash scripts/generate-client.sh
    cd frontend && bun run lint

# Create the configured first superuser if missing.
create-superuser:
    cd backend && uv run python -m app.commands.create_superuser

# Seed demo data.
seed-demo:
    cd backend && uv run python -m app.commands.seed_demo

# Run e2e tests against the Docker Compose stack.
test-e2e:
    docker compose run --rm playwright bunx playwright test
