---
name: scrnaseq-cell-type-annotation
description: Marker-based and reference-based cell type annotation of single-cell RNA-seq clusters using SingleR, Azimuth, or manual curation.
---

# Skill: scRNA-seq Cell Type Annotation

## Use When

- User has a clustered single-cell dataset and wants to assign biological cell type labels to clusters.
- User wants to use automated reference-based annotation (SingleR, Azimuth) alongside manual marker validation.
- User wants to generate per-cluster marker gene tables and visualizations.
- User needs cell type composition summaries across samples.

## Inputs

- Required:
  - Clustered AnnData (.h5ad) or Seurat object (.rds) with UMAP coordinates
- Optional:
  - Framework: `scanpy` or `seurat` (default: `scanpy`)
  - Annotation method: `singler`, `azimuth`, `manual`, or `combined` (default: `combined`)
  - Reference dataset for SingleR: e.g., `HumanPrimaryCellAtlasData`, `BlueprintEncodeData`, `MouseRNAseqData`, or path to a user-provided reference (default: `HumanPrimaryCellAtlasData`)
  - Azimuth reference tissue (e.g., `pbmcref`, `bonemarrowref`, `lungref`, `kidneyref`, `brainref`)
  - Custom marker gene list (YAML or CSV with cell type → gene list mapping)
  - Minimum log2FC for marker genes (default: 0.25)
  - Minimum fraction of cells expressing the gene in the cluster, `pct.1` (default: 0.1)

## Workflow

1. Find cluster marker genes using Wilcoxon rank-sum test (`sc.tl.rank_genes_groups` in Scanpy or `FindAllMarkers` in Seurat). Retain genes with logFC > 0.25, pct.1 > 0.1, and adjusted p-value < 0.05.
2. Generate dot plots and feature plots for the top 5 marker genes per cluster to visualize expression specificity.
3. If `singler` or `combined`: run SingleR using the specified reference dataset. Map cluster-level pseudobulk profiles to reference cell types. Report per-cluster label and confidence score (delta.next statistic).
4. If `azimuth` or `combined`: run Azimuth reference mapping. Map query cells to the reference UMAP; assign predicted cell type label and confidence score per cell.
5. Cross-validate automated labels against canonical lineage markers from the literature (e.g., CD3D/CD3E for T cells, CD19/MS4A1 for B cells, LYZ/CD14 for monocytes, EPCAM for epithelial, PECAM1 for endothelial).
6. Assign final cell type labels per cluster. Merge clusters with identical cell types if biologically justified; flag ambiguous clusters for manual review.
7. Plot an annotated UMAP with cell type labels.
8. Compute cell type composition per sample as a fraction of total cells; generate a stacked bar plot.
9. Save annotated AnnData (.h5ad) or Seurat object (.rds) with `cell_type` annotation in obs/metadata.

## Output Contract

- Annotated AnnData (.h5ad) or Seurat object (.rds) with `cell_type` column in obs
- Marker gene table per cluster (TSV): gene, cluster, log2FC, pct.1, pct.2, adj_p_value
- Dot plot of top markers per cluster (PDF)
- Feature plots for canonical lineage markers (PDF)
- SingleR/Azimuth prediction table (TSV): cluster or cell barcode, predicted label, confidence score
- Annotated UMAP plot (PDF)
- Cell type composition table and stacked bar plot per sample (TSV + PDF)

## Limits

- Automated annotation accuracy depends on reference dataset relevance to the tissue and species; cross-species or rare cell types may be mislabeled.
- Manual validation against literature markers is always required; treat automated labels as hypotheses.
- Azimuth reference panels are tissue-specific: check availability before use (PBMC, bone marrow, lung, kidney, brain, fetal development).
- Batch effects can cause the same cell type to split across clusters; address batch effects with scrnaseq-integration before annotation.
- Marker gene overlap between closely related subtypes (e.g., CD4+ T cell subsets) requires sub-clustering or additional markers for resolution.
- SingleR performs poorly when the query tissue contains cell types absent from the reference; spurious assignments appear with low confidence scores (delta.next < 0.05).
- Common failure cases:
  - Reference dataset species mismatch (e.g., using a human reference for mouse data) causing all cells to map to the wrong types.
  - Azimuth reference not installed or outdated; update with `SeuratData::InstallData()`.
  - Marker-based annotation failing because the dataset is poorly clustered (resolution too low); re-cluster at higher resolution before annotating.
