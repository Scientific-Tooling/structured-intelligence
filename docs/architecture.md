# Architecture

## Design Goals

1. Fast onboarding for new agents and skills.
2. Clear boundaries between reusable capability (skills) and orchestration behavior (agents).
3. Repeatable workflows for coding, research, and writing.
4. Traceable outputs and source provenance.

## Information Flow

1. `prompts/` and `knowledge/sources/` provide shared inputs.
2. `agents/` orchestrate task execution, optionally invoking `skills/`.
3. `workflows/` define how teams run work end-to-end.
4. Outputs are saved to `knowledge/outputs/` and can be reused in future runs.
