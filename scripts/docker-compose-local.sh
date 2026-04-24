#!/usr/bin/env bash
set -euo pipefail

case "${LOCAL_DOCKER_PLATFORM:-}" in
    "")
        case "$(uname -m)" in
            arm64 | aarch64)
                export DOCKER_DEFAULT_PLATFORM="linux/arm64"
                ;;
            x86_64 | amd64)
                export DOCKER_DEFAULT_PLATFORM="linux/amd64"
                ;;
            *)
                unset DOCKER_DEFAULT_PLATFORM
                ;;
        esac
        ;;
    "native")
        unset DOCKER_DEFAULT_PLATFORM
        ;;
    *)
        export DOCKER_DEFAULT_PLATFORM="$LOCAL_DOCKER_PLATFORM"
        ;;
esac

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_ENV_ARGS=()

if [ -f "$PROJECT_ROOT/.env" ]; then
    COMPOSE_ENV_ARGS+=(--env-file "$PROJECT_ROOT/.env")
fi

if [ -f "$PROJECT_ROOT/.env.supabase.local" ]; then
    COMPOSE_ENV_ARGS+=(--env-file "$PROJECT_ROOT/.env.supabase.local")
fi

exec docker compose "${COMPOSE_ENV_ARGS[@]}" "$@"
