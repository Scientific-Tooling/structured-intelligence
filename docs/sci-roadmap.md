# sci roadmap

Updated October 28, 2026. Current baseline: **sci 0.3.1**.

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

| Milestone | Status | Researcher outcome |
| --- | --- | --- |
| 1. Find evidence across a project | In progress: implemented on main; release and independent evaluation pending | Locate relevant saved evidence without reopening every paper. |
| 2. Compare and review findings | In progress: implemented on main; release and independent domain review pending | Compare methods or claims with traceable support and explicit gaps. |
| 3. Discover and add relevant papers | In progress: implemented on main; release and independent evaluation pending | Move from a question or identifier to a selected, attributed reading set. |
| 4. Maintain a living project | In progress: change reports, retained brief editions and explicit discovery repeats; recurrence and evaluation pending | Understand what changed when sources or interpretations change. |
| 5. Connect evidence to analysis | Exploratory | Turn a literature decision into a bounded, reproducible analysis handoff. |

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

Hand a selected research decision to an existing analysis skill or workflow.
Record the rationale, dataset identity, assumptions, environment, parameters and
expected outputs. Start with one narrow single-cell RNA-seq methods use case
before extending to other domains. Link results back to the decision and source
evidence, with execution progress and resource requirements visible to the user.

**Done when:** an independent user can reproduce the bounded example from its
saved inputs and environment, inspect its outputs, and trace the chosen method
back to reviewed evidence. Scope and implementation depend on earlier pilots.

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
