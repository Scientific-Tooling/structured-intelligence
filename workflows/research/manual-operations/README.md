# Advanced manual operations

Start with the [PDF-to-brief quick start](../quickstart.md) for normal use. It
handles workspace setup, source preservation, reading sessions, evidence
transfers and reader startup through `sci` or the bundled agent skill.

Use this reference when developing an integration, investigating a failed
handoff, or connecting tools to an existing RKS workspace. You manage each
component and its files explicitly.

- [Windows / PowerShell](windows.md)
- [Linux / macOS, Bash or zsh](unix.md)

Both references cover source installation, ingestion, reader startup, selected
evidence preview/import, brief generation, replay and backup. Their command
blocks are the canonical manual instructions; the website links here.

For individual interfaces, see [source reading](../source-reading.md),
[selected evidence import](../evidence-import.md), and
[passage-linked briefs](../source-linked-brief.md).

## Maintaining the reference

From the repository root, run the native shell syntax checks:

```text
python -m unittest discover -s tests -p test_manual_docs.py -v
```

On Linux or macOS with Python 3.12–3.15 and venv support, run the full manual
workflow in fresh public checkouts:

```bash
python3 tests/verify_unix_walkthrough.py --shell bash
# On systems with zsh:
python3 tests/verify_unix_walkthrough.py --shell zsh
```

CI retains PowerShell syntax checks on Windows and native Bash/zsh execution
on Linux/macOS. The full manual check supplies an unreviewed annotation fixture
through APW's HTTP API, then verifies preview/import, citation resolution,
replay counts and viewer shutdown. Logs and receipts are saved under
`.workflow-test/manual/`. The installed `sci` and browser workflow tests remain
separate. These are engineering checks, not scientific answer validation.
