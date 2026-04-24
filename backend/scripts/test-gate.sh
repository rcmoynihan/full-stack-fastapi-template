#!/usr/bin/env bash

set -euo pipefail
set -x

COVERAGE_DIR="$(mktemp -d)"

cleanup() {
    rm -rf "$COVERAGE_DIR"
}

trap cleanup EXIT

export COVERAGE_FILE="$COVERAGE_DIR/.coverage"
export PYTHONDONTWRITEBYTECODE=1

coverage run -m pytest -p no:cacheprovider tests/ "$@"
coverage report --fail-under=92
