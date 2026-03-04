#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_DIR="$ROOT_DIR/skills/research"
REF_DIR="$SKILL_DIR/references"

if [[ ! -d "$SKILL_DIR" ]]; then
  echo "Missing skill directory: $SKILL_DIR"
  exit 1
fi

required_files=(
  "$REF_DIR/system_prompt.md"
  "$REF_DIR/research_protocol.md"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "Missing research reference file: $file"
    exit 1
  fi
done

echo "Research skill is self-contained; sync not required."
