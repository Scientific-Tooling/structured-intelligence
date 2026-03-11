#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "install_researcher_skill.sh is deprecated; installing the current 'research' skill." >&2
exec "$ROOT_DIR/scripts/install_skill.sh" research "$@"
