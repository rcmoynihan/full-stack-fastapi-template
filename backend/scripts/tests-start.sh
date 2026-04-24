#! /usr/bin/env bash
set -euo pipefail

# Tests must use the local Docker Compose Postgres by default. Do not let a
# developer, dotenv, or deployment DATABASE_URL redirect destructive tests.
export POSTGRES_SERVER="${POSTGRES_SERVER:-localhost}"
export POSTGRES_PORT="${POSTGRES_PORT:-5432}"
export POSTGRES_DB="${POSTGRES_DB:-app}"
export POSTGRES_USER="${POSTGRES_USER:-postgres}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-changethis}"
export ENVIRONMENT="local"
export DATABASE_URL="postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_SERVER}:${POSTGRES_PORT}/${POSTGRES_DB}"
export DATABASE_URL_DIRECT="$DATABASE_URL"

set -x
bash scripts/test.sh "$@"
