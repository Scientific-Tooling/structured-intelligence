#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/.site"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

cp "$ROOT_DIR/docs/index.html" "$OUT_DIR/index.html"
cp "$ROOT_DIR/docs/sitemap.xml" "$OUT_DIR/sitemap.xml"
cp "$ROOT_DIR/docs/robots.txt" "$OUT_DIR/robots.txt"

mkdir -p "$OUT_DIR/assets"
cp -R "$ROOT_DIR/docs/assets/." "$OUT_DIR/assets/"

# Manuscript pages reference ../../logo.svg (relative to manuscripts/<name>/)
cp "$ROOT_DIR/docs/assets/logo.svg" "$OUT_DIR/logo.svg"
cp "$ROOT_DIR/docs/assets/logo.png" "$OUT_DIR/logo.png"

# Manuscript pages fetch article markdown via ../../docs/articles/<name>.md
mkdir -p "$OUT_DIR/docs/articles"
cp -R "$ROOT_DIR/docs/articles/." "$OUT_DIR/docs/articles/"

mkdir -p "$OUT_DIR/manuscripts"
cp -R "$ROOT_DIR/manuscripts/." "$OUT_DIR/manuscripts/"

echo "Built Pages site at $OUT_DIR"
