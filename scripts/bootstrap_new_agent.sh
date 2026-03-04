#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <agent-id>"
  exit 1
fi

AGENT_ID="$1"
ROOT="agents/${AGENT_ID}"

if [[ -e "$ROOT" ]]; then
  echo "Agent already exists: $ROOT"
  exit 1
fi

mkdir -p "$ROOT/prompts" "$ROOT/tests"
cp agents/_templates/agent/AGENT.md "$ROOT/AGENT.md"
cp agents/_templates/agent/config.yaml "$ROOT/config.yaml"
cp agents/_templates/agent/prompts/system.md "$ROOT/prompts/system.md"
cp agents/_templates/agent/prompts/task.md "$ROOT/prompts/task.md"
cp agents/_templates/agent/tests/smoke.md "$ROOT/tests/smoke.md"

echo "Created $ROOT from template"
