# Your papers, one question, a source-linked brief

Scientific Tooling now manages the RKS/APW workspace, reading session, import
previews and reader process for you. Keep one or more PDFs under a shared research
question in each project workspace. The same commands work on Windows, Linux and macOS.

For planned capabilities and completion criteria, see the [sci roadmap](../../docs/sci-roadmap.md).

## Install once

Use Python 3.12 or newer with pip and Git; **Python 3.14 is recommended**.
Install into your chosen Python environment:

```text
python -m pip install --upgrade "git+https://github.com/Scientific-Tooling/structured-intelligence.git"
sci doctor
```

This source installation includes compatible RKS and APW dependencies and the
prebuilt reader. No Node.js, model API key or MCP setup is required. On systems
where the interpreter is named `python3`, use it for the installation command.
If the environment's scripts directory is not on PATH, use
`python -m scientific_tooling` in place of `sci`.

`sci` is the short command. This workflow is version 0.3.1. The original
`scientific-tooling` command remains an alias. Run the installation command above
again to upgrade an existing environment; saved workspaces continue to work.

## Open your paper

```text
sci start "paper.pdf" --question "What evidence addresses my question?" --workspace "my-review"
```

The reader opens automatically. Highlight a passage, check it in the **Evidence**
tab, and click **Preview selected evidence**. Inspect the quotes and comments,
then click **Import evidence & create brief**. Open the **Brief** tab to download
the brief or return to its supporting passages. Imported observations remain unreviewed.

Use **Notes** to write a thought and link it to supporting highlights. Drag the
sidebar edges to resize them, or choose **Focus on paper** for more reading space.
On a phone, the Papers and Workspace buttons open one panel at a time.

The CLI assigns and remembers an available local port. A second terminal is not
needed. If the browser cannot open automatically, follow the returned URL.

## Let your agent coordinate

Install the bundled skill into the skills directory used by your agent:

```text
sci skill --dest "~/.codex/skills"
```

For another host, give its skills directory, such as `~/.claude/skills`.
Reload skills in that host, then ask:

> Use paper-to-brief to read these PDFs and collect evidence relevant to my question.

The agent reads the source with its available tools, proposes passages, and uses
the same workflow commands. It can save exact quotes as unreviewed annotations.
You can inspect the evidence alongside the original PDF. The CLI itself does not
call a model or upload your PDF to a hosted service; your chosen agent host has
its own data-handling behavior.

## Work with several papers

Pass several paths to `start`, or grow an existing project with `add`:

```text
sci start "paper-a.pdf" "paper-b.pdf" --question "Which methods fit my dataset?" --workspace "methods"
sci add "paper-c.pdf" --workspace "methods"
sci papers --workspace "methods"
sci open p2 --workspace "methods"
sci brief --workspace "methods"
```

Switch papers using **Project papers** in the reader. Use **Refresh project** after
adding papers. Each paper keeps its own annotations, reading session and preview;
all papers share the project's evidence database and question. Identical PDF bytes
are reused, even under a different filename. Different versions are separate papers.

The project brief groups quotations by paper and shows evidence coverage, review
status and source links. Papers without imported evidence remain visible as gaps.
It does not infer agreement, contradictions or a scientific conclusion. An agent
can use the evidence to propose a synthesis, clearly distinguished from source text.

For projects with several papers, `annotate` and `preview` require `--paper p2`.
Use `status --paper p2 --json` to inspect that paper, or `resume --paper p2` to open
it. `apply` uses the inspected preview ID to identify its paper. `brief` always
includes the whole project. Paper keys such as `p2` are stable within the workspace;
the returned RKS paper IDs also work.

## Continue later

```text
sci resume --workspace "my-review"
sci status --workspace "my-review"
sci stop --workspace "my-review"
```

Resume preserves the papers, question, sessions, previews and imported evidence.
Stop the reader when finished; resume it to use passage links again. Back up the
whole workspace with all writers stopped. Keep its original absolute location
when restoring; citations and retained source paths use it.

Before upgrading an active reader, stop it with the old installation. Existing
single-paper workspaces migrate on their next saved operation. The original manifest
is retained as `workspace.v1.json`; sessions, previews, evidence and citation URLs
keep their identities. After migration, use sci 0.3.0 or later for that workspace.

## Agent and advanced commands

Every command supports `--json`. `status` returns annotations and notes while the
reader is running. Preview uses only explicitly selected IDs:

```text
sci preview --workspace "my-review" --paper p1 --annotation ANNOTATION_ID --json
sci apply PREVIEW_ID --workspace "my-review" --json
sci brief --workspace "my-review" --json
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

For debugging or developing integrations with the individual tools, see
[advanced manual operations](manual-operations/README.md).

Repository `main` also includes [project evidence search](../../docs/evidence-search.md)
and [comparison and human review](../../docs/comparisons.md), with matching RKS/APW
commits pinned for installation. These development features are not in the tagged
sci 0.3.1 release; independent scientific evaluation remains pending.

## Upgrading from Python 3.10 or 3.11

Version 0.2.0 raises the minimum Python version to 3.12. Stop an active reader
with the old environment's `sci stop --workspace "my-review"`, then create a
fresh Python 3.14 virtual environment and install using the command above.
Use the new environment's `sci resume --workspace "my-review"` to continue.
Keep the saved workspace at the same absolute path; it is separate from the
Python environment. Do not recreate it with `sci start` or copy an old virtual
environment into a new interpreter.

Core CI covers Python 3.12, 3.13, 3.14, and 3.15; 3.14 is the default for browser
and native shell workflow checks. Scientific Conda environments retain their
own pinned Python and analysis-library versions.
