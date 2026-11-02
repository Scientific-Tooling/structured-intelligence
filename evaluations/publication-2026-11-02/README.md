# November 2 coordinated publication

The APW invalid-citation-page fix is published at
[`d800a7779f1893be1a4aa0a93804c7e630d6be1a`](https://github.com/Scientific-Tooling/agent-pdf-workbench/commit/d800a7779f1893be1a4aa0a93804c7e630d6be1a).
Sci's package dependency and browser CI checkout now pin that exact commit.
RKS remains at `44a8f33f47d9e867a03a8cff9e07a7b021e04cea`.

## Installation verification

A fresh environment at `.publication/2026-11-02/installed` installed the sci
checkout using `python -m pip install ./structured-intelligence`. Its APW and
RKS dependencies came from their ordinary public Git URLs; no editable install
or `--no-deps` substitution was used. The retained [install log](install.log)
and [installation identity](checks/installation.json) record package versions,
exact dependency commits, module locations and file hashes.

All installed application files were compared with frozen candidate c3. Exact
matches and CRLF/LF-only differences are recorded separately; no semantic
changes are accepted by the comparison. The corrected APW reader assets are
included. The installed sci metadata also names the new APW commit.

All **21 checks passed**: 19 installed workflow/recovery checks and two native
RKS/APW integration checks. The [check results](checks/results.json) and raw logs
retain their commands, timing and outcome. Application imports resolve
inside the fresh environment; `PYTHONPATH` is removed and both native test
interpreter variables point to that environment. See [summary.json](summary.json)
for their final counts and outcome.

## Relationship to acceptance evidence

The [engineering acceptance report](../engineering-acceptance-2026-11-02/README.md)
retains c2's failure, c3's correction, 41 passing browser checks, frontend
regressions and the 10,000-record benchmark. Those frozen receipts are unchanged,
including their original pre-publication metadata. This record qualifies the
coordinated installation separately rather than rewriting candidate evidence.

The APW remote `main` was verified after pushing, and its
[hosted CI run passed](https://github.com/Scientific-Tooling/agent-pdf-workbench/actions/runs/41475793974).
Sci's [hosted runs](https://github.com/Scientific-Tooling/structured-intelligence/actions)
remain separate from the local installation result. No release tag or scientific approval is implied.
Independent review and remaining release gates stay open.

`verify_installation.py` refuses to replace its checks directory. Retain this
record and choose a new publication/run directory for future verification.
