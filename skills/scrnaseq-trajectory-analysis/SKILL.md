---
name: scrnaseq-trajectory-analysis
description: Pseudotime inference and RNA velocity analysis of single-cell RNA-seq data using Monocle3 and scVelo.
---

# Skill: scRNA-seq Trajectory Analysis

## Use When

- User wants to infer developmental or differentiation trajectories from a single-cell dataset.
- User wants to order cells along a pseudotime axis representing a biological process (e.g., differentiation, activation, cell cycle).
- User wants to compute RNA velocity to infer the future transcriptional state of cells from spliced/unspliced read ratios.
- User wants to identify genes that change significantly along a trajectory.

## Inputs

- Required:
  - Clustered and annotated AnnData (.h5ad) or Seurat object (.rds) with UMAP coordinates
- Optional:
  - Analysis type: `pseudotime`, `velocity`, or `both` (default: `pseudotime`)
  - Pseudotime tool: `monocle3` or `diffusion-pseudotime` (default: `monocle3`)
  - Root cell cluster or cell type (required for pseudotime; must be biologically the starting state)
  - For RNA velocity: spliced/unspliced count matrices as a loom file (`velocyto` output) or STARsolo with `--soloFeatures Velocyto`
  - Velocity model: `stochastic` or `dynamical` (default: `stochastic`; use `dynamical` for more accuracy at higher compute cost)
  - Gene significance threshold for pseudotime-variable genes (default: q-value < 0.05)

## Workflow

### Pseudotime (Monocle3)

1. Convert the AnnData or Seurat object to a Monocle3 CellDataSet using `as.cell_data_set()` (Seurat) or the `scverse` Monocle3 bridge.
2. Run `learn_graph()` to fit a principal graph through the UMAP embedding. The graph represents the trajectory topology.
3. Set root cells by specifying the root cluster or cell type. If multiple root candidates exist, present options to the user. Root selection must be biologically justified (earliest developmental state, undifferentiated progenitors, etc.).
4. Order cells along pseudotime with `order_cells()`. Inspect the pseudotime UMAP plot for biological plausibility (expected early → late ordering).
5. Identify genes that change significantly along the principal graph using `graph_test()` (Moran's I spatial autocorrelation). Retain genes with q-value < 0.05.
6. Plot gene expression trends along pseudotime for the top significant genes (`plot_genes_in_pseudotime`).

### RNA Velocity (scVelo)

1. Generate spliced/unspliced/ambiguous count matrices:
   - Using velocyto CLI: `velocyto run10x` on the Cell Ranger output BAM and genome GTF.
   - Using STARsolo: add `--soloFeatures Velocyto` to the STAR command during alignment.
2. Load the loom file alongside the AnnData object; merge spliced, unspliced, and ambiguous layers.
3. Preprocess velocity data: `scv.pp.filter_and_normalize()` (filter genes with insufficient spliced/unspliced counts), `scv.pp.moments()` (compute first and second-order moments of gene expression for neighbors).
4. Estimate RNA velocity:
   - Stochastic model: `scv.tl.velocity(mode='stochastic')` — fast, suitable for exploratory analysis.
   - Dynamical model: `scv.tl.recover_dynamics()` then `scv.tl.velocity(mode='dynamical')` — more accurate, identifies kinetic rate parameters (transcription, splicing, degradation rates).
5. Compute velocity graph: `scv.tl.velocity_graph()`. Project velocity arrows onto the UMAP: `scv.pl.velocity_embedding_stream()`.
6. Identify velocity genes (genes driving the velocity signal): `scv.tl.rank_velocity_genes()`.
7. Compute latent time (a global pseudotime derived from velocity): `scv.tl.latent_time()` (dynamical model only).

## Output Contract

- Updated AnnData (.h5ad) or Seurat/CellDataSet object with pseudotime values and/or velocity embeddings
- UMAP colored by pseudotime (PDF)
- Velocity stream plot on UMAP (PDF)
- Pseudotime-variable genes table (TSV): gene, Moran's I, q-value, spatial autocorrelation
- Gene expression along pseudotime plots for top 10 genes (PDF)
- Velocity genes table (TSV): gene, velocity score, rank
- Latent time UMAP (PDF, dynamical model only)

## Limits

- Pseudotime assumes a continuous biological process; applying it to unrelated or discrete cell populations produces meaningless orderings.
- Root cell selection requires biological prior knowledge; incorrect root selection produces reversed or meaningless pseudotime.
- RNA velocity requires spliced/unspliced count matrices generated at the alignment step; these are not produced by default Cell Ranger output and must be generated separately with velocyto or STARsolo.
- The dynamical scVelo model requires significantly more computation time (hours for large datasets) and convergence is not guaranteed for all genes.
- Trajectory analysis is sensitive to clustering quality; poorly resolved clusters lead to discontinuous or looped trajectories.
- RNA velocity assumptions (constant kinetics) may not hold in rapidly changing systems; interpret velocity arrows as directional tendencies, not deterministic predictions.
- Common failure cases:
  - Monocle3 `learn_graph()` producing a disconnected graph; increase `minimal_branch_len` or ensure the UMAP has smooth transitions between related clusters.
  - scVelo `recover_dynamics()` failing due to insufficient cells expressing a gene in both spliced and unspliced forms; lower the `min_shared_counts` threshold.
  - Velocyto CLI running for many hours on large BAM files; consider using STARsolo `--soloFeatures Velocyto` during alignment instead.
