# Maintain a living project (development)

Milestone 4 adds project change checks, retained brief editions, interrupted-brief
recovery and explicit repeats of saved discovery. It is a development feature,
not part of the tagged sci 0.3.1 release. RKS continues to own evidence and review
decisions; APW owns reading records. sci retains the inputs and outputs of each
project brief without changing their scientific review status.

The package pins APW reader commit `2806a6c182a0ae442b39e68015a9bf76d31a3af5`
for the matching history UI. Stop the old reader before upgrading, then resume the
same workspace with the new installation.

## Check what changed

```text
sci changes --workspace review
sci changes --workspace review --json
sci update --workspace review --json
```

`changes` compares current records with the latest retained brief. It does not
start the reader, query providers, initialize a database, import evidence or
record a review. `update` performs the same inspection and saves a report under
`updates/`. JSON includes exact before/after records for papers, selected works,
imported evidence and comparisons, plus affected interpretations and review states.
Changes count from the last brief, not the last check: saving a report never makes
an obsolete brief current.

Checks include retained PDF byte identities, RKS source identity, changed or
missing imported notes, edited/deleted APW material, supporting passages,
comparison versions and review decisions. Editing an imported highlight without
reimporting it is visible as changed reading material. The old import and its
recorded review remain intact. Affected comparison entries identify their paper
and criterion; comparisons that exclude later papers report that coverage gap.

Freshness is separate from scientific quality:

- **Current:** captured inputs match the last edition at the reported check time.
  The brief can still contain unreviewed material, gaps or warnings.
- **Outdated:** project inputs changed. Inspect them before creating a new edition.
- **Unverified:** no edition has a captured baseline. Earlier Markdown files remain
  in `briefs/`; their original provenance cannot be invented.
- Routine `status` shows saved briefs as **unchecked**. Open Brief or run `changes`
  for a fresh check. A failed check cannot establish freshness.

The reader checks when you open **Brief**, keeping expensive source inspection out
of paper-switching. **Check changes** refreshes it; **Save change report** retains
the result. **Earlier brief editions** opens an exact saved output for inspection
or download. No model generates or approves conclusions during these operations.

## Retain a decision's supporting material

```text
sci brief --workspace review --json
sci history --workspace review
sci history EDITION_ID --workspace review --json
```

Each edition retains original quotes, imported interpretations and review records,
source identities and availability checks, comparison entries, their conditions
and review histories, and the exact rendered Markdown. Current reading material
is recorded separately from imported evidence. Comparison text keeps its human
or agent origin.

The canonical `briefs/EDITION_ID/record.json` publishes the complete text and
provenance together as one atomic record with a SHA-256 revision. `brief.md` is a
convenient copy. Earlier editions are never overwritten; retrying an older edition
cannot make it the latest. PDFs keep their existing hash-based paths; selecting
a changed PDF creates a separate version through discovery. Old links can become
unavailable, but the edition retains original supporting text and identities.
Digests detect accidental changes; they are not signatures or authentication.

Two matching observations are required for a change check. Brief generation also
rechecks its inputs before publication. Concurrent changes cause an explicit error
and no new committed edition. These are bounded observations across public tool
contracts, not a global transaction across databases and files. Freshness is tied
to a check time, not a promise about future edits.

## Recover an interrupted brief

Creation saves its request before collecting inputs. The error and `history` list
the request ID when work was interrupted:

```text
sci brief --request-id REQUEST_ID --workspace review --json
```

If publication completed but its response or workspace-pointer update was lost,
retry returns the exact committed edition. Otherwise it completes the same pending
request from freshly inspected inputs. The reader offers **Resume this brief**.
Imports retain their preview/receipt protocol; retrying an import duplicates neither
evidence nor its automatically generated edition. Changed source/evidence conflicts
require inspection and an explicit new selection or preview. Checks never repair,
overwrite or silently substitute source material.

## Repeat a saved discovery explicitly

```text
sci discover repeat DISCOVERY_ID --workspace review --json
```

The reader offers **Repeat this saved discovery**. It uses the same provider, exact
query or identifier, and result limit. The new run links to the previous run and
revision, preserves its own raw responses, and reports new candidates, metadata
changes and candidates not returned this time using exact provider identities.
Absence from a bounded result list does not establish removal, retraction or
irrelevance. No PDF is selected and no evidence is imported by a repeat. Failed or
interrupted attempts remain inspectable; repeating again creates a separate run.

There is no automatic scheduling in this slice. Recurring runs require a future
explicit opt-in scheduler; a normal project update makes no external searches.

## Validation and remaining gates

Engineering fixtures cover changed evidence, unimported reading edits, changed
reviews and stale support, added source versions, duplicate additions, legacy
outputs, tampered history, concurrent changes, interrupted publication, request
replay, reader scope and bounded repeat discovery. Reader tests cover stale
responses after paper switching and failures to verify freshness. Fixtures are
not scientific judgments.

Independent researcher evaluation, release validation, automatic recurrence and
export/restore remain separate gates. Workspaces still require their original
absolute location. Back up the complete workspace and its databases; a history
record does not replace retained PDFs or RKS.
