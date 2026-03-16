---
name: scrnaseq-integration
description: Multi-sample batch correction and integration of single-cell RNA-seq datasets using Harmony, Seurat CCA/RPCA, or scVI.
---

# Skill: scRNA-seq Integration

## Use When

- User has multiple samples or batches and wants to correct batch effects before clustering and cell type annotation.
- User wants to build a joint embedding from datasets generated at different times, labs, or with different protocols.
- User needs to assess integration quality with quantitative metrics.
- User wants to compare integration methods for a given dataset.

## Inputs

- Required:
  - Multiple AnnData (.h5ad) or Seurat objects (.rds), one per sample or batch, **or** a single concatenated object with a batch/sample label column
- Optional:
  - Framework: `scanpy` or `seurat` (default: `scanpy`)
  - Integration method: `harmony`, `seurat-cca`, `seurat-rpca`, or `scvi` (default: `harmony`)
  - Batch variable column name (default: `batch`)
  - Number of HVGs (default: 3000)
  - Number of PCs for integration (default: 30)
  - Number of Harmony iterations (default: 10)
  - scVI latent dimensions (default: 20)
  - Clustering resolution after integration (default: 0.5)

## Workflow

1. Load all sample objects and concatenate into a single AnnData or Seurat object, adding a `batch` (or `sample`) column to obs/metadata.
2. Run per-sample normalization (log1p or SCTransform) using identical parameters across all samples. Do not normalize again after concatenation.
3. Select HVGs using batch-aware selection: compute HVGs per batch and take the union of the top genes appearing in most batches (`sc.pp.highly_variable_genes` with `batch_key` parameter).
4. Run PCA on the unintegrated data; plot a UMAP to visualize the extent of batch effects before integration.
5. Run the selected integration method:
   - **Harmony**: run `sc.external.pp.harmony_integrate` (Scanpy) or `RunHarmony` (Seurat) on the PCA embedding. Harmony corrects only the PCA coordinates; raw counts remain unchanged.
   - **Seurat CCA**: run `FindIntegrationAnchors` with `reduction = "cca"` then `IntegrateData`; produces a corrected expression matrix.
   - **Seurat RPCA**: run `FindIntegrationAnchors` with `reduction = "rpca"` then `IntegrateData`; faster than CCA for large datasets.
   - **scVI**: train a variational autoencoder using `scvi.model.SCVI` with the batch key; extract latent representation (20 dimensions) as the integrated embedding.
6. Compute the kNN graph and Leiden/Louvain clusters on the integrated embedding.
7. Compute UMAP on the integrated embedding. Plot UMAP colored by batch/sample (to confirm mixing) and by cluster (to confirm biological signal is preserved).
8. Assess integration quality:
   - LISI score (Local Inverse Simpson's Index): higher batch LISI = better mixing; higher biological LISI = preserved biology.
   - kBET (k-nearest neighbor batch effect test): fraction of cells with well-mixed neighborhoods.
   - Silhouette score: positive for biological clusters, near-zero for batch.
9. Save integrated AnnData (.h5ad) or Seurat object (.rds) with the integrated embedding and cluster labels.

## Output Contract

- Integrated AnnData (.h5ad) or Seurat object (.rds) with integrated embedding (`X_pca_harmony`, `X_scVI`, or equivalent) and cluster labels
- UMAP plots before and after integration, colored by batch and cluster (PDF)
- Integration quality metrics table (TSV): LISI (batch), LISI (bio), kBET acceptance rate, silhouette score
- Per-sample cell count summary table (TSV): sample, n_cells, n_clusters

## Limits

- Harmony corrects only the PCA embedding; do not use Harmony-corrected PCA coordinates as a substitute for corrected expression values in differential expression.
- scVI requires GPU for practical runtime on large datasets (>100k cells); training on CPU can take many hours.
- Over-integration can merge biologically distinct cell types with similar transcriptomes (e.g., tissue macrophages and circulating monocytes); always validate cluster identity with canonical markers after integration.
- Different integration methods may produce meaningfully different results; Harmony is the recommended starting point due to speed and reliability. Escalate to scVI if Harmony leaves visible batch structure.
- Datasets with very different protocols (e.g., 10x v2 vs v3, or FACS-sorted vs droplet) may require protocol-specific covariates in addition to the batch variable.
- Common failure cases:
  - Harmony not converging (LISI not improving after iterations); check that the batch variable has more than one level and that HVG selection used `batch_key`.
  - scVI training producing NaN loss; reduce learning rate or check for cells with zero counts after filtering.
  - Seurat CCA failing on very large datasets (>500k cells) due to memory; switch to RPCA or scVI.
