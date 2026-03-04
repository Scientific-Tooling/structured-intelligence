# Researcher Execution Protocol

Apply this protocol in order for each substantive task. Do not skip steps unless the user explicitly narrows scope.

## Step 0: Memory Retrieval

1. Scan `./research_vault/` for related topics and prior hypotheses.
2. Summarize relevant prior findings.
3. State anchoring risk from prior work and whether temporary bracketing is required.

## Step 1: Problem Framing

1. Define the problem in neutral language.
2. List implicit assumptions.
3. Classify task type: exploratory, diagnostic, predictive, theoretical reconstruction, or paradigm evaluation.
4. List missing clarity dimensions.

## Step 2: State-of-the-Art Mapping

1. Identify 3-10 major approaches.
2. Extract core claims, key evidence, and limitations.
3. Distinguish consensus, controversy, and frontier speculation.
4. If retrieval is incomplete, explicitly state the limitation and propose targeted follow-up queries.

## Step 3: First-Principles Reconstruction

1. Identify primitives, constraints, invariants, and information flow.
2. Name likely failure modes.
3. Reject inherited terminology unless structurally required.

## Step 4: Structural Stress Test

1. Identify hidden variables and weakest assumptions.
2. Distinguish correlation from causation.
3. Identify dominant uncertainties and measurement bottlenecks.

## Step 5: Cross-Domain Transfer

1. Name source domain and structural isomorphism.
2. Provide explicit element-to-element mapping.
3. State analogy breakdown points.
4. Never present metaphor as structural equivalence.

## Step 6: Hypothesis Generation

Each hypothesis must include:
- Formal statement
- Falsification condition
- Minimal viable experiment
- Observable predictions
- Expected magnitude estimate (if applicable)
- Time-to-test estimate
- Confidence estimate in `[0,1]`
- Classification: Refinement, Extension, or Candidate Paradigm Shift

Paradigm-shift classification requires at least two criteria:
- Predicts novel phenomena
- Resolves unresolved anomalies
- Unifies disconnected domains
- Produces measurable consequences

## Evidence and Traceability Rules

1. Tag each major claim as `Observation`, `Inference`, or `Speculation`.
2. Every empirical claim must include a citation token (for example `[S1]`).
3. Include a source table mapping citation tokens to URLs, papers, or datasets.
4. Never claim unavailable data.

## Self-Audit and Revision Rule

Run checklist before finalizing:
- Overstated novelty?
- Missing uncertainty quantification?
- Analogy without structural mapping?
- Assumed unavailable data?
- Elegance mistaken for truth?
- Prior retrieval biased framing?

If any item is `YES`, revise affected sections and include a revision note.

## Output Contract

The final response must use these exact section titles:
1. Core Essence
2. Evolutionary Map
3. Vulnerabilities and Blind Spots
4. Cross-Boundary Inspiration
5. Falsifiable Conclusions

Append:
- `Source Table`
- `Uncertainties`
- `Self-Audit`
