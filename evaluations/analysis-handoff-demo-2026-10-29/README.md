# Synthetic evidence-to-analysis handoff: October 29, 2026

This engineering demonstration connects the existing three-paper single-cell
methods pilot to the `scrnaseq-differential-expression` skill. It verifies retained
provenance, input identity, explicit draft status and interruption recovery.
**No statistical analysis ran, and no scientific plan review was recorded.**

The [machine-readable receipt](results.json) records actual identities and checks.
The [usage guide](../../docs/analysis-handoffs.md) describes the contract and remaining
milestone gates; the [generator](../../examples/analysis-handoff/make_demo.py) and
[request template](../../examples/analysis-handoff/request.example.json) support reuse
with another project's explicit evidence selections.

## Demonstration

| Item | Observed result |
| --- | --- |
| Input | 200 synthetic cells, 80 genes, eight samples; four per condition |
| Raw counts | Integer counts retained in `X` and `layers["counts"]`; H5AD round trip verified |
| Selected support | Six comparison cells and ten distinct evidence records from three papers |
| Native review state | All selected evidence and comparison entries remain unreviewed |
| Proposed method | Pseudobulk DESeq2 for one balanced synthetic contrast; no universal method ranking implied |
| Freshness check | Current identities, zero changes; sixteen support items still need review |
| Exact retry | Same canonical record, one handoff, no pending request |
| Existing project | Native snapshot and every existing brief file unchanged |
| Execution | Not run; proposed R environment and input adapter not verified |

The retained rationale acknowledges mixed-model alternatives and the different
conditions in the selected papers. Synthetic observations do not supply biological
evidence. The artificial changes in the generator are not a scientific benchmark.

The local handoff ID is `c1c711050d5e436fb84828589ecd1741`, under
`analyses/ID/` in the original `single-cell-de` pilot workspace. Its canonical
`record.json` contains the retained skill, environment specification and readable
`handoff.md`. Dataset bytes stay in the original local demonstration directory.
These absolute locations are required for live checks and are not published as a
portable project archive. The receipt provides hashes for auditing the original run.

## Validation

A wheel built from committed baseline
`5e8e50f3b2fdc31b6361fd0badbf29f6ad977897` plus this feature's files was installed
into a dedicated Windows Python 3.12 environment. This isolated concurrent
refactoring in the shared checkout. APW and RKS were installed at the exact public
revisions recorded in the receipt.

- **9/9 analysis tests passed:** packaged skill lookup, public CLI and exit status,
  immutable support, exact replay, interrupted artifact publication, stale request
  revisions, changing input bytes, selected review changes, reading edits, unrelated
  comparison edits, tampered records/artifacts and project identity.
- **13/13 baseline maintenance tests passed:** change checks, retained editions,
  scope, read-only backend access and publication recovery.
- The real pilot handoff was created, checked and replayed through the public CLI.
  Native state and all existing brief bytes were compared before and after.

The repository CI matrix includes the new handoff suite, but this local evaluation
does not establish a cross-platform CI result. Environment resolution, dataset
semantic validation, analysis execution, measured resources, output provenance,
scientific review and independent reproduction remain pending.
