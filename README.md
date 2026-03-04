# Structured Intelligence

A repository for production-ready AI assets that improve coding, research, and writing throughput.

## What Lives Here

- `agents/`: Task-specific agents with prompts, config, and smoke tests.
- `skills/`: Reusable capabilities packaged with `config.yaml`, `SKILL.md`, scripts, references, and assets.
- `workflows/`: End-to-end operating playbooks for coding, research, and writing.
- `knowledge/`: Reusable source material, notes, and generated outputs.
- `prompts/`: Shared persona and task prompt libraries.
- `scripts/`: Local automation for scaffolding and validation.
- `docs/`: Architecture and contribution conventions.

## Quick Start

### Use The `research` Skill

After cloning this repository:

```bash
# Default target: Codex (~/.codex/skills)
./scripts/install_skill.sh research

# Claude Code (~/.claude/skills)
./scripts/install_skill.sh research --tool claude

# Other tools (custom skills directory)
./scripts/install_skill.sh research --dest ~/.my-tool/skills
```

Then restart your tool session and ask for `research`.

### Build This Repository

1. Add an agent from `agents/_templates/agent`.
2. Add a skill from `skills/_templates/skill`.
3. Register both in their `registry.yaml` files.
4. Follow the relevant workflow under `workflows/`.
5. Run `./scripts/validate_structure.sh` before commit.
