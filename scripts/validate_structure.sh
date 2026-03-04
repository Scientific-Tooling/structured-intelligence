#!/usr/bin/env bash
set -euo pipefail

required_paths=(
  "agents/registry.yaml"
  "skills/registry.yaml"
  "workflows/coding/default.md"
  "workflows/research/default.md"
  "workflows/writing/default.md"
  "docs/architecture.md"
  "README.md"
)

missing=0
for p in "${required_paths[@]}"; do
  if [[ ! -e "$p" ]]; then
    echo "Missing: $p"
    missing=1
  fi
done

if [[ "$missing" -ne 0 ]]; then
  echo "Structure validation failed"
  exit 1
fi

python3 scripts/validate_registry_schema.py

echo "Structure validation passed"
