#!/usr/bin/env bash
set -e
set -x

# Local development prestart: wait for DB, migrate, bootstrap.
# In production, migrations run via release command scripts/migrate.sh.

python -m app.commands.ensure_database

python app/backend_pre_start.py

alembic upgrade head

python -m app.commands.create_superuser
