# October 29 development publication verification

The sci `0.4.0.dev20261029` development build installs successfully with its
published dependencies, and **128 local Python checks pass** on Windows with
Python 3.14.10. APW's continuous reader is published at
[`4c3a379123847aff42e221013ae4c49a4149997d`](https://github.com/Scientific-Tooling/agent-pdf-workbench/commit/4c3a379123847aff42e221013ae4c49a4149997d).
Both sci's package dependency and browser CI checkout use that exact revision.
RKS remains pinned to `44a8f33f47d9e867a03a8cff9e07a7b021e04cea`.

## Installation and checks

A new environment at `.publication/2026-10-29/installed` was created from the
retained Python 3.14 interpreter. From the umbrella workspace,
`python -m pip install ./structured-intelligence` built sci and resolved its
ordinary public Git dependencies; no editable install or `--no-deps` was used.
[Installation output](install.log) and [module/distribution identities](checks/installation.json)
retain exact versions, paths and `direct_url.json` provenance. APW and RKS commit
IDs were asserted before tests. Installed modules were verified inside this new
environment. The application source and APW frontend files had also been checked
against the tested c1 snapshot before publication; the coordinated dependency pin
is the new package-metadata change.

| Check | Passed |
| --- | --- |
| Installed workflow and recovery | 19 |
| Discovery and selection | 12 |
| Atomic state | 4 |
| Maintenance and history | 21 |
| Draft analysis handoffs | 9 |
| Research adapters and evaluation tooling | 61 |
| Native RKS/APW boundaries | 2 |
| Total | 128 |

[Command results](checks/results.json) retain individual commands, elapsed times,
exit codes and log hashes. Each group ran in a separate process from the sci
checkout using the new interpreter; `PYTHONPATH` was removed, and native boundary
tests received that interpreter through `RKS_TEST_PYTHON` and `APW_TEST_PYTHON`.
The adapter suite intentionally includes tests of checkout helper scripts. The
retained [summary](summary.json) records the counts and exact dependency revisions.
The [artifact index](receipts.json) hashes this publication record.

APW's [hosted CI run](https://github.com/Scientific-Tooling/agent-pdf-workbench/actions/runs/40931374863)
passed for the published commit. Sci's hosted CI and broader platform/acceptance
checks are separate from the local result above.

## Candidate and review status

The [frozen c1 baseline](../development-candidate-2026-10-29/README.md) remains
unchanged, including its older public dependency metadata. This record verifies
the coordinated publication separately; it does not rewrite c1 or create a new
release candidate. Its earlier 111-test result and the subsequent 61-test adapter
results remain dated evidence rather than being replaced by this 128-test run.

The [imported-evidence evaluation](../imported-evidence-2026-10-29/results.md)
retains original and corrected source runs plus the final source-linked review
packet. All 26 independent review decisions remain pending. This publication
does not create a release tag, qualify scientific accuracy or close the remaining
browser, citation, performance, platform and researcher-pilot gates.

Continue from the [tracked handoff](../../docs/phase-2-handoff.md). Evaluation
directories preserve their original bytes through Git attributes, including
Windows line endings and source whitespace, so their receipts remain verifiable
on a fresh checkout.
