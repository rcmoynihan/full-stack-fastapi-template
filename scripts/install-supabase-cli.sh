#!/usr/bin/env bash
set -euo pipefail

SUPABASE_CLI_VERSION="${SUPABASE_CLI_VERSION:-2.72.7}"
INSTALL_DIR="${INSTALL_DIR:-/usr/local/bin}"
ARCHIVE_NAME="supabase_linux_amd64.tar.gz"
DOWNLOAD_URL="https://github.com/supabase/cli/releases/download/v${SUPABASE_CLI_VERSION}/${ARCHIVE_NAME}"

if command -v supabase >/dev/null 2>&1; then
    INSTALLED_VERSION="$(supabase --version | head -n 1 | awk '{print $1}')"
    if [ "$INSTALLED_VERSION" = "$SUPABASE_CLI_VERSION" ]; then
        exit 0
    fi
fi

curl -fsSL "$DOWNLOAD_URL" | sudo tar -xz -C "$INSTALL_DIR" supabase
supabase --version
