#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/.site"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

cp "$ROOT_DIR/docs/index.html" "$OUT_DIR/index.html"
cp "$ROOT_DIR/docs/site.css" "$OUT_DIR/site.css"
cp "$ROOT_DIR/docs/logo.svg" "$OUT_DIR/logo.svg"
cp "$ROOT_DIR/docs/logo.png" "$OUT_DIR/logo.png"
cp "$ROOT_DIR/docs/social-preview.png" "$OUT_DIR/social-preview.png"
cp "$ROOT_DIR/docs/sitemap.xml" "$OUT_DIR/sitemap.xml"
cp "$ROOT_DIR/docs/robots.txt" "$OUT_DIR/robots.txt"

cp "$ROOT_DIR/docs/ncbi-eutilities-assistant-manuscript.md" \
  "$OUT_DIR/ncbi-eutilities-assistant-manuscript.md"
cp "$ROOT_DIR/docs/rpsblast-assistant-manuscript.md" \
  "$OUT_DIR/rpsblast-assistant-manuscript.md"

mkdir -p "$OUT_DIR/manuscripts"
cp -R "$ROOT_DIR/manuscripts/." "$OUT_DIR/manuscripts/"

echo "Built Pages site at $OUT_DIR"
