#!/usr/bin/env bash
# Compatibility entry point; use start_localharness.sh for new workflows.
set -Eeuo pipefail
readonly PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
exec bash "$PROJECT_DIR/start_localharness.sh" "$@"
