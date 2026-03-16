---
name: scrnaseq-standard
description: Standard single-cell RNA-seq analysis pipeline from raw FASTQ to annotated cell atlas, with optional integration and trajectory analysis.
---

# Workflow: scRNA-seq Standard Analysis

## Overview

This workflow processes single-cell RNA-seq data from raw FASTQ files to a biologically annotated cell atlas. It supports 10x Chromium and other droplet-based protocols, single-sample and multi-sample experiments, and optional trajectory analysis.

## Pipeline Steps

```
FASTQ → scrnaseq-cellranger-count → scrnaseq-quality-control → [scrnaseq-integration (multi-sample)] → scrnaseq-clustering → scrnaseq-cell-type-annotation → scrnaseq-differential-expression → [scrnaseq-trajectory-analysis (optional)]
```

### Step 1: Generate Count Matrix

**Skill**: `scrnaseq-cellranger-count`

Align raw FASTQ reads to the reference transcriptome and produce a per-cell feature-barcode count matrix. Produces both a filtered matrix (cell-called barcodes) and a raw matrix (all barcodes, needed for ambient RNA removal).

**Tool decision**:
- Cell Ranger: preferred for 10x data, produces a complete web summary and BAM file.
- STARsolo: open-source alternative; use when Cell Ranger licensing is unavailable.
- alevin-fry: fastest option; use for large cohorts or compute-constrained environments.

**Key parameters**: Chemistry (auto-detect or specify v2/v3/v3.1), reference genome build (must match downstream annotation).

**Input**: Raw FASTQ + reference transcriptome.
**Output**: Filtered + raw feature-barcode matrices, cell calling summary.

### Step 2: Quality Control

**Skill**: `scrnaseq-quality-control`

Remove ambient RNA contamination (SoupX or CellBender), detect and remove doublets (Scrublet or scDblFinder), and filter low-quality cells by gene count, UMI count, and mitochondrial fraction.

**Pass criteria**:
- Fraction reads in cells ≥ 60% (from Step 1 summary)
- Median genes per cell ≥ 500
- After QC: cell doublet rate < 2%, median percent.mt < 20% for the retained cells

**Key decision**: Ambient RNA correction threshold — SoupX is faster; CellBender is more accurate but requires GPU.

**Input**: Filtered + raw count matrices.
**Output**: QC-filtered AnnData (.h5ad) or Seurat object (.rds), QC metric plots.

### Step 3: Integration (Multi-Sample Only)

**Skill**: `scrnaseq-integration`

Skip this step for single-sample experiments. For multi-sample or multi-batch experiments, integrate datasets to correct batch effects before clustering.

**Method decision**:

| Criterion | Harmony | Seurat RPCA | scVI |
|-----------|---------|-------------|------|
| Speed | Fast | Moderate | Slow (GPU) |
| Dataset size | Any | ≤500k cells | Large |
| Corrected counts | No (embedding only) | Yes | Yes (latent space) |
| Recommended for | Most cases | Cross-dataset | Complex batch structure |

**Validate integration**: UMAP should show batch mixing within cell types; known markers should remain cluster-specific.

**Input**: Multiple QC-filtered objects or a concatenated object with batch labels.
**Output**: Integrated object with corrected embedding, integration quality metrics.

### Step 4: Clustering

**Skill**: `scrnaseq-clustering`

Normalize, select highly variable genes, run PCA, build kNN graph, cluster with Leiden algorithm, and compute UMAP embedding.

**Normalization decision**:
- `lognorm` (CPM + log1p): default; compatible with all downstream tools.
- `scttransform`: better for datasets with high sequencing depth variation; computationally expensive for >100k cells.

**Resolution guidance**: Start at 0.5; increase for finer resolution (rare subpopulations), decrease if clusters appear biologically implausible. Run at multiple resolutions and compare cluster stability.

**Input**: QC-filtered (or integrated) AnnData or Seurat object.
**Output**: Clustered object with UMAP, cluster membership table.

### Step 5: Cell Type Annotation

**Skill**: `scrnaseq-cell-type-annotation`

Assign biological cell type labels using marker genes and automated reference-based methods (SingleR or Azimuth). Cross-validate automated labels against canonical literature markers.

**Key decision**: Reference dataset must match the tissue and species. Check Azimuth reference availability for the tissue before running.

**Pass criteria**: Each cluster has a clear top marker (logFC > 0.5, pct.1 > 0.3); automated and manual labels agree for ≥ 80% of clusters.

**Input**: Clustered object.
**Output**: Annotated object with `cell_type` column, marker gene tables, annotated UMAP.

### Step 6: Differential Expression

**Skill**: `scrnaseq-differential-expression`

Find genes differentially expressed between conditions within each cell type.

**Test decision**:
- Single sample or exploratory: Wilcoxon rank-sum (fast, no replicates needed).
- Multi-sample with ≥ 3 replicates per condition: pseudobulk DESeq2 (statistically rigorous).

**Input**: Annotated object + condition metadata.
**Output**: DE gene tables per cell type, volcano plots, summary table.

### Step 7: Trajectory Analysis (Optional)

**Skill**: `scrnaseq-trajectory-analysis`

Use only when a continuous biological process (differentiation, activation, cell cycle) is expected. Not appropriate for discrete, unrelated cell populations.

**Analysis decision**:
- Pseudotime (Monocle3): for any continuous trajectory; requires root cell specification.
- RNA velocity (scVelo): for systems with active transcriptional dynamics; requires spliced/unspliced counts generated during alignment.

**Input**: Annotated object (+ loom file for RNA velocity).
**Output**: Pseudotime-colored UMAP, trajectory-variable gene table, velocity stream plot.

## Shared References

- [File Formats](../../knowledge/sources/genomics/file-formats.md)
- [Reference Genomes](../../knowledge/sources/genomics/reference-genomes.md)
- [Quality Thresholds](../../knowledge/sources/genomics/quality-thresholds.md)
- [R Environment Setup](../../knowledge/sources/genomics/r-environment-setup.md)
