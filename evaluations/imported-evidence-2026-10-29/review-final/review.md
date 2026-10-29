# Imported evidence and comparison review

Independent review pending. No approvals have been recorded by this packet.

Review question relevance and comparison claims against the attributed sources. Check answerability, all relevant passages, values and units, negation, experimental unit, conditions, applicability, contradictions and limitations. Record decisions in a copy of responses.json; retain pending fields until an actual review occurs.

Packet revision: `38351b5c216098587eba7817969d8f9165a721d06e3a1d8b420e2a68b05e89cc`. Candidate: `2026-10-29-c1`.

JATS excerpt notes below have no verified PDF page anchor. Their selector, original XML fingerprint and exact source slice are retained in packet.json. PDF comparison passages have separately retained page/annotation identities.

## Review questions

### q01 How many library protocols, differential-expression setups, and approximate pipelines were evaluated by Vieth et al.?

Public split: development; draft answerable: True.

Agent draft answer: The abstract reports five library protocols, nine DE setups, and approximately 3000 pipelines.

Required qualifications: These are the counts stated in the abstract, not the total number of simulated datasets.

Draft relevance target [vieth2019.abstract](#passage-vieth2019abstract). [A systematic evaluation of single cell RNA-seq analysis pipelines](https://pmc.ncbi.nlm.nih.gov/articles/PMC6789098/); selector `abstract.p.1`.

### q02 How did increasing asymmetry of differential expression affect normalization estimates in the Vieth simulations?

Public split: development; draft answerable: True.

Agent draft answer: Size-factor deviations increased with asymmetry; scran and SCnorm performed better than the listed alternatives under those simulation conditions.

Required qualifications: Do not extend this simulation-specific comparison to every real single-cell dataset.

Draft relevance target [vieth2019.normalization](#passage-vieth2019normalization). [A systematic evaluation of single cell RNA-seq analysis pipelines](https://pmc.ncbi.nlm.nih.gov/articles/PMC6789098/); selector `body.p.13`.

### q03 What technical covariate and stabilization strategy does the original sctransform paper propose?

Public split: development; draft answerable: True.

Agent draft answer: Cellular sequencing depth is a covariate in regularized negative-binomial regression; information is pooled across genes of similar abundance to stabilize parameters.

Required qualifications: The abstract discusses UMI-based scRNA-seq and an unconstrained model that may overfit.

Draft relevance target [hafemeister2019.abstract](#passage-hafemeister2019abstract). [Normalization and variance stabilization of single-cell RNA-seq data using regularized negative binomial regression](https://pmc.ncbi.nlm.nih.gov/articles/PMC6927181/); selector `abstract.p.1`.

### q04 What exact false-discovery rate does the supplied sctransform excerpt guarantee for a new donor-level differential-expression study?

Public split: development; draft answerable: False.

Agent draft answer: The supplied excerpt states no such numerical guarantee; additional design-specific evidence is needed.

Required qualifications: Do not infer an FDR guarantee from a normalization-method abstract.

Draft reference says insufficient evidence. Review this explicitly; an empty target list is not an abstention score.

### q05 In the Townes negative controls, are UMI counts described as zero-inflated?

Public split: development; draft answerable: True.

Agent draft answer: No. The negative-control UMI counts are described as having no zero inflation, unlike the read-count representation affected by PCR duplicates.

Required qualifications: Restrict the statement to UMI counts and the studied negative controls; do not generalize to all read-count assays.

Draft relevance target [townes2019.abstract](#passage-townes2019abstract). [Feature selection and dimension reduction for single-cell RNA-Seq based on a multinomial model](https://pmc.ncbi.nlm.nih.gov/articles/PMC6927135/); selector `abstract.p.1`.

Draft relevance target [townes2019.umi-read](#passage-townes2019umi-read). [Feature selection and dimension reduction for single-cell RNA-Seq based on a multinomial model](https://pmc.ncbi.nlm.nih.gov/articles/PMC6927135/); selector `body.p.14`.

### q06 Which non-normal dimension-reduction and feature-selection methods do Townes et al. propose?

Public split: development; draft answerable: True.

Agent draft answer: They propose GLM-PCA for non-normal distributions and feature selection using deviance.

Required qualifications: The reported improvement concerns the evaluated clustering assessment.

Draft relevance target [townes2019.abstract](#passage-townes2019abstract). [Feature selection and dimension reduction for single-cell RNA-Seq based on a multinomial model](https://pmc.ncbi.nlm.nih.gov/articles/PMC6927135/); selector `abstract.p.1`.

### q07 Does the reported bias in low-expression overdispersion estimates necessarily substantially change the Pearson residuals?

Public split: development; draft answerable: True.

Agent draft answer: The authors state that this bias does not substantially affect Pearson residuals for low expression means because the predicted variance is only weakly affected by the exact overdispersion value.

Required qualifications: Do not equate biased parameter estimates with a demonstrated large residual error.

Draft relevance target [lause2021.caveat](#passage-lause2021caveat). [Analytic Pearson residuals for normalization of single-cell RNA-seq UMI data](https://pmc.ncbi.nlm.nih.gov/articles/PMC8419999/); selector `body.p.27`.

### q08 For the full 33k PBMC dataset, what runtimes does Table 1 report for Pearson-residuals PCA and GLM-PCA?

Public split: development; draft answerable: True.

Agent draft answer: Table 1 reports 35 seconds for Pearson residuals followed by PCA and 15 hours for GLM-PCA on the full 33k PBMC dataset.

Required qualifications: These are measured runtimes on the stated 256 Gb RAM, 30-thread, 2.1 GHz machine; do not mix with the 1000-HVG row.

Draft relevance target [lause2021.runtimes](#passage-lause2021runtimes). [Analytic Pearson residuals for normalization of single-cell RNA-seq UMI data](https://pmc.ncbi.nlm.nih.gov/articles/PMC8419999/); selector `table-wrap.1`.

### q09 What role does variation between biological replicates play in the false-discovery finding reported by Squair et al.?

Public split: development; draft answerable: True.

Agent draft answer: The abstract says relative method performance depends on accounting for variation between biological replicates; methods that ignore it are prone to false discoveries, including differences when no biological difference is present.

Required qualifications: This is the paper's reported benchmark finding, not proof that every use of every cell-level method is invalid.

Draft relevance target [squair2021.abstract](#passage-squair2021abstract). [Confronting false discoveries in single-cell differential expression](https://pmc.ncbi.nlm.nih.gov/articles/PMC8479118/); selector `abstract.p.1`.

### q10 How were the eighteen ground-standard datasets in Squair et al. selected?

Public split: development; draft answerable: True.

Agent draft answer: They used matched bulk and single-cell RNA-seq on the same purified cell population, with the same perturbations and laboratories; eighteen datasets met the criteria.

Required qualifications: Bulk agreement is their chosen approximation to ground truth, not universal clinical ground truth.

Draft relevance target [squair2021.benchmark](#passage-squair2021benchmark). [Confronting false discoveries in single-cell differential expression](https://pmc.ncbi.nlm.nih.gov/articles/PMC8479118/); selector `body.p.4`.

### q11 Why are cells from the same individual pseudoreplicates in the Zimmerman analysis?

Public split: development; draft answerable: True.

Agent draft answer: They share genetic and environmental backgrounds and are not statistically independent; the authors propose a generalized linear mixed model with a random effect for individual.

Required qualifications: Independent donors and cells within donors are different experimental units.

Draft relevance target [zimmerman2021.abstract](#passage-zimmerman2021abstract). [A practical solution to pseudoreplication bias in single-cell studies](https://pmc.ncbi.nlm.nih.gov/articles/PMC7854630/); selector `abstract.p.1`.

### q12 Do the Zimmerman and Squair excerpts justify saying that pseudobulk is universally better than mixed models?

Public split: development; draft answerable: True.

Agent draft answer: No. Zimmerman reports pseudobulk as conservative and underpowered relative to mixed models in their setup, whereas Squair emphasizes accounting for biological-replicate variation using different benchmark data; the supplied excerpts do not establish a universal ordering.

Required qualifications: Preserve the differing simulation and matched-data designs; do not manufacture a direct head-to-head comparison from unlike benchmarks.

Draft relevance target [zimmerman2021.abstract](#passage-zimmerman2021abstract). [A practical solution to pseudoreplication bias in single-cell studies](https://pmc.ncbi.nlm.nih.gov/articles/PMC7854630/); selector `abstract.p.1`.

Draft relevance target [squair2021.abstract](#passage-squair2021abstract). [Confronting false discoveries in single-cell differential expression](https://pmc.ncbi.nlm.nih.gov/articles/PMC8479118/); selector `abstract.p.1`.

Draft relevance target [squair2021.benchmark](#passage-squair2021benchmark). [Confronting false discoveries in single-cell differential expression](https://pmc.ncbi.nlm.nih.gov/articles/PMC8479118/); selector `body.p.4`.

### q13 What does muscat call differential-state analysis, and at what level is the inference intended?

Public split: development; draft answerable: True.

Agent draft answer: It concerns sample-level cross-condition inferences within subpopulations in replicated multi-condition scRNA-seq datasets.

Required qualifications: Differential-state analysis is not merely finding markers between cell types.

Draft relevance target [crowell2020.abstract](#passage-crowell2020abstract). [muscat detects subpopulation-specific state transitions from multi-sample multi-condition single-cell transcriptomics data](https://pmc.ncbi.nlm.nih.gov/articles/PMC7705760/); selector `abstract.p.1`.

### q14 In the muscat PBMC reference dataset, how many lupus patients were measured, after what treatment duration, and how many samples resulted?

Public split: development; draft answerable: True.

Agent draft answer: Eight lupus patients were measured before and after six hours of IFN-beta treatment, giving sixteen samples in total.

Required qualifications: Sixteen paired samples do not mean sixteen independent patients.

Draft relevance target [crowell2020.samples](#passage-crowell2020samples). [muscat detects subpopulation-specific state transitions from multi-sample multi-condition single-cell transcriptomics data](https://pmc.ncbi.nlm.nih.gov/articles/PMC7705760/); selector `body.p.12`.

### q15 How many method/preprocessing combinations and integration tasks were included in the atlas-integration abstract?

Public split: reserved; draft answerable: True.

Agent draft answer: The abstract reports 68 combinations and 13 integration tasks, spanning 85 batches from 23 publications and more than 1.2 million cells.

Required qualifications: Combinations, methods, tasks, batches, publications, and cells are distinct counts.

Draft relevance target [luecken2022.abstract](#passage-luecken2022abstract). [Benchmarking atlas-level data integration in single-cell genomics](https://pmc.ncbi.nlm.nih.gov/articles/PMC8748196/); selector `abstract.p.1`.

### q16 What were the pancreas task cell count and batch count in Table 1?

Public split: reserved; draft answerable: True.

Agent draft answer: The pancreas task has 16,382 cells and nine batches.

Required qualifications: Do not substitute the lung row's donor count or cell count.

Draft relevance target [luecken2022.tasks](#passage-luecken2022tasks). [Benchmarking atlas-level data integration in single-cell genomics](https://pmc.ncbi.nlm.nih.gov/articles/PMC8748196/); selector `table-wrap.1`.

### q17 What happens to DESeq/TMM size-factor estimates if the non-differential-expression assumption does not hold?

Public split: reserved; draft answerable: True.

Agent draft answer: The paper states that the computed factors will not be accurate; it describes non-DE proportions of 50% for DESeq and 40-70% for TMM depending on DE direction.

Required qualifications: The cited percentages and sparsity concerns are properties discussed for these normalization assumptions.

Draft relevance target [lun2016.assumptions](#passage-lun2016assumptions). [Pooling across cells to normalize single-cell RNA sequencing data with many zero counts](https://pmc.ncbi.nlm.nih.gov/articles/PMC4848819/); selector `body.p.10`.

### q18 What is pooled before deconvolution in the Lun normalization approach?

Public split: reserved; draft answerable: True.

Agent draft answer: Expression values are summed across pools of cells, normalized at pool level, and pool-based size factors are deconvolved into cell-based factors.

Required qualifications: This pooling is for normalization, not the biological-replicate pseudobulk DE comparison.

Draft relevance target [lun2016.abstract](#passage-lun2016abstract). [Pooling across cells to normalize single-cell RNA sequencing data with many zero counts](https://pmc.ncbi.nlm.nih.gov/articles/PMC4848819/); selector `abstract.p.1`.

### q19 What distribution underlies Splat, and which population structures can it simulate in the supplied abstract?

Public split: reserved; draft answerable: True.

Agent draft answer: Splat is based on a gamma-Poisson distribution and can simulate one cell population, multiple cell types, or differentiation paths.

Required qualifications: Describe the version documented in the 2017 article; do not assume the current package has identical capabilities.

Draft relevance target [zappia2017.abstract](#passage-zappia2017abstract). [Splatter: simulation of single-cell RNA sequencing data](https://pmc.ncbi.nlm.nih.gov/articles/PMC5596896/); selector `abstract.p.1`.

### q20 How many patients were randomized to a clinical disease-treatment trial in the provided Splatter excerpts?

Public split: reserved; draft answerable: False.

Agent draft answer: No clinical trial or randomized patient count is described in these simulation-method excerpts.

Required qualifications: Absence from the supplied excerpts does not prove that no related clinical trial exists anywhere.

Draft reference says insufficient evidence. Review this explicitly; an empty target list is not an abstention score.

## Complete excerpt set

Inspect every candidate when checking relevance, including passages absent from the draft target lists. The extra whitespace representation is retained in packet.json and earns no additional evidence credit.

### Passage vieth2019.abstract

[A systematic evaluation of single cell RNA-seq analysis pipelines](https://pmc.ncbi.nlm.nih.gov/articles/PMC6789098/); JATS selector `abstract.p.1`; transform `jats-itertext-whitespace-v1`.

Source slice [0, 1061); excerpt SHA-256 `f450c1463a1425a33ac84201f1776c5057733967ef49bd7c850b045a084b23ee`.

> The recent rapid spread of single cell RNA sequencing (scRNA-seq) methods has created a large variety of experimental and computational pipelines for which best practices have not yet been established. Here, we use simulations based on five scRNA-seq library protocols in combination with nine realistic differential expression (DE) setups to systematically evaluate three mapping, four imputation, seven normalisation and four differential expression testing approaches resulting in ~3000 pipelines, allowing us to also assess interactions among pipeline steps. We find that choices of normalisation and library preparation protocols have the biggest impact on scRNA-seq analyses. Specifically, we find that library preparation determines the ability to detect symmetric expression differences, while normalisation dominates pipeline performance in asymmetric DE-setups. Finally, we illustrate the importance of informed choices by showing that a good scRNA-seq pipeline can have the same impact on detecting a biological signal as quadrupling the sample size.

### Passage vieth2019.normalization

[A systematic evaluation of single cell RNA-seq analysis pipelines](https://pmc.ncbi.nlm.nih.gov/articles/PMC6789098/); JATS selector `body.p.13`; transform `jats-itertext-whitespace-v1`.

Source slice [0, 1052); excerpt SHA-256 `73f69a751ec7d19180b5c6f544e92236ff5e351fa03545fcfd53d16fe5a47034`.

> The next step in any RNA-seq analysis is the normalisation of the count matrix. The main idea here is that the resulting size factors correct for differing sequencing depths. In order to improve normalisation, spike-ins as an added standard can help, but are not feasible for all scRNA-seq library preparations. Another avenue to improve normalisation would be to deal with sparsity by imputing missing data prior to normalisation as discussed in the next chapter (Fig. 1c). To begin with, we compare how much the estimated size factors deviate from the truth. As long as there is only a small proportion of DE-genes or if the differences are symmetric, estimated size factors are not too far from the simulated ones and there are no large differences among methods (Fig. 3a and Supplementary Figs. 10 and 11). However with increasing asymmetry, size factors deviate more and more and the single cell methods scran25 and SCnorm26 perform markedly better than the bulk methods TMM27, MR28 and Positive Counts as well as the single cell method Linnorm29.

### Passage hafemeister2019.abstract

[Normalization and variance stabilization of single-cell RNA-seq data using regularized negative binomial regression](https://pmc.ncbi.nlm.nih.gov/articles/PMC6927181/); JATS selector `abstract.p.1`; transform `jats-itertext-whitespace-v1`.

Source slice [0, 1319); excerpt SHA-256 `351e4542717b5cc869e7c839bf7b80940de38bbea86adaa9ee89fc2effbfe87c`.

> Single-cell RNA-seq (scRNA-seq) data exhibits significant cell-to-cell variation due to technical factors, including the number of molecules detected in each cell, which can confound biological heterogeneity with technical effects. To address this, we present a modeling framework for the normalization and variance stabilization of molecular count data from scRNA-seq experiments. We propose that the Pearson residuals from “regularized negative binomial regression,” where cellular sequencing depth is utilized as a covariate in a generalized linear model, successfully remove the influence of technical characteristics from downstream analyses while preserving biological heterogeneity. Importantly, we show that an unconstrained negative binomial model may overfit scRNA-seq data, and overcome this by pooling information across genes with similar abundances to obtain stable parameter estimates. Our procedure omits the need for heuristic steps including pseudocount addition or log-transformation and improves common downstream analytical tasks such as variable gene selection, dimensional reduction, and differential expression. Our approach can be applied to any UMI-based scRNA-seq dataset and is freely available as part of the R package sctransform, with a direct interface to our single-cell toolkit Seurat.

### Passage hafemeister2019.depth

[Normalization and variance stabilization of single-cell RNA-seq data using regularized negative binomial regression](https://pmc.ncbi.nlm.nih.gov/articles/PMC6927181/); JATS selector `body.p.3`; transform `jats-itertext-whitespace-v1`.

Source slice [0, 262); excerpt SHA-256 `8bb2be17673b2b0281ab8ef0933429510a196fb96f86a6190c817cea311fe1ab`.

> In general, the normalized expression level of a gene should not be correlated with the total sequencing depth of a cell. Downstream analytical tasks (dimensional reduction, differential expression) should also not be influenced by variation in sequencing depth.

### Passage townes2019.abstract

[Feature selection and dimension reduction for single-cell RNA-Seq based on a multinomial model](https://pmc.ncbi.nlm.nih.gov/articles/PMC6927135/); JATS selector `abstract.p.1`; transform `jats-itertext-whitespace-v1`.

Source slice [0, 699); excerpt SHA-256 `df00edc2833a94e9e5282e027999ed5c01906608f56f1be1a413b51dc29a6706`.

> Single-cell RNA-Seq (scRNA-Seq) profiles gene expression of individual cells. Recent scRNA-Seq datasets have incorporated unique molecular identifiers (UMIs). Using negative controls, we show UMI counts follow multinomial sampling with no zero inflation. Current normalization procedures such as log of counts per million and feature selection by highly variable genes produce false variability in dimension reduction. We propose simple multinomial methods, including generalized principal component analysis (GLM-PCA) for non-normal distributions, and feature selection using deviance. These methods outperform the current practice in a downstream clustering assessment using ground truth datasets.

### Passage townes2019.umi-read

[Feature selection and dimension reduction for single-cell RNA-Seq based on a multinomial model](https://pmc.ncbi.nlm.nih.gov/articles/PMC6927135/); JATS selector `body.p.14`; transform `jats-itertext-whitespace-v1`.

Source slice [0, 636); excerpt SHA-256 `3447e036a97a136662706047a2e6c4a8c2fc9db729c15dd92628f4fb483907c8`.

> To illustrate the marked difference between UMI count distributions and read count distributions, we created histograms from individual genes and spike-ins of the negative control data. Here, the UMI counts are the computationally de-duplicated versions of the read counts; both measurements are from the same experiment, so no differences are due to technical or biological variation. The results suggest that while read counts appear zero-inflated and multimodal, UMI counts follow a discrete distribution with no zero inflation (Additional file 1: Figure S1). The apparent zero inflation in read counts is a result of PCR duplicates.

### Passage lause2021.model

[Analytic Pearson residuals for normalization of single-cell RNA-seq UMI data](https://pmc.ncbi.nlm.nih.gov/articles/PMC8419999/); JATS selector `abstract.p.2`; transform `jats-itertext-whitespace-v1`.

Source slice [0, 958); excerpt SHA-256 `dcab45dc82be2c01fb59a1ffe1dc33e02d0ec49daf84bbedcf75bcf29521ec19`.

> We show that the model of Hafemeister and Satija produces noisy parameter estimates because it is overspecified, which is why the original paper employs post hoc smoothing. When specified more parsimoniously, it has a simple analytic solution equivalent to the rank-one Poisson GLM-PCA of Townes et al. Further, our analysis indicates that per-gene overdispersion estimates in Hafemeister and Satija are biased, and that the data are in fact consistent with the overdispersion parameter being independent of gene expression. We then use negative control data without biological variability to estimate the technical overdispersion of UMI counts, and find that across several different experimental protocols, the data are close to Poisson and suggest very moderate overdispersion. Finally, we perform a benchmark to compare the performance of Pearson residuals, variance-stabilizing transformations, and GLM-PCA on scRNA-seq datasets with known ground truth.

### Passage lause2021.caveat

[Analytic Pearson residuals for normalization of single-cell RNA-seq UMI data](https://pmc.ncbi.nlm.nih.gov/articles/PMC8419999/); JATS selector `body.p.27`; transform `jats-itertext-whitespace-v1`.

Source slice [0, 373); excerpt SHA-256 `b559d24f6fd40ebeb5bbf4e12918d82298cfd3a5166fd2c1f1401dc3a1a1c7b9`.

> The above arguments show that the overdispersion parameter estimates in Hafemeister and Satija [3] for genes with low expression were strongly biased. In practice, however, the predicted variance μ+μ2/θ is only weakly affected by the exact value of θ for low expression means μ, and so the bias reported here does not substantially affect the Pearson residuals (see below).

### Passage lause2021.runtimes

[Analytic Pearson residuals for normalization of single-cell RNA-seq UMI data](https://pmc.ncbi.nlm.nih.gov/articles/PMC8419999/); JATS selector `table-wrap.1`; transform `jats-simple-table-tsv-v1`.

Exact tab-separated table excerpt; headers, row boundaries, units and footnotes are retained:

```text
Table 1: Runtimes for different normalization pipelines
	Sqrt(CPMedian), PCA	Pearson residuals, PCA	GLM-PCA
33k PBMC	31 s	35 s	15 h
33k PBMC, 1000 HVGs	3 s	4 s	4 h
2M organogenesis, 2000 HVGs	166 s	224 s	52 h
The datasets are the full 33k PBMC dataset, the PBMC dataset after selecting 1, 000 HVGs, and the organogenesis dataset [39] after selecting 2, 000 HVGs. Genes with largest Pearson residual variances were selected, which took 9 s (PBMC) and 15 min (organogenesis), respectively. See “Methods” for details. All runtimes measured on a machine with 256 Gb RAM and 30 CPU threads at 2.1 GHz
```

### Passage squair2021.abstract

[Confronting false discoveries in single-cell differential expression](https://pmc.ncbi.nlm.nih.gov/articles/PMC8479118/); JATS selector `abstract.p.1`; transform `jats-itertext-whitespace-v1`.

Source slice [0, 873); excerpt SHA-256 `1e0640e85d33f937bbf6fbd8a9a347573e1e463abab74a6b77a3c5897a4f6c7c`.

> Differential expression analysis in single-cell transcriptomics enables the dissection of cell-type-specific responses to perturbations such as disease, trauma, or experimental manipulations. While many statistical methods are available to identify differentially expressed genes, the principles that distinguish these methods and their performance remain unclear. Here, we show that the relative performance of these methods is contingent on their ability to account for variation between biological replicates. Methods that ignore this inevitable variation are biased and prone to false discoveries. Indeed, the most widely used methods can discover hundreds of differentially expressed genes in the absence of biological differences. To exemplify these principles, we exposed true and false discoveries of differentially expressed genes in the injured mouse spinal cord.

### Passage squair2021.benchmark

[Confronting false discoveries in single-cell differential expression](https://pmc.ncbi.nlm.nih.gov/articles/PMC8479118/); JATS selector `body.p.4`; transform `jats-itertext-whitespace-v1`.

Source slice [0, 908); excerpt SHA-256 `78474a8bcfafc474d62fd19070675de8ced20ad678b4fc5283079596036f9540`.

> We aimed to compare available statistical methods for differential expression (DE) analysis based on their ability to generate biologically accurate results. We reasoned that performing this comparison in real datasets where the experimental ground truth is known would faithfully reflect differences in the performance of these methods, while avoiding the shortcomings of simulated data. We posited that the closest possible approximation to this ground truth could be obtained from matched bulk and scRNA-seq performed on the same population of purified cells, exposed to the same perturbations, and sequenced in the same laboratories. An extensive survey of the literature identified a total of eighteen ‘gold standard’ datasets that met these criteria (Fig. 1a)12–15. This compendium allowed us to carry out a large-scale comparison of DE methods in experimental settings where the ground truth is known.

### Passage zimmerman2021.abstract

[A practical solution to pseudoreplication bias in single-cell studies](https://pmc.ncbi.nlm.nih.gov/articles/PMC7854630/); JATS selector `abstract.p.1`; transform `jats-itertext-whitespace-v1`.

Source slice [0, 1128); excerpt SHA-256 `272de9b81ffe4754d24caf0de97006a67caee14a485873321d4da40e180b4cb4`.

> Cells from the same individual share common genetic and environmental backgrounds and are not statistically independent; therefore, they are subsamples or pseudoreplicates. Thus, single-cell data have a hierarchical structure that many current single-cell methods do not address, leading to biased inference, highly inflated type 1 error rates, and reduced robustness and reproducibility. This includes methods that use a batch effect correction for individual as a means of accounting for within-sample correlation. Here, we document this dependence across a range of cell types and show that pseudo-bulk aggregation methods are conservative and underpowered relative to mixed models. To compute differential expression within a specific cell type across treatment groups, we propose applying generalized linear mixed models with a random effect for individual, to properly account for both zero inflation and the correlation structure among measures from cells within an individual. Finally, we provide power estimates across a range of experimental conditions to assist researchers in designing appropriately powered studies.

### Passage zimmerman2021.type1-caption

[A practical solution to pseudoreplication bias in single-cell studies](https://pmc.ncbi.nlm.nih.gov/articles/PMC7854630/); JATS selector `body.p.9`; transform `jats-itertext-whitespace-v1`.

Source slice [0, 873); excerpt SHA-256 `e1e2fac6be12139aa07e3e22aa36c3b5a4c882f7607a18f652b38c3ce5c4fe43`.

> Type I error rates of some currently applied tools in single-cell analyses. Type I error rates of ten different methods under twenty different conditions and a significance threshold of p &lt; 0.05. In all, 250,000 iterations were computed to obtain an error rate for each method. The inflated type I error rates computed with mixed models at the lower number of individuals per group are a consequence of the two-part hurdle model simultaneously testing two hypotheses and an overabundance of subsampling with small sample sizes. Type I error rates are well-controlled for with mixed models and pseudo-bulk methods, while type I error rates increase with other methods as additional independent samples or more cells are added. Pseudo-bulk methods are overly conservative. Confidence intervals (95%) are included in the enlarged version of this table (Supplementary Table 1).

### Passage crowell2020.abstract

[muscat detects subpopulation-specific state transitions from multi-sample multi-condition single-cell transcriptomics data](https://pmc.ncbi.nlm.nih.gov/articles/PMC7705760/); JATS selector `abstract.p.1`; transform `jats-itertext-whitespace-v1`.

Source slice [0, 1142); excerpt SHA-256 `2a19846dbdf08013ea82fe8cdf09cbee421c1100807b1a69c0a010d6836d3ca9`.

> Single-cell RNA sequencing (scRNA-seq) has become an empowering technology to profile the transcriptomes of individual cells on a large scale. Early analyses of differential expression have aimed at identifying differences between subpopulations to identify subpopulation markers. More generally, such methods compare expression levels across sets of cells, thus leading to cross-condition analyses. Given the emergence of replicated multi-condition scRNA-seq datasets, an area of increasing focus is making sample-level inferences, termed here as differential state analysis; however, it is not clear which statistical framework best handles this situation. Here, we surveyed methods to perform cross-condition differential state analyses, including cell-level mixed models and methods based on aggregated pseudobulk data. To evaluate method performance, we developed a flexible simulation that mimics multi-sample scRNA-seq data. We analyzed scRNA-seq data from mouse cortex cells to uncover subpopulation-specific responses to lipopolysaccharide treatment, and provide robust tools for multi-condition analysis within the muscat R package.

### Passage crowell2020.samples

[muscat detects subpopulation-specific state transitions from multi-sample multi-condition single-cell transcriptomics data](https://pmc.ncbi.nlm.nih.gov/articles/PMC7705760/); JATS selector `body.p.12`; transform `jats-itertext-whitespace-v1`.

Source slice [0, 390); excerpt SHA-256 `3b08364862ca738ea79f250c710e4ef0370f7629a9f579152da7abe0367adaf2`.

> As reference datasets, we used (i) scRNA-seq data of peripheral blood mononuclear cells (PBMCs) from eight lupus patients measured before and after 6 h-treatment with IFN-β (16 samples in total)20, where cells were already annotated into various immune subpopulations; and, (ii) single-nuclei RNA-seq data of brain cortex tissue from eight mice split into a vehicle and LPS treatment group.

### Passage crowell2020.cell-count

[muscat detects subpopulation-specific state transitions from multi-sample multi-condition single-cell transcriptomics data](https://pmc.ncbi.nlm.nih.gov/articles/PMC7705760/); JATS selector `body.p.23`; transform `jats-itertext-whitespace-v1`.

Source slice [0, 638); excerpt SHA-256 `331ec48df344bd9130607f6354515a363d224827dee27d26b91aead5a81df198`.

> To investigate the effect of subpopulation size on DS detection, we ran methods on simulations containing 10% of DE genes using subsets of 20–400 cells per subpopulation-sample (Fig. 2b). For most methods, FDR control varies drastically with the number of cells, while TPRs improve for more cells across all methods. For aggregation-based methods, ~100 cells were sufficient to reach decent performance; in particular, there is a sizable gain in performance in going from 20 to 100 cells (per subpopulation per sample), but only a moderate gain in a deeper sampling of subpopulations (e.g., 200 or 400 cells per subpopulation per sample).

### Passage luecken2022.abstract

[Benchmarking atlas-level data integration in single-cell genomics](https://pmc.ncbi.nlm.nih.gov/articles/PMC8748196/); JATS selector `abstract.p.1`; transform `jats-itertext-whitespace-v1`.

Source slice [0, 1247); excerpt SHA-256 `6df02cd8f46727ef378f34e57160dbb94d76a74e9489d18a502505c5814a7bfe`.

> Single-cell atlases often include samples that span locations, laboratories and conditions, leading to complex, nested batch effects in data. Thus, joint analysis of atlas datasets requires reliable data integration. To guide integration method choice, we benchmarked 68 method and preprocessing combinations on 85 batches of gene expression, chromatin accessibility and simulation data from 23 publications, altogether representing &gt;1.2 million cells distributed in 13 atlas-level integration tasks. We evaluated methods according to scalability, usability and their ability to remove batch effects while retaining biological variation using 14 evaluation metrics. We show that highly variable gene selection improves the performance of data integration methods, whereas scaling pushes methods to prioritize batch removal over conservation of biological variation. Overall, scANVI, Scanorama, scVI and scGen perform well, particularly on complex integration tasks, while single-cell ATAC-sequencing integration performance is strongly affected by choice of feature space. Our freely available Python module and benchmarking pipeline can identify optimal data integration methods for new data, benchmark new methods and improve method development.

### Passage luecken2022.tradeoff

[Benchmarking atlas-level data integration in single-cell genomics](https://pmc.ncbi.nlm.nih.gov/articles/PMC8748196/); JATS selector `body.p.18`; transform `jats-itertext-whitespace-v1`.

Source slice [0, 567); excerpt SHA-256 `5b0a067b5e0ef96a1461fcec2bd086ed49dffb49b5440d25f7cf0141bd132f6d`.

> Particularly in more complex integration tasks, we observed a tradeoff between batch effect removal and bio-conservation (Fig. 3a and Supplementary Data 1). While methods such as SAUCIE, LIGER, BBKNN and Seurat v3 tend to favor the removal of batch effects over conservation of biological variation, DESC and Conos make the opposite choice, and Scanorama, scVI and FastMNN (gene) balance these two objectives. Other methods strike different balances per task (Extended Data Fig. 4). This tradeoff is particularly noticeable where biological and batch effects overlap.

### Passage luecken2022.tasks

[Benchmarking atlas-level data integration in single-cell genomics](https://pmc.ncbi.nlm.nih.gov/articles/PMC8748196/); JATS selector `table-wrap.1`; transform `jats-simple-table-tsv-v1`.

Exact tab-separated table excerpt; headers, row boundaries, units and footnotes are retained:

```text
Table 1: Integration tasks for benchmarking
Integration task	Cell number	Batches	Tested features
Pancreas	16,382	9 batches	Widely used test data, protocols
Lung	32,472	16 donors	Human variation, protocols, spatial locations, high resolution subtypes, laboratories
Immune (human)	33,506	10 donors	Tissues, laboratories, similar cell types
Immune (human and mouse)	97,952	23 samples	Tissues, laboratories, similar cell types, species
Mouse brain (RNA)	978,734	4 datasets	Large dataset, spatial locations, nucleus versus cell, protocols
Mouse brain small (ATAC, 3 tasks: windows, peaks, gene activity)	10,761, 11,597, 11,270	3 datasets	Different modality, laboratories, technologies and feature spaces
Mouse brain large (ATAC, 3 tasks: windows, peaks gene activity)	84,813	11 samples	Different samples from 3 unbalanced datasets; different modality, laboratories, technologies and feature spaces
Simulation 1	12,097	6 batches	Variation in cellular compositions
Simulation 2	19,318	16 batches	Nested batch effects, composition variation
Overview of the tasks used to benchmark data integration methods. The tested feature describes the unique challenge presented by the integration task. Donor refers to human individuals, sample is used when mice are involved and batches is the general term that includes dataset and sample batches. The six ATAC tasks are summarized in two entries.
```

### Passage lun2016.abstract

[Pooling across cells to normalize single-cell RNA sequencing data with many zero counts](https://pmc.ncbi.nlm.nih.gov/articles/PMC4848819/); JATS selector `abstract.p.1`; transform `jats-itertext-whitespace-v1`.

Source slice [0, 674); excerpt SHA-256 `0b3c5453213701ca1f9410848543747a5fea4af622273f137172494ebc053aa0`.

> Normalization of single-cell RNA sequencing data is necessary to eliminate cell-specific biases prior to downstream analyses. However, this is not straightforward for noisy single-cell data where many counts are zero. We present a novel approach where expression values are summed across pools of cells, and the summed values are used for normalization. Pool-based size factors are then deconvolved to yield cell-based factors. Our deconvolution approach outperforms existing methods for accurate normalization of cell-specific biases in simulated data. Similar behavior is observed in real data, where deconvolution improves the relevance of results of downstream analyses.

### Passage lun2016.assumptions

[Pooling across cells to normalize single-cell RNA sequencing data with many zero counts](https://pmc.ncbi.nlm.nih.gov/articles/PMC4848819/); JATS selector `body.p.10`; transform `jats-itertext-whitespace-v1`.

Source slice [0, 1205); excerpt SHA-256 `5579b423263ad5982f0fb8a4ad43eaaff52d2a4dbde39b607ff9e2b9cfb31531`.

> Both DESeq and TMM normalization assume that some minimal proportion of genes are not DE between libraries. For DESeq, the proportion is 50 % of all genes, whereas for TMM, it is 40–70 % depending on the direction of DE [4] (for simplicity, this will be referred to as a non-DE majority for both methods). Consequently, any systematic difference in expression across the majority of genes is treated as bias, which is incorporated into the size/normalization factors and removed upon scaling. If the non-DE assumption does not hold, the computed factors will not be accurate. In addition, both methods perform poorly in the presence of a large number of zeroes. For DESeq normalization, the geometric mean will be equal to zero for genes with a zero count in any library, such that the ratios for that gene become undefined. Moreover, a library with zero counts for a majority of genes will have a size factor of zero, which precludes any sensible scaling. For TMM normalization, M values are undefined when the count in either library is zero. In such conditions, both methods require ad hoc workarounds such as the removal of zero counts (this is done automatically by their respective implementations).

### Passage zappia2017.abstract

[Splatter: simulation of single-cell RNA sequencing data](https://pmc.ncbi.nlm.nih.gov/articles/PMC5596896/); JATS selector `abstract.p.1`; transform `jats-itertext-whitespace-v1`.

Source slice [0, 717); excerpt SHA-256 `34a2aea1f5b5688799a6a9d41d4bf0c09a53fc17f0e1ddb8595721aa0a12c7fd`.

> As single-cell RNA sequencing (scRNA-seq) technologies have rapidly developed, so have analysis methods. Many methods have been tested, developed, and validated using simulated datasets. Unfortunately, current simulations are often poorly documented, their similarity to real data is not demonstrated, or reproducible code is not available. Here, we present the Splatter Bioconductor package for simple, reproducible, and well-documented simulation of scRNA-seq data. Splatter provides an interface to multiple simulation methods including Splat, our own simulation, based on a gamma-Poisson distribution. Splat can simulate single populations of cells, populations with multiple cell types, or differentiation paths.

### Passage zappia2017.models

[Splatter: simulation of single-cell RNA sequencing data](https://pmc.ncbi.nlm.nih.gov/articles/PMC5596896/); JATS selector `body.p.8`; transform `jats-itertext-whitespace-v1`.

Source slice [0, 336); excerpt SHA-256 `d2131896135fc7b592e5ed5aaeb183849b09c2a6f1868223cfacee4f84cfa346`.

> Currently, Splatter implements six different simulation models, each with their own assumptions but accessed through a consistent, easy-to-use interface. These simulations are described in more detail in the following sections and in the documentation for each simulation in Splatter, which also describes the required input parameters.

## Comparison review

Replication and method choice: three-paper pilot. Comparison revision `5f611a44b3efb664273c2eba279898bf53bb266ccfadc5846afef8c3354c85eb`.

### A practical solution to pseudoreplication bias in single-cell studies — Experimental unit and benchmark

Origin: agent; current review: unreviewed; cell revision `db3001ecc1b53e5b3d65c343006132f2962e1d3eb8745d349693c488a797f858`.

Interpretation: Cells from one individual are correlated subsamples. The study evaluates type 1 error using simulated inter- and intra-individual variance estimated from real data.

Conditions: Within-cell-type comparisons across individuals; a simulation-based reference standard. Do not equate cell count with independent sample count.

Evidence `n_000001` revision `7651874856dcac7755bf882f4750c50013ea5253f6e53447c2afcb1f8c647a0d`; imported review `unreviewed`.

> PDF page 1: Cells from the same individual share common genetic and environmental backgrounds and are not statistically independent; therefore, they are subsamples or pseudoreplicates.

[Publisher PDF page](https://www.nature.com/articles/s41467-021-21038-1.pdf#page=1) · [Article](https://doi.org/10.1038/s41467-021-21038-1)

[Exact retained reader passage](http://127.0.0.1:52718/?session_id=ps_ae9ad0ab957c&document_sha256=464b4845a2b4d02fb3f2cd23b61f0bc9bd2287fc6ad2114baf7d64919006501c&annotation_id=ann_0d83fce29c0040bfb815a7020606f29c&page=1&passage_sha256=3748f779f2ccfb20995406a9c704ad7120e875c042041ba5f160f83e67d690a0) (requires original local reader).

Evidence `n_000002` revision `70a1109dd986f52d3fde93475a0ac39a5a088c7258120f1934c80bd6456f222a`; imported review `unreviewed`.

> PDF page 3: We completed a simulation study that reproduced both the inter- and intra-individual variance structures estimated from real data and documented the effect of intra-individual correlation on the type 1 error rates of the most frequently used single-cell analysis tools

[Publisher PDF page](https://www.nature.com/articles/s41467-021-21038-1.pdf#page=3) · [Article](https://doi.org/10.1038/s41467-021-21038-1)

[Exact retained reader passage](http://127.0.0.1:52718/?session_id=ps_ae9ad0ab957c&document_sha256=464b4845a2b4d02fb3f2cd23b61f0bc9bd2287fc6ad2114baf7d64919006501c&annotation_id=ann_49d83e2344b544f98f72672408b7d9f1&page=3&passage_sha256=040df3f91b17a05237ddd92ba1c9220da3dd4d51f357ad14dd20310ea241bb62) (requires original local reader).

### A practical solution to pseudoreplication bias in single-cell studies — Method finding and limits

Origin: agent; current review: unreviewed; cell revision `01a0ec8786b02ca2690b5cf32321534dd7c41c72753666db59375fe597063d66`.

Interpretation: The authors report a power advantage for mixed-effects models over pseudo-bulk aggregation in their simulation-based study. Their discussion particularly emphasizes heavy imbalance and within-subject variability large relative to between-subject variability. This conditional finding does not directly overturn rankings from the other papers' different benchmarks.

Conditions: Within-cell-type comparisons across individuals; simulations of inter- and intra-individual variance. The additional page-6 passage qualifies the initial abstract-level interpretation. Unequal cells per individual and the within-/between-individual variance ratio matter; this entry does not establish a universal winner.

Evidence `n_000002` revision `70a1109dd986f52d3fde93475a0ac39a5a088c7258120f1934c80bd6456f222a`; imported review `unreviewed`.

> PDF page 3: We completed a simulation study that reproduced both the inter- and intra-individual variance structures estimated from real data and documented the effect of intra-individual correlation on the type 1 error rates of the most frequently used single-cell analysis tools

[Publisher PDF page](https://www.nature.com/articles/s41467-021-21038-1.pdf#page=3) · [Article](https://doi.org/10.1038/s41467-021-21038-1)

[Exact retained reader passage](http://127.0.0.1:52718/?session_id=ps_ae9ad0ab957c&document_sha256=464b4845a2b4d02fb3f2cd23b61f0bc9bd2287fc6ad2114baf7d64919006501c&annotation_id=ann_49d83e2344b544f98f72672408b7d9f1&page=3&passage_sha256=040df3f91b17a05237ddd92ba1c9220da3dd4d51f357ad14dd20310ea241bb62) (requires original local reader).

Evidence `n_000003` revision `1d6ccce0945f2d1fcdda4be9448363b8cf62f6fdbbb27ba4e2637a99b44b9141`; imported review `unreviewed`.

> PDF page 1: Here, we document this dependence across a range of cell types and show that pseudo-bulk aggregation methods are conservative and underpowered relative to mixed models.

[Publisher PDF page](https://www.nature.com/articles/s41467-021-21038-1.pdf#page=1) · [Article](https://doi.org/10.1038/s41467-021-21038-1)

[Exact retained reader passage](http://127.0.0.1:52718/?session_id=ps_ae9ad0ab957c&document_sha256=464b4845a2b4d02fb3f2cd23b61f0bc9bd2287fc6ad2114baf7d64919006501c&annotation_id=ann_78eb2e3024fd4af78c99787f9d9a376f&page=1&passage_sha256=f2d34f1880caded98da13085a2d08dae58360aaa445946cd888dcd9a554a7db2) (requires original local reader).

Evidence `n_000010` revision `efcd6d363a3d0c5fd6914f3f8d51410b6230028332dfd65767921c744bada597`; imported review `unreviewed`.

> PDF page 6: we recommend mixed-effects models based on long-standing statistical justi fications for the analysis of subsamples, including increased power. This is parti- cularly so in scenarios with heavy imbalance and where within- subject variability is large compared to between-subject variability.

[Publisher PDF page](https://www.nature.com/articles/s41467-021-21038-1.pdf#page=6) · [Article](https://doi.org/10.1038/s41467-021-21038-1)

[Exact retained reader passage](http://127.0.0.1:52718/?session_id=ps_ae9ad0ab957c&document_sha256=464b4845a2b4d02fb3f2cd23b61f0bc9bd2287fc6ad2114baf7d64919006501c&annotation_id=ann_7b26d020dd72401a9984ae83adf5a771&page=6&passage_sha256=48c93395c672d33c31ba33ea92f7d73df9a5744193decfea2486034cc0c0f2c8) (requires original local reader).

### Confronting false discoveries in single-cell differential expression — Experimental unit and benchmark

Origin: agent; current review: unreviewed; cell revision `7bd9434441cdfdfb1aaf4dc0c464211d12de7fe030d37c65641e3e76643b5549`.

Interpretation: Performance depends on accounting for between-replicate variation. The reported main benchmark compares 14 methods across 18 reference datasets, using concordance between matched bulk and single-cell DE results.

Conditions: Matched populations and perturbations are the reference; the concordance metric differs from simulated power and type 1 error. Eighteen reference datasets are distinct from the separate 46-dataset compendium.

Evidence `n_000004` revision `1bb7b716aa5b07d4593e88cca13ee058e0f9b37e2d8338f7d2dbe20031e6c15b`; imported review `unreviewed`.

> PDF page 2: We compared the performance of the fourteen methods across the entire compendium of the eighteen gold standard datasets. This analysis immediately revealed that all six of the top- performing methods shared a common analytical property. These methods aggregated cells within a biological replicate, to form so- called ‘pseudobulks’, before applying a statistical test

[Publisher PDF page](https://www.nature.com/articles/s41467-021-25960-2.pdf#page=2) · [Article](https://doi.org/10.1038/s41467-021-25960-2)

[Exact retained reader passage](http://127.0.0.1:52718/?session_id=ps_7202764ea4f7&document_sha256=465fd1842f2e07e17d55e0170dd96dd994f61a15c019655f3f1503ef37e7f22a&annotation_id=ann_1e93180167bc48d8a75a544c70dfe30c&page=2&passage_sha256=67dd8ca224923c48217178d8690e7a66a75f42aca382aa8d05842876f86ead3a) (requires original local reader).

Evidence `n_000005` revision `947a444f73a046e31a9fcbf3f133a86fad23e39e0da4e742f9bb8576236fa82e`; imported review `unreviewed`.

> PDF page 1: Here, we show that the relative performance of these methods is contingent on their ability to account for variation between biological replicates.

[Publisher PDF page](https://www.nature.com/articles/s41467-021-25960-2.pdf#page=1) · [Article](https://doi.org/10.1038/s41467-021-25960-2)

[Exact retained reader passage](http://127.0.0.1:52718/?session_id=ps_7202764ea4f7&document_sha256=465fd1842f2e07e17d55e0170dd96dd994f61a15c019655f3f1503ef37e7f22a&annotation_id=ann_375c8ad9db2b4023bcd9ddf35a786503&page=1&passage_sha256=958f08a6a0b74b3a47f4ca76267ce6dde6da190a9fc480baadff691fa155f4b6) (requires original local reader).

### Confronting false discoveries in single-cell differential expression — Method finding and limits

Origin: agent; current review: unreviewed; cell revision `c7bcf3d7c0a44544606c59de5d0a59a001e0b1eb4f8e27dc83b9cfc9ea070e8d`.

Interpretation: All six leading methods in the main benchmark aggregate cells within biological replicates. A follow-up GLMM analysis also reports accurate results for specific settings and convergence to pseudobulk performance at 500 or more cells, qualifying a blanket claim that mixed models always perform worse.

Conditions: Main 14-method/18-dataset benchmark and separate follow-up GLMM experiments. The reported 25-50 and 500-or-more cell settings are benchmark conditions, not universal design thresholds.

Evidence `n_000004` revision `1bb7b716aa5b07d4593e88cca13ee058e0f9b37e2d8338f7d2dbe20031e6c15b`; imported review `unreviewed`.

> PDF page 2: We compared the performance of the fourteen methods across the entire compendium of the eighteen gold standard datasets. This analysis immediately revealed that all six of the top- performing methods shared a common analytical property. These methods aggregated cells within a biological replicate, to form so- called ‘pseudobulks’, before applying a statistical test

[Publisher PDF page](https://www.nature.com/articles/s41467-021-25960-2.pdf#page=2) · [Article](https://doi.org/10.1038/s41467-021-25960-2)

[Exact retained reader passage](http://127.0.0.1:52718/?session_id=ps_7202764ea4f7&document_sha256=465fd1842f2e07e17d55e0170dd96dd994f61a15c019655f3f1503ef37e7f22a&annotation_id=ann_1e93180167bc48d8a75a544c70dfe30c&page=2&passage_sha256=67dd8ca224923c48217178d8690e7a66a75f42aca382aa8d05842876f86ead3a) (requires original local reader).

Evidence `n_000006` revision `6e750e8c728598e06ac3beaa394d9563cef54f160568797c9867e236f7003baf`; imported review `unreviewed`.

> PDF page 8: In datasets of 25-50 cells, GLMMs could produce accurate results under very speci fic parameter combinations. However, in datasets comprising 500 or more cells, their performance converged to that of pseudobulk DE methods.

[Publisher PDF page](https://www.nature.com/articles/s41467-021-25960-2.pdf#page=8) · [Article](https://doi.org/10.1038/s41467-021-25960-2)

[Exact retained reader passage](http://127.0.0.1:52718/?session_id=ps_7202764ea4f7&document_sha256=465fd1842f2e07e17d55e0170dd96dd994f61a15c019655f3f1503ef37e7f22a&annotation_id=ann_93937e845099455a808315f0c117321a&page=8&passage_sha256=cdb7a64bfa300eb9bb0d6460e8a19fd70a63c95505af0a9a0e6b89da12874e39) (requires original local reader).

### muscat detects subpopulation-specific state transitions from multi-sample multi-condition single-cell transcriptomics data — Experimental unit and benchmark

Origin: agent; current review: unreviewed; cell revision `aa5e63452a885c6b47f79cba96645ceb17ca68ccb12c70ce66f130a27101f52f`.

Interpretation: The framework retains sample labels within cell subpopulations for replicated condition comparisons. Its main simulation targets an average 200 cells per subpopulation-sample, about 3,600 cells overall, and five repeats per scenario.

Conditions: Multi-sample differential-state simulation; cells per sample and simulation repetitions are different quantities. Reference data and simulation design differ from the other two papers.

Evidence `n_000008` revision `eca1f65b8fb9ecfc58f72ec23ae4755a949c196a9674dfa2f6697b927957ffca`; imported review `unreviewed`.

> PDF page 3: To ensure that method performances are comparable and do not suffer from low cell numbers, we simulated an average of 200 cells per subpopulation-sample instance, amounting to a total of ~200 × (S1 + S2)× K ≈3, 600 cells per simulation. Each simulation and method was repeated five times per scenario, and performances were averaged across replicates.

[Publisher PDF page](https://www.nature.com/articles/s41467-020-19894-4.pdf#page=3) · [Article](https://doi.org/10.1038/s41467-020-19894-4)

[Exact retained reader passage](http://127.0.0.1:52718/?session_id=ps_862e882eb069&document_sha256=7b4cc7a8890549c6f34d6ebdb3660c2143bc7830b8004e8cfae270eaa72dbc0a&annotation_id=ann_f429b9877eca402da836db133631b633&page=3&passage_sha256=a28d4dd5f81d7f87bede8ecfdf57438997840c1e1c4951219a9cd0fc130ecb51) (requires original local reader).

Evidence `n_000009` revision `15af4a45271ac9b6aa2eeb769773500bdd08fda4d24cf9f79fff466ea28d53ba`; imported review `unreviewed`.

> PDF page 3: Each cell additionally has a sub- population (cluster) label as well as a sample label; metadata should be linked to samples, such that they can be organized into comparable groups with sample-level replicates

[Publisher PDF page](https://www.nature.com/articles/s41467-020-19894-4.pdf#page=3) · [Article](https://doi.org/10.1038/s41467-020-19894-4)

[Exact retained reader passage](http://127.0.0.1:52718/?session_id=ps_862e882eb069&document_sha256=7b4cc7a8890549c6f34d6ebdb3660c2143bc7830b8004e8cfae270eaa72dbc0a&annotation_id=ann_f6f480c4dec04244b3dac030dccd93fa&page=3&passage_sha256=c17ec37c5f6daa70d12bcf5b8cdeefb975827468e28301481a910c5258ec94a1) (requires original local reader).

### muscat detects subpopulation-specific state transitions from multi-sample multi-condition single-cell transcriptomics data — Method finding and limits

Origin: agent; current review: unreviewed; cell revision `71b1a0305eb62ad1b2883ae4cf8a68ca7934d8278026687342e1d928b854b248`.

Interpretation: Most pseudobulk and cell-level mixed-model methods perform well for DE, DM and DP and are relatively consistent across simulation repeats. The selected passage supports both method families under these conditions.

Conditions: DE: mean expression changes; DM: modality changes; DP: mixture-proportion changes. Do not extend this result to DB, discussed separately as difficult when means do not differ, or infer a universal winner.

Evidence `n_000007` revision `065be0cc61106934ca465adb696265bf5fc631f06827e06a0521702952789107`; imported review `unreviewed`.

> PDF page 4: For DE, DM, and DP, there is a set of methods that perform generally well, including most of the pseudobulk approaches and cell-level MM models. Aggregation- and MM- based methods also performed fairly consistent across simulation replicates, while other methods were generally more erratic in their performance

[Publisher PDF page](https://www.nature.com/articles/s41467-020-19894-4.pdf#page=4) · [Article](https://doi.org/10.1038/s41467-020-19894-4)

[Exact retained reader passage](http://127.0.0.1:52718/?session_id=ps_862e882eb069&document_sha256=7b4cc7a8890549c6f34d6ebdb3660c2143bc7830b8004e8cfae270eaa72dbc0a&annotation_id=ann_703062d902e84743819ab31a018c9515&page=4&passage_sha256=a22e4c42ae8b4c12dc9ca5848319ce21cc0a00844649e278f7080d62913dbc66) (requires original local reader).

Evidence `n_000008` revision `eca1f65b8fb9ecfc58f72ec23ae4755a949c196a9674dfa2f6697b927957ffca`; imported review `unreviewed`.

> PDF page 3: To ensure that method performances are comparable and do not suffer from low cell numbers, we simulated an average of 200 cells per subpopulation-sample instance, amounting to a total of ~200 × (S1 + S2)× K ≈3, 600 cells per simulation. Each simulation and method was repeated five times per scenario, and performances were averaged across replicates.

[Publisher PDF page](https://www.nature.com/articles/s41467-020-19894-4.pdf#page=3) · [Article](https://doi.org/10.1038/s41467-020-19894-4)

[Exact retained reader passage](http://127.0.0.1:52718/?session_id=ps_862e882eb069&document_sha256=7b4cc7a8890549c6f34d6ebdb3660c2143bc7830b8004e8cfae270eaa72dbc0a&annotation_id=ann_f429b9877eca402da836db133631b633&page=3&passage_sha256=a28d4dd5f81d7f87bede8ecfdf57438997840c1e1c4951219a9cd0fc130ecb51) (requires original local reader).

## Source attribution

Selected author text and tables retain their authors' CC BY 4.0 licenses. No PDFs or third-party images are bundled. JATS transforms/slices and the deliberate whitespace duplicate remain recorded in packet.json.

- Beate Vieth; Swati Parekh; Christoph Ziegenhain; Wolfgang Enard; Ines Hellmann. A systematic evaluation of single cell RNA-seq analysis pipelines. [DOI](https://doi.org/10.1038/s41467-019-12266-7); [license](https://creativecommons.org/licenses/by/4.0/). PDF SHA-256 `112dcf8fe1db9ff5c33e05bda563e678cff5254ceffe8521dd37f439ae0c2940`; XML SHA-256 `baad86bf2478429d01e59a7a263a69638522759d4c03f00e7f88bd28360d788c`.
- Christoph Hafemeister; Rahul Satija. Normalization and variance stabilization of single-cell RNA-seq data using regularized negative binomial regression. [DOI](https://doi.org/10.1186/s13059-019-1874-1); [license](https://creativecommons.org/licenses/by/4.0/). PDF SHA-256 `6926a728faa6400b2e3945931b078f088e1873cc220e59eec782ed2e8e255b4a`; XML SHA-256 `575d6101c7cacbe08e8b83d75ad09dea04b21eee33c1ba8b61ba93cc23784ba5`.
- F William Townes; Stephanie C Hicks; Martin J Aryee; Rafael A Irizarry. Feature selection and dimension reduction for single-cell RNA-Seq based on a multinomial model. [DOI](https://doi.org/10.1186/s13059-019-1861-6); [license](https://creativecommons.org/licenses/by/4.0/). PDF SHA-256 `5d3382bfbf474e6266a1278460e5d3e54166405f975ce1e92bdbacfca414e2ae`; XML SHA-256 `3bcd7817e357ef4343060c959c6973b8391ea7a0294b06261d2e45c2f696cf4e`.
- Jan Lause; Philipp Berens; Dmitry Kobak. Analytic Pearson residuals for normalization of single-cell RNA-seq UMI data. [DOI](https://doi.org/10.1186/s13059-021-02451-7); [license](https://creativecommons.org/licenses/by/4.0/). PDF SHA-256 `673d6bd4ed3f6ea2d90067f0e046decb118ff281bf482a7fdad444ab52b03ddc`; XML SHA-256 `15b8ff0f4abb46b6fd1245968db39f5538d1402c9d0d7dd7295115ae832b6bdc`.
- Jordan W. Squair; Matthieu Gautier; Claudia Kathe; Mark A. Anderson; Nicholas D. James; Thomas H. Hutson; Rémi Hudelle; Taha Qaiser; Kaya J. E. Matson; Quentin Barraud; Ariel J. Levine; Gioele La Manno; Michael A. Skinnider; Grégoire Courtine. Confronting false discoveries in single-cell differential expression. [DOI](https://doi.org/10.1038/s41467-021-25960-2); [license](https://creativecommons.org/licenses/by/4.0/). PDF SHA-256 `465fd1842f2e07e17d55e0170dd96dd994f61a15c019655f3f1503ef37e7f22a`; XML SHA-256 `b57cae308d321f956f9faf08e17409270a6c42e5688ae4aa80c36cda54c00ac9`.
- Kip D Zimmerman; Mark A Espeland; Carl D Langefeld. A practical solution to pseudoreplication bias in single-cell studies. [DOI](https://doi.org/10.1038/s41467-021-21038-1); [license](https://creativecommons.org/licenses/by/4.0/). PDF SHA-256 `464b4845a2b4d02fb3f2cd23b61f0bc9bd2287fc6ad2114baf7d64919006501c`; XML SHA-256 `ceb08f28de71780ed7379e5957f55e13ea0e7601d72568fc7dcd0fcba62fe3a0`.
- Helena L. Crowell; Charlotte Soneson; Pierre-Luc Germain; Daniela Calini; Ludovic Collin; Catarina Raposo; Dheeraj Malhotra; Mark D. Robinson. muscat detects subpopulation-specific state transitions from multi-sample multi-condition single-cell transcriptomics data. [DOI](https://doi.org/10.1038/s41467-020-19894-4); [license](https://creativecommons.org/licenses/by/4.0/). PDF SHA-256 `7b4cc7a8890549c6f34d6ebdb3660c2143bc7830b8004e8cfae270eaa72dbc0a`; XML SHA-256 `2b928a2e682ed7ec76e3f367182404c3fb472cc60af10d7efa1b4aad649a0553`.
- Malte D. Luecken; M. Büttner; K. Chaichoompu; A. Danese; M. Interlandi; M. F. Mueller; D. C. Strobl; L. Zappia; M. Dugas; M. Colomé-Tatché; Fabian J. Theis. Benchmarking atlas-level data integration in single-cell genomics. [DOI](https://doi.org/10.1038/s41592-021-01336-8); [license](https://creativecommons.org/licenses/by/4.0/). PDF SHA-256 `9383de7b64ae813371125ecfd92019834d32e835f1645baba4184c8738645e67`; XML SHA-256 `f65dd8b63336ff1a5045dad3cb9c5905ec3bb8b494a221f67dfbffb9a6f612db`.
- Aaron T L Lun; Karsten Bach; John C Marioni. Pooling across cells to normalize single-cell RNA sequencing data with many zero counts. [DOI](https://doi.org/10.1186/s13059-016-0947-7); [license](https://creativecommons.org/licenses/by/4.0/). PDF SHA-256 `42c11b662dd204b9bccb05d261d48e369583fc052c8ce72a32eba647164ce65d`; XML SHA-256 `9b5c62a7e01bd03b1e7ae8dc6233297743f18452a47e4ad563cf5e9bc2bff830`.
- Luke Zappia; Belinda Phipson; Alicia Oshlack. Splatter: simulation of single-cell RNA sequencing data. [DOI](https://doi.org/10.1186/s13059-017-1305-0); [license](https://creativecommons.org/licenses/by/4.0/). PDF SHA-256 `d66e2607c882c09a0eb90d1b622d2e2bac817e6d7f1a91df118a239c086660b8`; XML SHA-256 `4de891c74213c2ec6cbd3fc4f1e0b8a50571481e0e09f06b847e41cec6756224`.

## New held-out questions

A reviewer who did not tune retrieval must author at least ten new questions and source targets. Keep them separate and freeze them before scoring. The six public reserved questions are regressions, not blind tests.
