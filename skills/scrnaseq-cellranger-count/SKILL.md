---
name: scrnaseq-cellranger-count
description: Generate feature-barcode count matrices from raw scRNA-seq FASTQ files using Cell Ranger, STARsolo, or alevin-fry.
---

# Skill: scRNA-seq Cell Ranger Count

## Use When

- User has raw FASTQ files from a droplet-based single-cell protocol (10x Chromium, Parse Biosciences, etc.) and needs a feature-barcode count matrix.
- User wants to run Cell Ranger count, STARsolo, or alevin-fry to produce per-cell gene expression matrices.
- User needs to assess sequencing saturation or cell calling statistics before downstream analysis.
- User is generating input for the scrnaseq-quality-control skill.

## Inputs

- Required:
  - Raw FASTQ files (Cell Ranger naming: `{sample}_S{n}_L00{lane}_R{read}_001.fastq.gz`)
  - Reference transcriptome (Cell Ranger reference package, STAR genome index, or salmon index)
- Optional:
  - Aligner choice: `cellranger`, `starsolo`, or `alevin-fry` (default: `cellranger`)
  - 10x chemistry: `auto`, `threeprime`, `fiveprime`, `SC3Pv2`, `SC3Pv3`, `SC3Pv3.1`, `SC3Pv4` (default: `auto`)
  - Number of threads (default: 8)
  - Expected number of cells (leave unset to use automatic knee-point detection)
  - Output directory (default: `./cellranger_output`)
  - Cell barcode whitelist (required for STARsolo; bundled in Cell Ranger reference)

## Workflow

1. Validate FASTQ naming convention. Cell Ranger requires `{sample}_S{n}_L00{lane}_R{read}_001.fastq.gz`; rename files if needed. STARsolo accepts generic paired FASTQ names.
2. If Cell Ranger: run `cellranger count` with `--id`, `--transcriptome`, `--fastqs`, `--sample`, and `--chemistry` flags.
3. If STARsolo: run STAR with `--soloType CB_UMI_Simple`, providing `--soloCBwhitelist`, `--soloCBstart/End`, `--soloUMIstart/End` for the appropriate chemistry.
4. If alevin-fry: run `simpleaf quant` with the pre-built index and chemistry string; use `--resolution cr-like` for Cell Ranger-compatible output.
5. Report cell calling statistics: estimated cells, mean reads per cell, median genes per cell, sequencing saturation, fraction reads in cells.
6. Verify output: confirm existence of filtered and raw (unfiltered) feature-barcode matrices in MEX format.

## Output Contract

- Filtered feature-barcode matrix directory (`filtered_feature_bc_matrix/`): `matrix.mtx.gz`, `barcodes.tsv.gz`, `features.tsv.gz`
- Raw (unfiltered) feature-barcode matrix directory (`raw_feature_bc_matrix/`)
- Web summary HTML (Cell Ranger: `web_summary.html`) or equivalent STARsolo/alevin-fry summary
- Per-barcode metrics CSV (`metrics_summary.csv` for Cell Ranger)
- BAM file and index (Cell Ranger only: `possorted_genome_bam.bam`, `.bai`)

## Limits

- Cell Ranger requires a commercial license (free for academic) and approximately 10–30 GB disk per sample for intermediate files.
- STARsolo requires a STAR genome index and the appropriate cell barcode whitelist (bundled in Cell Ranger references or available from 10x Genomics).
- alevin-fry is fastest and lowest-memory but requires salmon index built with `simpleaf index`.
- Cell calling at the knee-point may under-call rare cell types; consider running EmptyDrops (via DropletUtils in R) on the raw matrix for improved sensitivity.
- Ambient RNA contamination is not removed at this step; handle in the scrnaseq-quality-control skill.
- Reference genome and transcriptome annotation must match (same genome build and GTF version).
- Common failure cases:
  - FASTQ naming mismatch causing Cell Ranger to find no reads for the sample.
  - Chemistry mismatch (`auto` detection fails on unusual protocols); specify explicitly.
  - Insufficient disk space for BAM file (~10x raw FASTQ size).
  - Reference built with a different Cell Ranger version causing incompatibility.
