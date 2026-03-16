---
name: bioinformatics-env-setup
description: Guide users through installing and verifying bioinformatics software for NGS, RNA-seq, scRNA-seq, and metagenomics pipelines using conda, pip, or manual installation.
---

# Skill: Bioinformatics Environment Setup

## Use When

- User is starting a new analysis and wants to install the required bioinformatics tools.
- A pipeline step fails because a tool is missing or the wrong version is installed.
- User asks how to install a specific bioinformatics tool (e.g., STAR, Cell Ranger, Scanpy, Seurat).
- User wants a ready-to-use conda environment for a specific pipeline.
- User is setting up a new compute environment (HPC, cloud VM, local workstation).

## Inputs

- Required:
  - Target pipeline(s): one or more of `ngs-shared`, `wgs`, `rnaseq`, `scrnaseq`, `metagenomics`, or `all`
- Optional:
  - Installation method: `conda` (default), `docker`, or `manual`
  - Operating system: `linux` (default), `macos`
  - Environment name prefix (default: `bioinfo`)
  - Conda channel priority: `strict` (default, reproducible) or `flexible`
  - Whether to verify existing installations before installing (default: true)

## Workflow

1. **Detect the environment**: Check whether `conda`/`mamba` is available (`which conda`), whether Docker is available (`docker --version`), and whether an HPC module system is present (`module avail`). Report findings to the user and recommend the best installation path.

2. **Check existing installations**: For each tool in the requested pipeline group(s), run `which <tool> && <tool> --version 2>&1 | head -1` to detect installed versions. Report a summary table: tool name, found/missing, installed version, required minimum version.

3. **Select the installation asset**: Choose the appropriate conda environment YAML from `assets/envs/`:
   - `ngs-shared.yaml` — FastQC, MultiQC, fastp, Trimmomatic, samtools
   - `wgs.yaml` — BWA-MEM2, GATK, Picard, bcftools, VEP, SnpEff
   - `rnaseq.yaml` — STAR, HISAT2, featureCounts (subread), salmon, kallisto, DESeq2 (R), edgeR (R)
   - `scrnaseq-python.yaml` — STARsolo (STAR), Scanpy, scVI-tools, scVelo, Scrublet, CellBender, harmonypy
   - `scrnaseq-r.yaml` — Seurat v5, SingleR, scDblFinder, SoupX, Monocle3, DoubletFinder
   - `metagenomics.yaml` — Bowtie2, MetaPhlAn4, HUMAnN3, Kraken2, Bracken, metaSPAdes, MEGAHIT, Prokka

4. **Create the conda environment**:
   ```bash
   mamba env create -f assets/envs/<pipeline>.yaml
   # or, if mamba is unavailable:
   conda env create -f assets/envs/<pipeline>.yaml
   ```
   Prefer `mamba` over `conda` for significantly faster dependency resolution.

5. **Handle tools that cannot be installed via conda** — prompt the user with manual steps:
   - **Cell Ranger**: Download from the 10x Genomics website (requires registration). Add to PATH: `export PATH=/path/to/cellranger:$PATH`.
   - **CellBender**: Install via pip inside the conda environment: `pip install cellbender`. Requires CUDA for GPU acceleration.
   - **DoubletFinder**: Install from GitHub inside R: `remotes::install_github("chris-mcginnis-ucsf/DoubletFinder")`.
   - **Monocle3**: Install from Bioconductor: `BiocManager::install("monocle3")`. Alternatively: `remotes::install_github("cole-trapnell-lab/monocle3")`.
   - **velocyto** (for RNA velocity loom generation): `pip install velocyto`. Requires `samtools` and a reference GTF.

6. **Verify all installations**: After installation, re-run the version check for each tool. For R packages, run `Rscript -e 'packageVersion("<pkg>")'`. Report a final verification table: tool, expected version, installed version, status (PASS/FAIL).

7. **Report any failures** with the specific error message and the most likely fix (e.g., missing system library, incompatible CUDA version, wrong conda channel).

## Output Contract

- Environment detection summary (printed to console)
- Pre-installation version check table (TSV or formatted table): tool, status, version
- Installation commands executed (echo each command before running)
- Post-installation verification table (TSV or formatted table): tool, expected_min_version, installed_version, pass/fail
- List of any tools that require manual installation steps, with exact instructions

## Limits

- Cell Ranger requires registration and manual download from 10x Genomics; it cannot be distributed via conda or pip.
- CellBender GPU acceleration requires CUDA ≥ 11.0 and a compatible NVIDIA GPU; CPU-only mode is available but slow (hours per sample).
- Monocle3 has complex Bioconductor dependencies that frequently cause installation conflicts; allocate extra time and follow the official installation guide.
- Conda environments can be large (2–5 GB each); ensure sufficient disk space before creating them.
- On HPC clusters, use `module load` for pre-installed tools before attempting conda installation; conda may conflict with system modules.
- macOS (Apple Silicon) requires `CONDA_SUBDIR=osx-64` for some bioinformatics tools that lack native ARM builds.
- Common failure cases:
  - `conda solve` timing out on complex environments; switch to `mamba` for faster resolution.
  - GATK or Picard failing due to wrong Java version; ensure Java 17+ is available (`java --version`).
  - R package installation failing due to missing system libraries (e.g., `libgdal`, `libcurl`); install the system library first with `apt-get` or `yum`.
  - STARsolo requiring a STAR version ≥ 2.7.9a for Velocyto output; check STAR version with `STAR --version`.
