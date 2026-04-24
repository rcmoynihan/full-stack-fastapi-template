#!/bin/sh
set -e

CONFIG_JSON="$(jq -n \
  --arg api_base_url "${API_BASE_URL:-}" \
  --arg supabase_url "${SUPABASE_URL:-}" \
  --arg supabase_publishable_key "${SUPABASE_PUBLISHABLE_KEY:-}" \
  '{API_BASE_URL: $api_base_url, SUPABASE_URL: $supabase_url, SUPABASE_PUBLISHABLE_KEY: $supabase_publishable_key}' | sed 's/</\\u003c/g; s/>/\\u003e/g; s/&/\\u0026/g')"
printf 'window.APP_CONFIG = %s;\n' "$CONFIG_JSON" > /usr/share/nginx/html/env.js

exec nginx -g 'daemon off;'
