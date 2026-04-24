#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:?Usage: smoke_frontend.sh <base-url> <expected-api-base-url>}"
EXPECTED_API_BASE_URL="${2:?Usage: smoke_frontend.sh <base-url> <expected-api-base-url>}"

echo "--- Page loads ---"
curl -sf "${BASE_URL}" > /dev/null || {
  echo "FAIL: page load"
  exit 1
}

echo "--- env.js contains expected runtime API URL ---"
ENV_JS_FILE="$(mktemp)"
trap 'rm -f "$ENV_JS_FILE"' EXIT
curl -sf "${BASE_URL}/env.js" -o "$ENV_JS_FILE" || {
  echo "FAIL: env.js"
  exit 1
}
python - "$ENV_JS_FILE" "$EXPECTED_API_BASE_URL" <<'PY'
import json
import re
import sys
from pathlib import Path

env_js_path = Path(sys.argv[1])
expected_api_base_url = sys.argv[2]

if not expected_api_base_url.strip():
    print("FAIL: expected API URL must be non-empty")
    sys.exit(1)

env_js = env_js_path.read_text(encoding="utf-8")
assignment_match = re.fullmatch(
    r"\s*window\.APP_CONFIG\s*=\s*\{(?P<body>.*)\}\s*;?\s*",
    env_js,
    flags=re.DOTALL,
)
if assignment_match is None:
    print("FAIL: env.js does not assign window.APP_CONFIG to an object")
    sys.exit(1)

try:
    property_match = re.search(
        r'(?:"API_BASE_URL"|API_BASE_URL)\s*:\s*(?P<value>"(?:\\.|[^"\\])*")',
        assignment_match.group("body"),
        flags=re.DOTALL,
    )
    if property_match is None:
        print("FAIL: env.js APP_CONFIG.API_BASE_URL is missing")
        sys.exit(1)
    api_base_url = json.loads(property_match.group("value"))
except json.JSONDecodeError as exc:
    print(f"FAIL: env.js APP_CONFIG.API_BASE_URL is not a valid JSON string: {exc}")
    sys.exit(1)

if not isinstance(api_base_url, str) or not api_base_url.strip():
    print("FAIL: env.js APP_CONFIG.API_BASE_URL is missing or empty")
    sys.exit(1)

if api_base_url != expected_api_base_url:
    print(
        "FAIL: env.js APP_CONFIG.API_BASE_URL mismatch: "
        f"expected {expected_api_base_url!r}, got {api_base_url!r}"
    )
    sys.exit(1)
PY

echo ""
echo "Frontend smoke tests passed"
