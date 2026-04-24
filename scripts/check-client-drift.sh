#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"

cleanup() {
    rm -rf "$TMP_DIR"
}

trap cleanup EXIT

OPENAPI_TMP="$TMP_DIR/openapi.json"
CLIENT_TMP="$TMP_DIR/client"

echo "Generating OpenAPI schema into temporary output..."
(
    cd "$PROJECT_ROOT/backend"
    uv run python -c "import app.main; import json; print(json.dumps(app.main.app.openapi()))" > "$OPENAPI_TMP"
)

echo "Generating frontend client into temporary output..."
(
    cd "$PROJECT_ROOT/frontend"
    OPENAPI_INPUT="$OPENAPI_TMP" OPENAPI_OUTPUT="$CLIENT_TMP" bun run generate-client
    bunx biome format --write "$OPENAPI_TMP"
)

if [ ! -f "$PROJECT_ROOT/frontend/openapi.json" ]; then
    echo "frontend/openapi.json is missing. Run: just generate-client" >&2
    exit 1
fi

if ! diff -u "$PROJECT_ROOT/frontend/openapi.json" "$OPENAPI_TMP"; then
    echo "frontend/openapi.json is stale. Run: just generate-client" >&2
    exit 1
fi

if ! diff -ruN "$PROJECT_ROOT/frontend/src/client" "$CLIENT_TMP"; then
    echo "frontend/src/client is stale. Run: just generate-client" >&2
    exit 1
fi

echo "Generated OpenAPI schema and frontend client are current."
