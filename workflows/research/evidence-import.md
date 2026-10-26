# Import selected reading evidence into RKS

This is the second implemented slice of the literature workflow. Start with the
saved JSON from [source reading](source-reading.md). APW owns annotations; RKS
stores explicitly imported paper notes and their provenance; this adapter only
orchestrates their public CLIs.

Use compatible checkouts containing APW `export-evidence` and RKS
`note import-evidence`. Set `RKS_DATA_DIR` to the handoff's RKS directory and run
`rks migrate` once for an older database (migration 0014). Preview and apply do not
perform hidden migrations. Keep the PDF cache with APW backups.

## Prepare inspectable artifacts

Select the APW annotation and/or note IDs you intend to import. Use a stable
`--source-id` unique to this APW database and retain it through moves and restores.
The handoff's workspace ID continues to name the RKS workspace.

```bash
python scripts/research_evidence.py reading-handoff.json --source-id reader-a --annotation-id ann_example --note-id note_example --bundle evidence.json --plan import-plan.json
```

Repeat selection flags as needed. Both output paths must be new and distinct.
Pass `--rks-python` and `--apw-python` for separate installed environments, as in
the reading adapter. The adapter verifies the cached PDF, obtains a selected APW
export, verifies that it matches the handoff, and saves RKS's read-only preview.
It never applies evidence. A conflict report is saved and returned with exit 2.

If preview fails (for example because a migration is required), the successful
export remains available. Repair the reported problem and invoke RKS's preview
directly on that saved bundle. Do not overwrite an artifact already under review.

Read the bundle and plan together. The plan identifies additions, unchanged
items, and conflicts. Items remain explicitly unreviewed unless an actual human
review is supplied with `--reviews reviews.json`. APW's `docs/evidence-export.md`
documents this manifest: reviewer, time, statement, and exact content revision.
Never fill in reviewer names or dates for a review that did not occur.

## Apply the selected batch

With `RKS_DATA_DIR` set to the intended RKS workspace:

```bash
rks note import-evidence evidence.json --workspace-id review-a --apply --plan import-plan.json
rks note evidence p_000001
```

The workspace ID must match the handoff. RKS binds it on the first successful
import and rejects later mismatches. A complete batch commits atomically. Repeating
the command after a lost response produces unchanged records, without duplicate
notes. Imports preserve structured provenance and immutable revision history;
they never promote interpretations into graph claims.

For an edited item, RKS reports `revision_changed`. Compare the previous record
from `note evidence` with the new export. To accept the change explicitly, apply
the exact new plan with `--accept-updates`. If another importer changed the stored
revision after the preview, RKS reports `plan_stale` and requires a fresh preview.
One unresolved conflict blocks the whole batch. Local RKS edits are not overwritten.

Absence from a selected export never means deletion. Deleted APW annotations do
not delete imported RKS evidence. A selected or linked object missing from APW
fails a new export; the older exported artifact remains a historical snapshot.
Source changes create distinct identities, and new/edited evidence must match
the current RKS PDF. Exact historical replay remains possible with a verified
retained snapshot. Paper merges after migration 0014 retain redirects and original
import identities. RKS's `docs/evidence-import.md` is the detailed contract.

## Verification and remaining scope

Standard-library adapter tests run with:

```bash
python -m unittest discover -s tests -p 'test_research_*.py' -v
```

Set `RKS_TEST_PYTHON` and `APW_TEST_PYTHON` to installed interpreter paths, then use
`python -m unittest discover -s tests -v` for real cross-repository CLI integration.
The fixture is a generated one-page PDF with synthetic annotations and review
metadata. It checks source identity, export/preview/apply, replay, explicit review
updates, and retention after APW deletion. RKS additionally tests concurrent imports,
rollback, forced process termination, merge redirects, and snapshot restore.

These are engineering tests. They establish neither a scientific review nor a
researcher pilot. Page/annotation navigation, a source-linked research brief,
browser validation, and the small redistributable corpus demonstration are the next
Phase 2 slice. Hosted integration CI requires published compatible revisions;
current adapter CI covers both adapters on Windows and Linux.
