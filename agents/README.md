# Agents

Agents are orchestrators. They decide sequence, tool usage, and delegation strategy.

## Layout

Each agent should contain:

- `AGENT.md`: behavior contract and operating rules.
- `config.yaml`: metadata, version, entrypoints.
- `prompts/`: system/task prompt fragments.
- `tests/`: smoke and regression checks.

Use `agents/_templates/agent` as the starting point.
