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

exec docker compose "$@"
