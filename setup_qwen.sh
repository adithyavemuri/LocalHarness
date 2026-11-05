#!/usr/bin/env bash
# Compatibility entry point; use setup_localharness.sh for new workflows.
set -Eeuo pipefail
readonly PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
exec bash "$PROJECT_DIR/setup_localharness.sh" "$@"
