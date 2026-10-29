# Connect evidence to analysis (development)

The first slice of milestone 5 retains a **draft analysis handoff** from selected
comparison cells to the existing `scrnaseq-differential-expression` skill. It saves
the rationale, exact supporting evidence and review states, dataset identity,
environment specification, explicit parameters, assumptions, resources and expected
outputs. This is a development feature; it is not in the tagged sci 0.3.1 release.

The handoff does not run an analysis or approve its design. RKS remains the owner
of evidence and comparison review; APW owns the source reading records. Existing
review labels are preserved, including unreviewed interpretations. The saved
skill is prose for an agent to follow, not an executable or validated analysis runner.

## Create a handoff

Use an installed development build (`python -m pip install .` from a checkout).
Inspect the project's comparison before selecting its support:

```text
sci compare list --workspace review --json
sci compare show COMPARISON_ID --workspace review --json
```

Copy [the request template](../examples/analysis-handoff/request.example.json) to
your dataset directory. Replace the comparison ID, current comparison revision
and selected cell keys with the exact values from `compare show`. Choose populated
cells with linked evidence, retain relevant conditions and disagreements, and
write the rationale for this specific dataset. The schema requires explicit
parameters rather than inferring scientific choices from the literature.

Provide a readable dataset and a UTF-8 environment specification. Relative paths
resolve against the request file's directory. This first handoff accepts declared
H5AD or Seurat RDS inputs and the skill's pseudobulk DESeq2 or edgeR methods; it
does not inspect those file formats or infer metadata column names.

```text
sci analysis create request.json --workspace review --json
sci analysis list --workspace review
sci analysis show HANDOFF_ID --workspace review
sci analysis check HANDOFF_ID --workspace review --json
```

Creation saves the request ID before capturing inputs. Keep the returned ID to
retry an interrupted request with `--request-id HANDOFF_ID`. A different proposal
requires a new ID. Every handoff starts with `execution_status: "not_run"` and
`plan_review: "not_recorded"`; a caller cannot supply an approval field.

The readable `analyses/HANDOFF_ID/handoff.md` contains the selected interpretations,
conditions, quotes and source links alongside the proposed analysis. Its canonical
`record.json` retains those records and the exact `SKILL.md`, environment text and
Markdown. The dataset stays at its original location, identified by absolute path,
SHA-256 and byte size. Keep it and the original project available. This is not yet
a portable archive, environment lock or execution receipt.

## Check identities and recover interrupted work

`check` reads the input files and the current selected support. It detects changed
or missing datasets, environment files, retained artifacts, selected comparison
entries, evidence, reading material and review records. An unrelated comparison
cell edit does not invalidate this handoff. Reader address changes alone do not
invalidate the retained support; reopening links still requires a running reader
at the recorded address.

- **Current** means the observed identities still match. It does not establish
  statistical validity, dataset suitability or scientific review. Review gaps
  remain in `attention`.
- **Outdated** means a change or unavailable input needs inspection. `check`
  returns exit code 2; successful identity checks return 0.
- `list`, `show` and exact replay do not imply a live check. Creation and listing
  report freshness as **unchecked** until `check` runs.

The canonical record is committed before publishing the convenient files. An
exact retry returns that same record and restores missing derived artifacts,
even if the original inputs have since changed. It refuses to overwrite edited
artifacts. Inspect changes and create a new handoff instead of editing history.
A failed capture remains in `pending_requests` until the same request can succeed;
it is never presented as a completed handoff.

No command here imports evidence, records a human review, launches a job, installs
the proposed environment or rewrites an existing brief. The project and dataset
must remain at their original absolute paths. Checks describe observations at the
reported time, not a lock on files for a future execution.

## Generate the demonstration dataset

From the repository root, install the generator dependencies in a separate Python
3.12 environment, then choose a new output directory:

```text
python -m pip install -r examples/analysis-handoff/demo-requirements.txt
python examples/analysis-handoff/make_demo.py demo-analysis
```

The generator creates `synthetic-counts.h5ad`, `cells.tsv` and `generation.json`:
200 cells, 80 genes, eight synthetic samples, four samples per condition and one
cell type. Integer raw counts are stored in `X` and `layers["counts"]`. A fixed
seed controls generation; the receipt records the generator, data hashes and
package versions. The file is read back and its counts and sample labels checked.
An existing output directory is never overwritten.

These are synthetic engineering data. The artificial changes in the first eight
genes exercise the workflow; they are not scientific reference labels or a method
benchmark. Pins cover the generator's main libraries, not its full transitive
environment. Regeneration in another environment may produce a different HDF5
file identity, so retain the actual file used by a handoff.

Copy the request template into `demo-analysis/request.json`. As an initial proposed
analysis environment, copy
[`scrnaseq-r.yaml`](../skills/bioinformatics-env-setup/assets/envs/scrnaseq-r.yaml)
to `demo-analysis/analysis-environment.yml`. This existing R specification has
not been resolved or executed for the demonstration, and an H5AD input adapter
still needs verification. Replace the template's support IDs and rationale, then
run `sci analysis create` against your existing evidence project.

The demonstration uses synthetic counts with support from the existing
[three-paper pilot](../evaluations/living-project-pilot-2026-10-28/README.md).
Its literature interpretations remain agent-origin and unreviewed. A sample-level
method proposal does not settle the papers' differing comparisons or establish a
universal method ranking.

The [October 29 demonstration receipt](../evaluations/analysis-handoff-demo-2026-10-29/README.md)
records the actual data identity, selected support, exact replay and preservation
checks. Local output paths in that report require the original pilot workspace.

## Validation and next slice

`tests/test_analysis.py` exercises installed-package resources, exact replay,
interrupted publication, changed inputs, stale comparison revisions, selected
review changes, reading edits, foreign workspaces, tampered records and the CLI
contract. Its dataset fixture is deliberately not a valid H5AD file: the check
must never claim semantic validation from a file hash. CI runs the suite against
the installed wheel and pinned RKS/APW dependencies on Windows, Linux and macOS.

The next slice needs a checked dataset adapter, a verified runtime, recorded plan
review, explicit execution and output provenance linked to the handoff. Independent
scientific review and reproduction remain milestone acceptance gates. This draft
handoff does not complete milestone 5.
