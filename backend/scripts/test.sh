#!/usr/bin/env bash

set -euo pipefail

# Backend tests must never inherit deployment database URLs from the shell or
# from the root .env file. Export an explicit local URL so Pydantic settings
# cannot fall back to DATABASE_URL/DATABASE_URL_DIRECT values in dotenv.
: "${POSTGRES_SERVER:=localhost}"
: "${POSTGRES_PORT:=5432}"
: "${POSTGRES_DB:=app}"
: "${POSTGRES_USER:=postgres}"
: "${POSTGRES_PASSWORD:=changethis}"

postgres_server_lower="$(printf "%s" "$POSTGRES_SERVER" | tr "[:upper:]" "[:lower:]")"
if printf "%s" "$postgres_server_lower" | grep -q "supabase"; then
    echo "Refusing to run backend tests against Supabase host: $POSTGRES_SERVER" >&2
    exit 1
fi

export ENVIRONMENT="local"
export POSTGRES_SERVER
export POSTGRES_PORT
export POSTGRES_DB
export POSTGRES_USER
export POSTGRES_PASSWORD
export DATABASE_URL="postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_SERVER}:${POSTGRES_PORT}/${POSTGRES_DB}"
export DATABASE_URL_DIRECT="$DATABASE_URL"

python app/tests_pre_start.py

set -x
coverage run -m pytest tests/ "$@"
coverage report --fail-under=92
coverage html --title "coverage"
