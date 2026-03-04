# Skills

Skills are reusable capabilities. They should be composable, testable, and well-documented.

## Layout

Each skill should contain:

- `config.yaml`: metadata and runtime entrypoint contract.
- `SKILL.md`: execution guidance and constraints.
- `scripts/`: utilities used by the skill.
- `references/`: optional targeted references.
- `assets/`: reusable templates or static inputs.

Use `skills/_templates/skill` as the starting point.

## Registry Schema

`skills/registry.yaml` uses this shape:

```yaml
skills:
  - id: <skill-id>
    name: <human-friendly-name>
    version: <semver>
    path: skills/<skill-folder>
    config: skills/<skill-folder>/config.yaml
```

`config.yaml` required keys:
- `id`
- `name`
- `version`
- `owner`
- `description`
- `entrypoints`
- `default_tools`
