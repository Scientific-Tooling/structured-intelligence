# sci roadmap

Updated October 29, 2026. Current baseline: **sci 0.3.1**.

Development publication: **sci `0.4.0.dev20261029`**, with the continuous APW
reader pinned at `4c3a379123847aff42e221013ae4c49a4149997d`. Candidate
`2026-10-29-c1` and the imported-evidence evaluation/review packet are complete
engineering checkpoints. Independent scientific review and remaining acceptance
gates are open. Continue from the [development handoff](phase-2-handoff.md) and
[imported-evidence results](../evaluations/imported-evidence-2026-10-29/results.md).

`sci` should help a researcher carry a question from papers to evidence, a
defensible comparison, and a reproducible next step. The CLI maintains durable
project state; an agent helps read and reason; the reader lets a person inspect
the original material. All three should work on the same project.

This is the product roadmap for `sci`, the `scientific-tooling` package maintained
in this repository. The [repository roadmap](roadmap.md) covers the broader
collection of skills and agents. See the [quick start](../workflows/research/quickstart.md)
for commands available today.

## Available today

Version 0.3.1 provides:

- One or more local PDFs under a shared research question, with `start`, `add`,
  `papers`, `open`, `status`, `resume`, and `stop`.
- Separate reading sessions, highlights, notes, and import previews for each
  paper, with shared durable evidence and browser navigation between papers.
- Explicit selection, preview and import; revision checks and safe replay;
  retained PDF snapshots and supporting-passage links.
- A project brief that groups imported evidence by paper and shows coverage,
  including papers without evidence. It does not infer scientific conclusions.
- A reader with project navigation, Evidence/Notes/Brief tabs, resizable sidebars,
  focus mode and mobile drawers. Notes can link to readable supporting highlights.
- JSON output and the bundled `paper-to-brief` agent skill, Windows/Linux/macOS
  workflows, and migration of existing single-paper workspaces.

The CLI does not call a model. An agent host supplies reasoning and any model
connection. Engineering tests verify workflow behavior; they do not establish
the scientific correctness of imported interpretations.

## Planned sequence

The baseline above is released. Repository `main` adds project evidence search
through the CLI, JSON interface and reader, with exact published dependency pins; see
[usage, contracts and acceptance gaps](evidence-search.md). Milestone 2 also has a
development implementation of comparison matrices and revision-bound human reviews;
see [usage, recovery and acceptance gaps](comparisons.md). The milestones below remain in
priority order, without promised dates, release numbers, or final command names.
Keep each milestone useful on its own and revisit the order after researcher pilots.

An [agent-operated three-paper pilot](../evaluations/living-project-pilot-2026-10-28/README.md)
verified change detection, retained editions and exact replay on October 28, 2026.
It also exposed four failed citation targets out of ten and loss of the open paper
after a quote-matching error. The [subsequent remediation](../evaluations/living-project-pilot-2026-10-28/README.md#remediation)
fixes both defects: all ten unchanged links now open with highlights, rejected
quotes retain the paper, and inspection avoids per-record process startup.
Independent researcher and scientific review remain pending; these engineering
checks do not complete milestones 1-4.

| Milestone | Status | Researcher outcome |
| --- | --- | --- |
| 1. Find evidence across a project | In progress: implemented on main; release and independent evaluation pending | Locate relevant saved evidence without reopening every paper. |
| 2. Compare and review findings | In progress: implemented on main; release and independent domain review pending | Compare methods or claims with traceable support and explicit gaps. |
| 3. Discover and add relevant papers | In progress: implemented on main; release and independent evaluation pending | Move from a question or identifier to a selected, attributed reading set. |
| 4. Maintain a living project | In progress: change reports, retained brief editions and explicit discovery repeats; recurrence and evaluation pending | Understand what changed when sources or interpretations change. |
| 5. Connect evidence to analysis | In progress: draft handoffs and synthetic input; execution, output linkage and independent review pending | Turn a literature decision into a bounded, reproducible analysis handoff. |

### 1. Find evidence across a project

Expose project-scoped retrieval through the CLI, JSON interface and reader.
Search imported quotations, notes and interpretations, with filters for paper
and review status. Show the matched text, its evidence identity, paper, page,
source revision and a supporting link when one is available. Clearly distinguish
source text from commentary and report unavailable anchors.

Use RKS retrieval and evidence contracts. Keep evidence search separate from any
future full-paper search, so a result does not imply that a passage was imported
or reviewed. Measure retrieval failures before choosing a different ranking method.

**Done when:** a researcher can find and reopen relevant evidence across several
papers; filters prevent results from leaking between projects; empty, ambiguous,
duplicate and stale-source cases have explicit outcomes. Evaluate retrieval with
frozen cases and independently reviewed references, alongside usability checks.

### 2. Compare and review findings

Let the researcher define comparison criteria, such as dataset, method assumptions,
evaluation metric, limitations and applicability. Build a comparison from selected
evidence, retaining links and review status for each populated cell. Mark missing
information explicitly. Different experimental conditions must remain visible.

An agent may propose a synthesis, supporting evidence or an apparent disagreement.
Keep those interpretations distinct from quotations. Record human review against
the exact evidence revisions and review scope; editing the underlying material
must make an older review visibly stale.

**Done when:** every factual comparison entry has inspectable support or an explicit
unsupported label; unsupported cells remain gaps; real review decisions survive
restart and are invalidated appropriately by edits. Independent domain review
checks numerical values, conditions, negation and claimed contradictions.

### 3. Discover and add relevant papers

The first development slice provides question-only projects, bounded PubMed and
Crossref searches, DOI/PMID lookup, saved candidates, explicit PDF selection,
work/version identities and interrupted-selection recovery. See
[commands, provenance, validation and remaining gates](discovery.md). Its reader
panel ships through the pinned APW reader dependency, including the research desk
layout and steady navigation between papers.

Bring bounded literature discovery and identifier-based import into the project
workflow, reusing existing discovery skills and RKS ingestion. Present candidates
with bibliographic metadata, discovery query, source and retrieval date. Add the
researcher's selected papers and retain the available original source.

Distinguish a bibliographic work from its PDF versions. Preserve provenance when
the same work arrives through several providers, and report missing full text
without substituting an abstract for a read PDF. Discovery does not imply selection,
evidence import or scientific review.

**Done when:** a recorded query or identifier produces a reproducible candidate
list and a selected reading set; duplicates, changed versions, unavailable sources
and interrupted imports retain clear identities and recovery paths.

### 4. Maintain a living project

The first development slice provides change checks, saved update reports, brief
editions with supporting snapshots, interrupted-publication recovery, reader
history and explicit repeats of saved discovery. See
[commands, freshness semantics and remaining gates](living-projects.md).

Track additions and changes to sources, evidence, reviews and generated briefs.
Show what changed since the last brief and which interpretations need attention.
Retain earlier outputs so a researcher can reconstruct what supported a decision
at the time. Recurring discovery should be an explicit opt-in workflow using the
same bounded operations, with updates presented for selection.

**Done when:** a project update identifies affected evidence and reviews, preserves
older source revisions, avoids duplicate imports, and can be interrupted and
resumed without presenting an obsolete brief as current.

### 5. Connect evidence to analysis

The first development slice retains draft handoffs from selected comparison cells
to the existing single-cell differential-expression skill. It fingerprints inputs,
preserves exact support and review labels, checks selected-support freshness and
recovers interrupted publication. A labeled synthetic dataset exercises this path;
no statistical analysis or scientific plan review is implied. See
[commands, demonstration and remaining gates](analysis-handoffs.md).

Hand a selected research decision to an existing analysis skill or workflow.
Record the rationale, dataset identity, assumptions, environment, parameters and
expected outputs. Start with one narrow single-cell RNA-seq methods use case
before extending to other domains. Link results back to the decision and source
evidence, with execution progress and resource requirements visible to the user.

**Done when:** an independent user can reproduce the bounded example from its
saved inputs and environment, inspect its outputs, and trace the chosen method
back to reviewed evidence. Scope and implementation depend on earlier pilots.

## Development feature completion plan

Prepared October 29, 2026, against the current checkout, feature documentation,
test coverage and retained pilot receipts. This is the execution plan for the
five development entries in the [concise guide](sci-overview.md). It does not
change their availability or claim that release gates have already passed.

**Objective:** deliver a versioned, installable release in which a researcher can
find imported evidence, compare it, select additional papers, maintain the project,
and prepare a durable draft analysis handoff using the documented interfaces.

The implementations already exist. Concentrate on measured defects, independent
evaluation, integration and release. Preserve the earlier pilot and benchmark
results; attach new receipts to the exact candidate that was checked.

### Scope of completion

For this delivery, **done** means the documented feature passes its acceptance
cases, an independent user completes its workflow, the installed release passes
the supported-platform checks, and its guide accurately describes the shipped
behavior and limits. A released tool may still produce explicitly unreviewed
drafts; software maturity and scientific approval are separate states.

The maintenance entry covers change checks, retained editions and explicit search
repeats. Automatic recurrence and verified export/restore remain separately tracked
roadmap work. The handoff entry covers saving and checking a draft with evidence,
dataset identity, parameters and environment text. Dataset semantic validation,
environment resolution, plan approval, execution and result provenance remain the
next analysis milestone. Do not advertise a draft handoff as execution-ready or
reproducible analysis. These bounded feature releases do not automatically close
the broader milestones above.

### Completion work by feature

| Feature and owner | Remaining work | Acceptance evidence required |
| --- | --- | --- |
| **Find relevant saved evidence** — RKS retrieval; sci/APW integration | The ten-paper imported-note fixture and native search baseline are implemented. Have its questions and relevance references independently reviewed, add new held-out questions, and complete browser/source-navigation and large-project latency checks. Fix observed ranking or navigation failures at their source. | CLI and reader return the same scoped evidence identities; paper/review filters and revision changes behave correctly; unchanged citations open the exact retained page and highlight. Empty queries, duplicate text and unavailable sources have explicit outcomes. Retain rankings, reviewed labels, source identities and timing receipts. |
| **Compare findings** — RKS history/reviews; sci/APW editing | Have a domain reviewer inspect the existing three-paper, six-cell comparison against all ten supporting passages. Correct numerical, condition, negation and applicability errors. Exercise real review recording, stale reviews, conflicting edits and restart/retry. | Every populated factual cell has inspectable support or an explicit unsupported state. Actual human review records retain reviewer, scope, decision and exact revisions. Changing one cell or its support stales the affected review; unrelated cells retain their reviews. Export and reopened history agree with the saved state. |
| **Discover papers** — sci providers/selection; APW interface | Broaden live PubMed/Crossref checks beyond the previous accessible DOI. Cover query translation, identifier lookup, ambiguous identities, no PDF, multiple PDFs and changed versions. Test provider timeout/rate-limit responses and interrupted acquisition with deterministic fixtures. Observe independent candidate selection. | Saved runs reopen from retained responses without a network request. Repeating a query records a new run rather than promising identical live results. Explicit selection retains provider attribution and PDF identity; duplicate selections and retries create no duplicate work/version. Unavailable or invalid full text remains explicit and is never substituted with an abstract. |
| **Maintain the project** — sci snapshots/history; RKS/APW source state | Integrate and review the pending freshness/state changes. Extend the installed browser journey through change detection, history, failed freshness checks and brief retry. Repeat the existing two-edition pilot with source, evidence and review changes. | Each known mutation identifies its affected evidence/comparison; a saved report does not make an old brief current. Earlier edition bytes and supporting snapshots stay intact. Interrupted publication resumes once, and an older retry cannot replace the latest edition. Search repeat preserves bounds and selects nothing automatically. |
| **Prepare an analysis handoff** — sci; domain reviewer for content inspection | Review and package the local draft feature, schema, skill resource and examples. Check a valid synthetic input alongside malformed/missing/changed-input cases. Have a second person create, inspect, reopen and check a handoff using only the guide. | The installed wheel retains the exact selected support, review labels, dataset hash, parameters, environment text and skill revision. Exact retry reproduces the same record; changed inputs/support are reported without rewriting history. Unrelated cell edits do not invalidate it. `not_run` and `not_recorded` remain explicit; a hash check never claims that H5AD/RDS contents or the proposed environment are valid. |

### Delivery order and checkpoints

Effort ranges below are planning estimates for one implementation owner, assuming
the existing implementations can be retained. They are not measured durations or
promised dates. Reviewer and pilot availability is additional calendar time.

1. **Establish the release candidate baseline — 1–2 engineering days.**
   Inventory the uncommitted sci feature, state/refactoring, documentation and APW
   reader changes; separate reviewable changes without discarding existing work.
   Record candidate revisions, dependency pins, schemas and expected migrations.
   Give the candidate a distinguishable version/build identity rather than labeling
   every development installation `0.3.1`. Reproduce the current installed journey
   and list failures by feature. Preserve a stopped-workspace backup for upgrade
   checks. No release or approval status changes at this checkpoint.

2. **Finish evidence retrieval and comparison acceptance — 3–5 engineering days,
   with independent review scheduled from the start.**
   Build the imported-evidence evaluation fixture, freeze the review protocol and
   thresholds, and rerun search and comparison checks against the baseline. Prepare
   the source-linked review packet for the existing real comparison. Resolve
   measured failures and retain both the initial and corrected results. This is
   the prerequisite for trusting the support captured by later handoffs.

3. **Finish discovery and maintenance acceptance — 3–5 engineering days.**
   Run provider acquisition cases and the complete discover/select/read/import/
   compare/change/history/repeat journey in disposable projects. Add missing browser
   coverage for maintenance, including failed checks and lost responses. Verify
   upgrade from an existing 0.3.1 workspace, without duplicate records or lost
   editions. Recheck all ten pilot citations against the new continuous reader.
   Check long-document scrolling, page-scoped annotations, search, zoom and paper
   switching because the renderer is now part of this candidate's dependency.

4. **Finish the draft handoff delivery — 2–3 engineering days.**
   Review the local analysis implementation and installed resource packaging;
   exercise the real synthetic input, handoff request, create/list/show/check and
   exact replay from the documented commands. A second person must locate the
   retained evidence and distinguish input freshness from scientific suitability.
   Report missing dataset adapters or unresolved runtime specifications explicitly;
   do not make analysis execution a hidden requirement of this draft feature.

5. **Validate and publish the coordinated release — 3–5 engineering days, plus
   completion of independent user sessions.**
   Build candidate distributions and run the installed suites on Windows, Linux
   and macOS with the supported Python matrix. Verify the dependency identities
   actually installed and use the same APW revision in package metadata and browser
   CI. Validate changed RKS/APW dependencies, publish their immutable commits, then
   update sci's pins and repeat the clean public-dependency installation. The local
   APW install used for development is not evidence that sci's current public pin
   contains the continuous reader. Run the pilot below, resolve blocking defects,
   then publish a versioned release with receipts and upgrade instructions.

Estimated engineering envelope: **12–20 working days**, subject to the baseline
audit and evaluation findings. Each checkpoint produces a concrete acceptance
report. Researcher sessions can be arranged while engineering proceeds; they are
not replaced by agent-operated demonstrations.

### Evaluation and release gates

Freeze these proposed targets before evaluating the candidate; record any later
change as a new protocol revision, with its reason and the original result retained.

- **Evidence retrieval:** independently review the existing 20 questions and
  relevance targets, then add at least ten new held-out questions authored by a
  reviewer who did not tune retrieval. The six publicly reserved questions remain
  useful regressions, not a blind test. Proposed target: at least 90% `hit_at_5`
  on answerable reviewed queries, with raw numerator/denominator and `recall_at_5`
  reported separately. Do not claim precision from incomplete labels or interpret
  a retrieval hit as a complete scientific answer. Existing RKS claim-search
  scores cannot substitute for evaluating the imported-evidence search endpoint.
- **Source and state integrity:** every unchanged citation in the acceptance set
  must open its correct retained page and highlight. Deliberately altered/missing
  sources must be rejected clearly while preserving readable work. Require zero
  foreign-project results, silent source substitutions, false review approvals,
  duplicate replay records, or corrupted historical outputs in the fault cases.
- **Performance:** record cold and warm timings on named hardware and fixed
  projects, including 10,000 imported evidence records. Proposed target: warm
  evidence search p95 at or below two seconds over 100 recorded queries. Measure
  cold startup and project-change checks separately. Verify bounded raster/cache
  use while scrolling a 30-page PDF in the installed browser; report measurements
  rather than inferring browser memory behavior from unit tests.
- **Independent use:** recruit three researchers, including at least one relevant
  domain reviewer, to follow the guide through discovery, evidence search,
  comparison/review, a changed brief and a draft handoff. Each should complete the
  scripted journey without developer repair. Record completion, time, assistance
  and corrections; close blocking failures and rerun the affected task. This
  small pilot establishes initial usability evidence, not broad scientific validity.
- **Release reproducibility:** retain commands, build/dependency identities, OS/
  Python versions, test reports and representative screenshots from clean installs.
  Require the supported installed-package matrix and browser journeys to pass;
  check upgrade, restart and interrupted-operation recovery. Demonstrate backup
  restoration at the supported original path before documenting rollback; workspace
  relocation remains unsupported until its separate portability gate passes.

Only actual human statements may populate review records. An agent may prepare
the review packet and test fixtures; it must not invent independent judgments or
mark their acceptance gate passed. The human inputs needed are a domain reviewer
for reference/comparison checks and participants for the independent workflow trial.
Engineering preparation can proceed before they are available.

### Release artifacts and immediate next action

Retain a candidate manifest, feature acceptance matrix, frozen evaluation protocol,
review records, pilot receipts, installation/upgrade report and updated screenshots.
Give every unresolved issue an owner role and a blocking/nonblocking disposition.
Publish the scoped behavior and known limits in the concise guide, detailed guide,
quick start and release notes. Change an availability label to **Released** only
after that feature's gates pass and its version is published. Keep analysis outputs
labeled **Draft handoff** even when the handoff-saving feature is released.

**Checkpoint 1 is complete:** the candidate and its concrete acceptance/failure
matrix are frozen. The imported-evidence fixture and source-linked review packet
from checkpoint 2 are implemented; actual independent review remains pending.
Continue with missing browser recovery cases and the ten real pilot citation
checks, using the [current handoff](phase-2-handoff.md). The original instruction
for checkpoint 1 was to reconcile the local changes, freeze one candidate and
produce its failure/acceptance matrix. Then execute checkpoints 2–4 against that
same candidate lineage, followed by the coordinated release gate. The existing
feature code is the starting point; new scope requires a demonstrated gap in the
researcher workflow.

## Foundations carried through every milestone

- **Clear ownership:** Structured Intelligence coordinates projects; RKS owns
  durable evidence and review provenance; APW owns source reading and annotations.
  Reuse their public contracts and native transactions.
- **One workflow for people and agents:** browser actions and agent commands use
  the same identities, previews and saved state. Automation must respect the
  user's authorized selections and scope. Model-generated work stays labeled.
- **Recoverable, portable work:** preserve existing workspaces, revision identity
  and replay behavior. Add verified export/restore and workspace relocation before
  promising portable sharing; current workspaces still require their original
  absolute location. Track portability as a separate acceptance gate.
- **Measured usefulness:** test installation, recovery and source-link integrity
  on Windows, Linux and macOS. Also measure time to useful evidence, correction
  burden and successful task completion in researcher pilots. Tests alone cannot
  establish scientific answer quality.

The [scientific evaluation workflow](../workflows/research/scientific-evaluation.md)
and [single-cell RNA-seq candidate corpus](../evaluations/scrna-methods-v1/README.md)
provide a starting point. Their draft labels still need independent review;
public reserved questions are not a blind test. Keep retrieval performance,
source fidelity and scientific answer accuracy as separate measurements.

## Boundaries and maintenance

A general autonomous scientist, a new model-hosting platform, and real-time cloud
collaboration are outside this roadmap's committed scope. Keep the first useful
path short and expand it only when a demonstrated research task benefits.

At each milestone, update this file with what actually shipped, links to usage
documentation, validation evidence and remaining limitations. Select the next
slice from observed researcher needs and measured failures; preserve earlier
evaluation results rather than moving targets to make a release look better.
