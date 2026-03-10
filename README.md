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

### Use The `rpsblast-assistant` Skill

Install the skill:

```bash
# Default target: Codex (~/.codex/skills)
./scripts/install_skill.sh rpsblast-assistant

# Claude Code (~/.claude/skills)
./scripts/install_skill.sh rpsblast-assistant --tool claude
```

Then restart your tool session and use natural language.

Codex examples:

```text
Use $rpsblast-assistant to tell me what I need to download for a local RPS-BLAST workflow.

Use $rpsblast-assistant to download the minimal CDD database and rpsbproc annotation files into ./db and ./data.

Use $rpsblast-assistant to check whether my local setup is complete for running rpsblast with db/Cdd.

Use $rpsblast-assistant to run rpsblast on ./sequence.fasta against ./db/Cdd with E-value 0.01 and then post-process with rpsbproc.

Use $rpsblast-assistant to explain the format of sequence.out and tell me which part is the real tabular data.
```

Claude Code examples:

```text
Use rpsblast-assistant to tell me what I need to download for a local RPS-BLAST workflow.

Use rpsblast-assistant to download the minimal CDD database and rpsbproc annotation files into ./db and ./data.

Use rpsblast-assistant to check whether my local setup is complete for running rpsblast with db/Cdd.

Use rpsblast-assistant to run rpsblast on ./sequence.fasta against ./db/Cdd with E-value 0.01 and then post-process with rpsbproc.

Use rpsblast-assistant to explain the format of sequence.out and tell me which part is the real tabular data.
```

### Build This Repository

1. Add an agent from `agents/_templates/agent`.
2. Add a skill from `skills/_templates/skill`.
3. Register both in their `registry.yaml` files.
4. Follow the relevant workflow under `workflows/`.
5. Run `./scripts/validate_structure.sh` before commit.
