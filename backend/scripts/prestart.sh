#!/usr/bin/env bash
set -e

load_env_defaults() {
    local env_file="$1"
    local key
    local value

    if [ ! -f "$env_file" ]; then
        return 0
    fi

    while IFS='=' read -r key value || [ -n "$key" ]; do
        case "$key" in
            "" | \#*)
                continue
                ;;
        esac

        case "$value" in
            \"*)
                value="${value#\"}"
                value="${value%\"}"
                ;;
            \'*)
                value="${value#\'}"
                value="${value%\'}"
                ;;
        esac

        if [ -z "${!key:-}" ]; then
            export "$key=$value"
        fi
    done < "$env_file"
}

# Local development prestart: wait for DB, migrate, bootstrap.
# In production, migrations run via release command scripts/migrate.sh.
load_env_defaults ../.env
load_env_defaults ../.env.supabase.local

set -x

python -m app.commands.ensure_database

python app/backend_pre_start.py

alembic upgrade head

python -m app.commands.create_superuser
