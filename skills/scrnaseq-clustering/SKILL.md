---
name: scrnaseq-clustering
description: Normalization, highly variable gene selection, PCA, UMAP, and Leiden/Louvain clustering of single-cell RNA-seq data.
---

# Skill: scRNA-seq Clustering

## Use When

- User has a QC-filtered count matrix and wants to cluster cells into groups.
- User wants to generate UMAP or tSNE embeddings for visualization.
- User needs to perform dimensionality reduction before cell type annotation or differential expression.

## Inputs

- Required:
  - Filtered AnnData (.h5ad) or Seurat object (.rds)
- Optional:
  - Framework: `scanpy` or `seurat` (default: `scanpy`)
  - Normalization method: `lognorm` or `scttransform` (default: `lognorm`)
  - Number of highly variable genes (default: 3000)
  - Number of PCs to compute (default: 50)
  - Number of PCs to use for neighbor graph (default: 30; refine with elbow plot)
  - Number of neighbors for kNN graph (default: 15)
  - Clustering resolution (default: 0.5; range 0.1–2.0)
  - Clustering algorithm: `leiden` or `louvain` (default: `leiden`)
  - Variables to regress out (default: none; options: `nCount_RNA`, `percent.mt`)
  - Random seed (default: 42)

## Workflow

1. Normalize counts: CPM normalization (counts per 10,000) followed by log1p transformation (`sc.pp.normalize_total` + `sc.pp.log1p` in Scanpy; `NormalizeData` in Seurat), or run SCTransform (Seurat v5 / `scran` for Scanpy).
2. Select highly variable genes (HVGs): use `seurat_v3` flavor in Scanpy or `FindVariableFeatures` in Seurat; default to top 3000 HVGs.
3. Scale gene expression to zero mean and unit variance (`sc.pp.scale` or `ScaleData`). If regression is requested, regress out `nCount_RNA` and/or `percent.mt` during scaling. Skip scaling for SCTransform workflows.
4. Run PCA on the HVG-scaled matrix (`sc.tl.pca` or `RunPCA`); compute 50 PCs. Plot an elbow plot to identify where variance plateaus and select the number of PCs for the neighbor graph.
5. Compute the k-nearest neighbor (kNN) graph in PCA space (`sc.pp.neighbors` or `FindNeighbors`) using the selected number of PCs.
6. Cluster cells with the Leiden algorithm (`sc.tl.leiden`) or Louvain (`sc.tl.louvain` / `FindClusters`). Test at least two resolutions (e.g., 0.3 and 0.8) and compare cluster stability.
7. Compute UMAP embedding (`sc.tl.umap` or `RunUMAP`); optionally compute tSNE. Always set a fixed random seed.
8. Plot UMAP colored by: cluster ID, QC metrics (`nFeature_RNA`, `nCount_RNA`, `percent.mt`), and sample of origin. Flag clusters with elevated QC metrics as potentially low-quality.
9. Save updated AnnData (.h5ad) or Seurat object (.rds) with embeddings and cluster labels.

## Output Contract

- Updated AnnData (.h5ad) or Seurat object (.rds) with cluster labels (`leiden` or `seurat_clusters` column) and UMAP/tSNE coordinates
- UMAP plots colored by cluster, QC metrics, and sample (PDF)
- PCA elbow plot (PDF)
- Cluster membership table (TSV): cell barcode, cluster ID, UMAP1, UMAP2

## Limits

- Leiden resolution parameter strongly controls granularity: lower values (0.1–0.3) yield fewer, broader clusters; higher values (1.0–2.0) yield many fine-grained clusters.
- Scaling with regression is incompatible with SCTransform; choose one normalization path.
- UMAP is non-deterministic without a fixed random seed; always set `random_state=42`.
- Cell cycle effects may separate proliferating cells into their own cluster regardless of lineage; regress out cell cycle scores if this is not the biology of interest (`sc.tl.score_genes_cell_cycle`).
- SCTransform is computationally expensive for datasets with more than 100,000 cells; use `lognorm` for very large datasets.
- Neighbor graph quality depends on the number of PCs chosen; too few PCs lose biological signal, too many add noise. Use the elbow plot as a guide.
- Common failure cases:
  - Leiden clustering producing a single cluster (resolution too low) or as many clusters as cells (resolution too high); adjust resolution.
  - UMAP looks identical across runs due to missing random seed; check `random_state` parameter.
  - SCTransform failing due to insufficient memory on large datasets (>200k cells); fall back to lognorm.
