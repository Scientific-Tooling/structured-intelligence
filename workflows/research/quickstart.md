# A paper, a question, a source-linked brief

Scientific Tooling now manages the RKS/APW workspace, reading session, import
previews and reader process for you. Use one PDF and one research question per
workspace. The same commands work on Windows, Linux and macOS.

## Install once

Use Python 3.10–3.12 with pip and Git. Install into your chosen Python environment:

```text
python -m pip install "git+https://github.com/Scientific-Tooling/structured-intelligence.git"
scientific-tooling doctor
```

This source installation includes compatible RKS and APW dependencies and the
prebuilt reader. No Node.js, model API key or MCP setup is required. On systems
where the interpreter is named `python3`, use it for the installation command.
If the environment's scripts directory is not on PATH, use
`python -m scientific_tooling` in place of `scientific-tooling`.

## Open your paper

```text
scientific-tooling start "paper.pdf" --question "What evidence addresses my question?" --workspace "my-review"
```

The reader opens automatically. Highlight a passage, select it under **Evidence &
brief**, and click **Preview selected evidence**. Inspect the quotes and comments,
then click **Import evidence & create brief**. Download the brief or open its
supporting passages. Imported observations remain unreviewed.

The CLI assigns and remembers an available local port. A second terminal is not
needed. If the browser cannot open automatically, follow the returned URL.

## Let your agent coordinate

Install the bundled skill into the skills directory used by your agent:

```text
scientific-tooling skill --dest "~/.codex/skills"
```

For another host, give its skills directory, such as `~/.claude/skills`.
Reload skills in that host, then ask:

> Use paper-to-brief to read this PDF and collect evidence relevant to my question.

The agent reads the source with its available tools, proposes passages, and uses
the same workflow commands. It can save exact quotes as unreviewed annotations.
You can inspect the evidence alongside the original PDF. The CLI itself does not
call a model or upload your PDF to a hosted service; your chosen agent host has
its own data-handling behavior.

## Continue later

```text
scientific-tooling resume --workspace "my-review"
scientific-tooling status --workspace "my-review"
scientific-tooling stop --workspace "my-review"
```

Resume preserves the paper, question, session, previews and imported evidence.
Stop the reader when finished; resume it to use passage links again. Back up the
whole workspace with all writers stopped. Keep its original absolute location
when restoring this first version; citations and retained source paths use it.

## Agent and advanced commands

Every command supports `--json`. `status` returns annotations and notes while the
reader is running. Preview uses only explicitly selected IDs:

```text
scientific-tooling preview --workspace "my-review" --annotation ANNOTATION_ID --json
scientific-tooling apply PREVIEW_ID --workspace "my-review" --json
scientific-tooling brief --workspace "my-review" --json
```

Use the IDs returned by status/preview. Exact replays do not duplicate evidence.
Edits after preview require a fresh preview. Changed imported revisions require
explicit `apply --accept-updates`; other conflicts remain blocked. Old bundles,
plans and briefs stay available in the workspace.

If interrupted during setup, use `resume`. If an import succeeded but its reply
was lost, retry the same preview ID. If brief generation failed after import,
run `brief` again. The reader log is `server.log` in the workspace. A saved port
occupied by another program is reported without terminating that program or
silently changing existing citation addresses. For SSH, use `--no-open` and
forward the returned port to the browser machine.

The [Windows](windows-quickstart.md) and [Linux/macOS](unix-quickstart.md) manual
walkthroughs remain useful for inspecting the individual underlying tools.
