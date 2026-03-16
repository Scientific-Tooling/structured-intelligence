---
name: scrnaseq-quality-control
description: Ambient RNA removal, doublet detection, and cell filtering for single-cell RNA-seq count matrices.
---

# Skill: scRNA-seq Quality Control

## Use When

- User has a feature-barcode count matrix (from Cell Ranger, STARsolo, or alevin-fry) and needs to remove low-quality cells and technical artifacts.
- User wants to detect and filter doublets (two or more cells captured in one droplet).
- User wants to remove ambient RNA contamination from the count matrix.
- User needs to determine appropriate filtering thresholds before clustering.

## Inputs

- Required:
  - Feature-barcode matrix directory or AnnData (.h5ad) or Seurat object (.rds)
  - Raw (unfiltered) matrix directory (required for SoupX/CellBender ambient RNA removal)
- Optional:
  - Framework: `scanpy` or `seurat` (default: `scanpy`)
  - Ambient RNA removal tool: `soupx`, `cellbender`, or `none` (default: `soupx`)
  - Doublet detection tool: `scrublet`, `scdblfinder`, or `doubletfinder` (default: `scrublet` for Scanpy, `scdblfinder` for Seurat)
  - Mitochondrial gene prefix (default: `MT-` for human, `mt-` for mouse)
  - Filtering thresholds: min/max nFeature_RNA, min/max nCount_RNA, max percent.mt (defaults: 200–6000 genes, 500–50000 UMIs, <20% MT)
  - Expected doublet rate (default: 0.008 per 1000 cells loaded)

## Workflow

1. Load the filtered feature-barcode matrix into Scanpy (AnnData) or Seurat.
2. Calculate per-cell QC metrics: number of genes detected (`nFeature_RNA`), total UMI count (`nCount_RNA`), fraction of mitochondrial reads (`percent.mt`), and fraction of ribosomal reads (`percent.ribo`).
3. Visualize QC metric distributions as violin plots and scatter plots (`nCount_RNA` vs `nFeature_RNA`, `nCount_RNA` vs `percent.mt`).
4. Remove ambient RNA contamination:
   - SoupX (R): estimate the soup fraction using the raw + filtered matrices, correct counts, output a corrected count matrix.
   - CellBender (Python): run `cellbender remove-background` on the raw matrix; use GPU if available for speed.
5. Detect doublets:
   - Scrublet (Python/Scanpy): simulate doublets by combining random cell pairs; assign doublet scores per cell; threshold at bimodal score distribution.
   - scDblFinder (R/Bioconductor): simulate doublets and classify with a random forest classifier; recommended for Seurat workflows.
   - DoubletFinder (Seurat, R): requires a pre-clustered object; insert after a first round of clustering.
6. Apply filtering thresholds to remove low-quality cells. Adjust thresholds based on tissue type and expected cell size (e.g., neurons have high UMI counts; platelets have very low gene counts). Use MAD-based adaptive thresholds if cell populations are heterogeneous.
7. Report a cell retention summary: input cells, cells after ambient correction, cells after doublet removal, cells after threshold filtering.
8. Save filtered AnnData (.h5ad) or Seurat object (.rds).

## Output Contract

- Filtered count matrix as AnnData (.h5ad) or Seurat object (.rds)
- QC metric violin plots and scatter plots (PDF)
- Doublet score distribution and UMAP plot (PDF)
- Cell retention summary table (TSV): filter stage, cells retained, cells removed

## Limits

- SoupX requires both raw and filtered matrices; CellBender corrects empty droplets more aggressively but requires GPU for practical runtime.
- Mitochondrial thresholds vary by tissue: brain neurons tolerate higher MT% (up to 30%), while immune cells are typically <10%.
- Doublet rates depend on loading density: ~0.8% per 1000 cells for 10x Chromium v3.
- Aggressive filtering on gene count can eliminate genuine rare cell types with low transcriptional activity (e.g., platelets, quiescent stem cells); inspect boundary cells carefully.
- CellBender is slow on CPU (several hours per sample); plan accordingly if no GPU is available.
- Common failure cases:
  - SoupX fails if the raw matrix directory is missing or misnamed.
  - Scrublet thresholding fails on unimodal score distributions (all scores similar); inspect the histogram and set threshold manually.
  - Seurat object version mismatch when loading `.rds` files between Seurat v4 and v5.
