---
name: scrnaseq-differential-expression
description: Single-cell differential expression analysis using Wilcoxon rank-sum tests and pseudobulk approaches with DESeq2 or edgeR.
---

# Skill: scRNA-seq Differential Expression

## Use When

- User wants to find differentially expressed genes between two conditions (e.g., treated vs control) within a cell type.
- User wants to identify marker genes that distinguish one cluster or cell type from all others.
- User is performing a multi-sample study and wants statistically rigorous pseudobulk DE analysis.
- User wants to generate volcano plots or heatmaps of DE results.

## Inputs

- Required:
  - Annotated AnnData (.h5ad) or Seurat object (.rds) with cell type labels
  - Contrast definition: condition A vs condition B (column name + values in obs/metadata), or cell type comparison
- Optional:
  - Framework: `scanpy` or `seurat` (default: `scanpy`)
  - DE method: `wilcoxon`, `pseudobulk-deseq2`, or `pseudobulk-edger` (default: `pseudobulk-deseq2` for multi-sample; `wilcoxon` for single-sample)
  - Cell type column name (default: `cell_type`)
  - Condition column name (default: `condition`)
  - Sample column name for pseudobulk aggregation (default: `sample`)
  - Minimum cells per group for inclusion (default: 10)
  - Log2FC threshold (default: 0.5)
  - Adjusted p-value threshold (default: 0.05)

## Workflow

1. Determine the appropriate test strategy:
   - Single-sample or within-cluster comparison: use Wilcoxon rank-sum test (fast, non-parametric).
   - Multi-sample experiment (≥ 3 samples per condition): use pseudobulk DE with DESeq2 or edgeR (statistically rigorous, accounts for sample-level variation).
2. For Wilcoxon DE: run `sc.tl.rank_genes_groups` (Scanpy) or `FindMarkers` (Seurat) between the specified groups within each cell type. Apply logFC and p-value filters.
3. For pseudobulk DE:
   a. Aggregate raw counts per cell type per sample (sum of UMIs across all cells of that type in that sample).
   b. Exclude cell-type–sample combinations with fewer than the minimum cell count threshold.
   c. Run DESeq2 (`DESeqDataSetFromMatrix`, Wald test) or edgeR (`DGEList`, `glmQLFTest`) on the aggregated count matrix.
   d. Use the sample as the replicate unit; include batch as a covariate in the design formula if applicable.
4. Filter DE results: retain genes with |log2FC| > threshold and adjusted p-value < threshold.
5. Generate a volcano plot per cell type comparison (log2FC on x-axis, -log10 adjusted p-value on y-axis; label top 10 genes).
6. Generate a heatmap of the top 50 DE genes across cells grouped by condition and cell type.
7. Optionally pass DE gene lists to the rnaseq-functional-enrichment skill for pathway analysis.
8. Report a summary table: comparison name, cell type, total significant DE genes, up-regulated count, down-regulated count.

## Output Contract

- DE results per comparison and cell type (TSV): gene, log2FC, pct.1, pct.2, p_val, p_val_adj, comparison, cell_type
- Volcano plots per cell type (PDF)
- Top DE gene heatmap across conditions (PDF)
- Summary table: comparison, cell type, n_sig, n_up, n_down (TSV)

## Limits

- Single-cell Wilcoxon tests are inflated when many cells are available (high statistical power for tiny effects); use pseudobulk for multi-sample designs to avoid false positives.
- Pseudobulk DE requires ≥ 3 biological replicates (samples) per condition, matching bulk RNA-seq requirements.
- Cells from the same sample are not independent; ignoring sample as a random effect leads to inflated false-positive rates (pseudo-replication).
- Very small clusters (<50 cells per group) have insufficient power for DE; results from such clusters should be treated as exploratory.
- Pseudobulk aggregation can produce zero-count samples for rare cell types; these are automatically excluded.
- Common failure cases:
  - DESeq2 failing due to a cell-type–sample combination with all-zero counts after aggregation; increase the minimum cell threshold.
  - FindMarkers returning no significant genes because the contrast groups are not in the `ident` slot; check that `Idents()` is set correctly.
  - Wilcoxon results with thousands of significant genes even at small effect sizes in a large dataset; switch to pseudobulk or apply a stricter logFC threshold.
