#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Backward-compatible alias for legacy script name.
exec "$ROOT_DIR/scripts/sync_research_skill.sh" "$@"
