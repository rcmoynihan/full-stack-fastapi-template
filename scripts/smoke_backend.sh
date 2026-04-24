#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:?Usage: smoke_backend.sh <base-url>}"

echo "--- Health check ---"
curl -sf "${BASE_URL}/api/v1/utils/health-check/" > /dev/null || {
  echo "FAIL: health check"
  exit 1
}

echo "--- OpenAPI schema accessible ---"
curl -sf "${BASE_URL}/api/v1/openapi.json" > /dev/null || {
  echo "FAIL: openapi"
  exit 1
}

echo ""
echo "Backend smoke tests passed"
