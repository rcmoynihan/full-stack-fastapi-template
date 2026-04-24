#!/usr/bin/env bash

set -euo pipefail
set -x

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE="$PROJECT_ROOT/scripts/docker-compose-local.sh"

cleanup() {
    "$COMPOSE" down -v --remove-orphans
}

trap cleanup EXIT

"$COMPOSE" build
"$COMPOSE" down -v --remove-orphans
"$COMPOSE" up -d --wait db mailcatcher backend
"$COMPOSE" exec -T backend bash scripts/tests-start.sh "$@"
