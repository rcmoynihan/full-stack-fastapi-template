#!/usr/bin/env bash
set -e
set -x

# Run by Fly release_command: migrations only, no bootstrap.
# Use DATABASE_URL_DIRECT when configured to bypass runtime poolers for DDL.

if [ -n "${DATABASE_URL_DIRECT:-}" ]; then
  export DATABASE_URL="$DATABASE_URL_DIRECT"
fi

python app/backend_pre_start.py
alembic upgrade head
