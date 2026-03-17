# Protein Heat Stability Prediction Playbook

## 1) Core Principle

Treat thermal stability prediction as evidence integration, not single-model truth.
Use at least two independent predictors whenever possible, and escalate top candidates
to experimental validation before downstream decisions.

## 2) When to Use Which Path

| Situation | Recommended Path |
|---|---|
| Sequence only, no structure | Path A: sequence-based features + language model scoring |
| Structure available or modelable | Path B: structure-based ΔG/Tm tools |
| Ranking WT vs. specific variants | Path C: variant ΔΔG/ΔTm prediction |
| Initial screen across many sequences | Path A (fast), then Path B for shortlist |

## 3) Tool Classes

### Sequence-Based Predictors

Use as a first-pass triage layer or when no structure exists.

**Composition feature heuristics (sequence only, no external tool required):**
- GRAVY index (Kyte-Doolittle): net hydrophobicity; context-dependent for thermostability
- Instability index (Guruprasad et al.): < 40 = likely stable in vitro
- Charged residue ratio (RKED/all): > 0.22 enriched in thermophiles
- Arg/(Arg+Lys): > 0.6 typical in thermophiles; Arg forms stronger salt bridges than Lys
- Aromatic content (WYF): > 0.075 common in thermophiles (aromatic stacking)

**Protein language models:**
- ESM-1v: log-likelihood scoring for variants; higher = more consistent with evolution
- ESM-2 masked marginal: per-residue variant effect from evolutionary context
- ProtTrans/ProtBERT: alternative sequence-level stability proxies

**OGT-based approaches:**
- Identify the organism of origin; look up OGT (optimal growth temperature) from NCBI Taxonomy or databases like BacDive
- OGT > 60°C strongly suggests thermophilic fold
- BLAST against characterised thermophile protein families for OGT evidence

### Structure-Based ΔG/Tm Predictors

Use when a crystal structure or high-confidence model (AlphaFold pLDDT > 70 for the region of interest) is available.

**Free energy / DDG tools:**
- FoldX `Stability`: estimates ΔG of folding; lower (more negative) = more stable; fast, practical for large sets
- Rosetta `cartesian_ddg`: slower, often orthogonal; useful for cross-validation
- DynaMut2 / DUET: web-accessible DDG estimators; good for spot-checks
- mCSM-Stability: graph-based DDG; can be used as second axis

Practical guidance:
- Always repair the structure with `FoldX RepairPDB` before any FoldX run
- Fix chain selection, protonation state, and biological assembly consistently across WT and mutants
- Run WT in triplicate as a control; use SD to gauge run noise
- Do not compare absolute ΔG values across different proteins; use relative ΔΔG between variants

**Tm-scale predictors (preferred for thermostability objective):**
- HoTMuSiC: structure-based ΔTm predictor; directly models melting temperature change
- MAESTRO: energy-based predictor with Tm change output; handles single and multi-site
- ThermoNet: CNN-based ΔΔG/ΔTm; trained on experimentally determined stability data

Practical guidance:
- Prefer at least one Tm-oriented signal alongside ΔG scores when the objective is thermostability
- Do not use Tm predictors as substitutes for ΔG tools; use them as a second axis in consensus ranking
- Calibrate interpretation thresholds on known variants in the same protein family if possible

### Machine Learning Models for Tm Prediction

When predicting absolute Tm (not just ΔΔG):
- ProThermDB: curated experimental Tm database; search for homologs to anchor predictions
- Tm-Vec: learned Tm predictor from sequence embeddings (Stark et al. 2023)
- Protein Thermal Stability from sequence (various neural approaches): treat as triage only

## 4) AlphaFold and ColabFold Usage

Use AF/ColabFold outputs as input to structure-based tools, not as direct stability indicators.

Recommended process:
1. Generate WT and mutant models under identical pipeline settings.
2. Compare local pLDDT around the region of interest (not just global score).
3. Inspect changes in packing, hydrogen-bond patterns, and steric clashes.
4. Feed validated structural models into DDG/Tm tools.

Do NOT do this:
- Rank variants by pLDDT alone.
- Interpret pLDDT differences as quantitative ΔΔG.
- Use AF models without checking for local structural plausibility (clashes, chain breaks).

## 5) Consensus Strategy for Variant Ranking

When comparing multiple variants:
1. Collect all tool outputs in a unified table (`tool_scores.csv`).
2. Standardise each metric with correct directionality (lower = stabilising for FoldX ΔΔG; higher = more stabilising for ΔTm in HoTMuSiC/MAESTRO).
3. Normalise each column (rank normalisation preferred for mixed-scale tools).
4. Average normalized scores with explicit weights.
5. Compute support count (number of tools agreeing on stabilising direction) and support fraction.
6. Escalate variants with high consensus support for experimental validation.

Suggested default weights (adjust per protein family):
- FoldX ΔΔG: 0.30
- Rosetta cartesian_ddg: 0.25
- HoTMuSiC / MAESTRO ΔTm: 0.25
- Sequence-based (ESM-1v, GEMME): 0.20

## 6) Interpretation Bands

### Thermostability Class vs. Tm
| Class | Typical Tm | Typical OGT of source organism |
|---|---|---|
| Hyperthermophilic | > 80°C | > 80°C |
| Thermophilic | 60–80°C | 50–80°C |
| Mesophilic | 40–60°C | 20–50°C |
| Thermolabile/Psychrophilic | < 40°C | < 20°C |

### Sequence Feature Thresholds (Calibration Heuristics)
| Feature | Thermophile-associated | Mesophile-associated |
|---|---|---|
| Charged ratio (RKED/all) | > 0.22 | < 0.16 |
| Aromatic content (WYF) | > 0.075 | < 0.055 |
| Arg/(Arg+Lys) | > 0.60 | < 0.40 |
| Instability index | < 30 | > 40 |

### ΔΔG Effect Sizes (Typical, Tool-Dependent)
| Magnitude | Interpretation |
|---|---|
| |ΔΔG| > 1.0 kcal/mol | Strong stabilising/destabilising candidate |
| |ΔΔG| 0.3–1.0 kcal/mol | Moderate effect |
| |ΔΔG| < 0.3 kcal/mol | Near-neutral / uncertain |

Always verify sign convention for each tool before combining values.
Always adapt thresholds to the specific protein family and assay conditions.

## 7) Experimental Validation Methods

When predictions identify top candidates, validate experimentally:

| Method | What it measures | Typical throughput |
|---|---|---|
| DSF (differential scanning fluorimetry) | Tm via SYPRO Orange dye fluorescence | High (96-well) |
| Nano-DSF | Tm via intrinsic fluorescence (Trp/Tyr) | Medium |
| DSC (differential scanning calorimetry) | Tm and ΔH of unfolding; thermodynamic ground truth | Low |
| Thermal shift assay | Tm via thermal ramping with dye | High |
| CD spectroscopy thermal melt | Secondary structure loss vs. temperature | Medium |
| T50 / residual activity assay | Functional heat tolerance; more relevant for enzymes | Medium |

Prioritise DSF for high-throughput triage; confirm with DSC for mechanistic characterisation.

## 8) Failure Modes and Checks

Common failure modes:
- Wrong chain or biological assembly selected in structure input
- Residue numbering mismatch between FASTA and structure (use `structure_residue_mapper.py` from design-thermostable-mutations skill)
- Missing cofactors/ions/ligands that alter local geometry and stability
- Structure with missing loops repaired incorrectly
- Composition features calibrated on mesophilic proteins applied to membrane or disordered proteins

Checks to enforce:
- Validate mutation mapping before any scoring run
- Re-score top hits with an orthogonal method
- Cross-check predicted class against organism OGT if known
- Downgrade confidence when predictions are based on sequence features alone for a multi-domain protein

## 9) Benchmark Signals and Caveats (2024–2025)

- Large-scale DDG predictor benchmarks report systematic destabilising-class bias and weak recall for stabilising variants; treat stabilising predictions as high-uncertainty until orthogonally validated.
- AF3 benchmarks show strong local structural improvements in some settings but limited predictive gain for ΔΔG over AF2 in others; do not assume AF3 always outperforms for stability workflows.
- Tm-Vec and similar learned Tm predictors offer coarse-grained Tm estimates from sequence alone but show high variance on proteins distant from their training distribution.
- Integrative workflows combining ΔG estimates with ΔTm-scale signals are consistently favoured over single-score ranking when thermostability is the explicit objective.
- Protein family-specific calibration substantially improves prediction accuracy; always search for characterised homologs before interpreting raw scores.

## 10) Quick Reference: Tool Availability

| Tool | Input | Output | Availability |
|---|---|---|---|
| FoldX | Structure (.pdb) | ΔG, ΔΔG (kcal/mol) | License required (academic free) |
| HoTMuSiC | Structure | ΔTm (°C) | Web server |
| MAESTRO | Structure | ΔΔG + Tm indication | Web server / standalone |
| ThermoNet | Structure | ΔΔG (kcal/mol) | Open source |
| ESM-1v | Sequence | Log-likelihood delta | Open source (Meta) |
| GEMME | Sequence MSA | Evolutionary effect score | Web server / standalone |
| Tm-Vec | Sequence | Predicted Tm (°C) | Open source |
| predict_heat_stability.py | Sequence | Feature-based class | Included in this skill |
