#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/.site"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

cp -R "$ROOT_DIR/docs/." "$OUT_DIR/"

if [[ -d "$ROOT_DIR/manuscripts" ]]; then
  cp -R "$ROOT_DIR/manuscripts" "$OUT_DIR/manuscripts"
fi

echo "Built Pages site at $OUT_DIR"
