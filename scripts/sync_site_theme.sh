#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_REPO="${SCIENTIFIC_TOOLING_HOME_REPO:-/mnt/c/Users/mingz/Codes/Scientific-Tooling.github.io}"
SOURCE_THEME="$SOURCE_REPO/theme.css"

if [[ ! -f "$SOURCE_THEME" ]]; then
  echo "Missing source theme: $SOURCE_THEME" >&2
  exit 1
fi

cp "$SOURCE_THEME" "$ROOT_DIR/docs/theme.css"
cp "$SOURCE_THEME" "$ROOT_DIR/manuscripts/theme.css"

echo "Synced theme.css from $SOURCE_REPO"
