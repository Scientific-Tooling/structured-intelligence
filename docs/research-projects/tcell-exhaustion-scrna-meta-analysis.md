# 跨癌种 T 细胞耗竭轨迹的单细胞转录组元分析

Cross-Cancer Single-Cell Meta-Analysis of T Cell Exhaustion Trajectories

**状态**: 研究计划（待启动）
**版本**: v1.0
**日期**: 2026-03-16

---

## 一、课题定位与差异化

### 科学背景

T 细胞耗竭（T cell exhaustion）是肿瘤免疫逃逸的核心机制。在持续抗原暴露下，CD8+ T 细胞逐步丧失效应功能，上调抑制性受体（PD-1、TIM-3、LAG-3），最终进入功能衰竭状态。anti-PD-1/PD-L1 免疫检查点抑制剂（ICB）的疗效正是依赖于逆转这一过程 — 但仅对部分患者有效，且不同癌种应答率差异巨大（黑色素瘤 ~40%，胰腺癌 < 5%）。

单细胞 RNA 测序（scRNA-seq）揭示了 T 细胞耗竭并非一个单一终点，而是一条包含多个中间状态的分化轨迹：

```
Naive/Memory (TCF7⁺ IL7R⁺)
    → Effector (GZMB⁺ PRF1⁺ IFNG⁺)
        → Progenitor exhausted (TCF7⁺ PD-1⁺ SLAMF6⁺)  ← ICB 应答靶点
            → Terminally exhausted (TCF7⁻ PD-1ʰⁱ TIM-3⁺ TOX⁺)
```

**关键科学缺口**：已有研究（Zheng et al. 2021）描绘了泛癌 T 细胞图谱，但未系统量化不同癌种间耗竭程序的保守性与特异性，也未将轨迹状态与 ICB 临床应答直接关联。

### 核心科学问题

> 不同癌种中 CD8+ T 细胞的耗竭分化轨迹是否共享统一的转录调控程序？耗竭轨迹中的哪个状态比例最能预测免疫治疗应答？

### 三个子问题

1. **轨迹保守性**：跨癌种整合后，T 细胞耗竭轨迹是否收敛为一条共享路径，还是各癌种各有独立轨迹？
2. **状态量化**：能否构建一个连续的「耗竭评分」（exhaustion score），取代传统的二元分类（exhausted vs non-exhausted）？
3. **临床预测**：在 ICB 治疗队列中，治疗前肿瘤内 T 细胞的耗竭状态组成能否预测应答/无应答？

### 与现有工作的差异化

| 现有工作 | 本研究的差异 |
|----------|-------------|
| Zheng et al. 2021 *Science*：泛癌 T 细胞图谱，侧重描述性分类 | 引入伪时间轨迹分析定量耗竭过程，构建连续评分而非离散分类 |
| Sade-Feldman et al. 2018 *Cell*：黑色素瘤 ICB 应答标志物 | 跨癌种验证其标志物的泛化能力，而非限于单一癌种 |
| 各研究独立分析各自数据集 | 跨数据集整合后做统一轨迹分析，消除实验室批次效应后比较生物学差异 |

本研究的独特贡献：
1. **整合-轨迹-预测三步闭环**：从跨数据集整合出发，经轨迹重建产出连续耗竭评分，最终用该评分预测 ICB 应答
2. **贝叶斯效应量估计**：对核心耗竭标记基因的跨癌种效应量做后验推断，取代单纯 p 值报告
3. **AI 辅助流程验证**：系统记录 structured-intelligence 工具组合在真实研究场景中的表现

---

## 二、数据来源

### 三个公开 scRNA-seq 数据集

| 编号 | 来源文献 | GEO | 癌种 | 细胞数 | 关键特征 |
|------|----------|-----|------|--------|----------|
| D1 | Zheng et al. 2021 *Science* | GSE156728 | 泛癌（21 癌种） | ~400K T 细胞 | 提供跨癌种 T 细胞参考图谱 |
| D2 | Yost et al. 2019 *Nat Med* | GSE123813 | 基底细胞癌（BCC） | ~34K 细胞 | 含 anti-PD-1 治疗前后配对样本 |
| D3 | Sade-Feldman et al. 2018 *Cell* | GSE120575 | 黑色素瘤 | ~16K 细胞 | 含 ICB 应答者 vs 无应答者注释 |

### D1 子集选择策略

Zheng 2021 包含 21 个癌种，全量分析不必要。选择 4 个 ICB 临床相关性最高的癌种子集：

| 癌种 | 缩写 | ICB 批准状态 | 选择理由 |
|------|------|-------------|----------|
| 黑色素瘤 | SKCM | 一线 ICB | ICB 应答率最高（~40%），可与 D3 交叉验证 |
| 非小细胞肺癌 | NSCLC | 一线/二线 ICB | 临床使用最广泛的 ICB 适应症 |
| 肾细胞癌 | RCC | 一线 ICB | 高免疫浸润，ICB 应答率中等（~25%） |
| 膀胱癌 | BLCA | 二线 ICB | 应答率较低（~20%），提供负面参照 |

**预估子集规模**：~100K-150K T 细胞（从 D1 的 400K 中选取 4 个癌种）

### 数据格式预期

- D1：h5ad 或 10x MTX 格式（Scanpy 生态）
- D2：10x MTX 或 h5 格式（CellRanger 输出）
- D3：TPM 矩阵或 count 矩阵（CSV/TSV）

**格式统一步骤**：所有数据统一转换为 AnnData（.h5ad）格式后进入分析流程。

### 元数据需求

每个数据集须确认以下字段可获取性：

| 字段 | D1 | D2 | D3 | 用途 |
|------|----|----|----|----- |
| 患者 ID | 必须 | 必须 | 必须 | 伪重复控制 |
| 癌种 | 必须 | 固定 (BCC) | 固定 (MEL) | 跨癌种比较 |
| 治疗状态 | — | 必须 (pre/post) | 必须 (pre) | 轨迹-治疗关联 |
| ICB 应答 | — | 可选 | 必须 (R/NR) | 预测模型 |
| 细胞类型注释 | 可用 | 可用 | 可用 | 参考验证 |

---

## 三、研究流程

### 阶段 A：文献综合与假设构建

| 步骤 | Skill / Agent | 任务 | 产出 |
|------|--------------|------|------|
| A1 | `research` | 综述 T 细胞耗竭生物学：关键转录因子（TOX, NR4A, BATF）、表面标记（PD-1, TIM-3, LAG-3, TIGIT）、信号通路（TCR 信号强度 → NFAT/AP-1 失衡） | 耗竭标记基因列表（分层：核心/扩展/癌种特异） |
| A2 | `research` | 调研 scRNA-seq 整合与轨迹分析最佳实践：Harmony vs scVI、扩散伪时间 vs RNA velocity、批次校正评估指标（kBET, LISI） | 方法选择决策树 |
| A3 | `research` | 确认三个目标数据集的数据格式、已有注释、原始文献方法 | 数据获取策略文档 |

### 阶段 B：数据获取

| 步骤 | Skill | 任务 | 产出 |
|------|-------|------|------|
| B1 | `search-geo` | 检索 GSE156728、GSE123813、GSE120575，确认样本列表和补充文件清单 | 数据集摘要表 + 文件URL列表 |
| B2 | `download-geo` | 下载各数据集计数矩阵和元数据文件 | count matrices + metadata TSV |
| B3 | `ncbi-eutilities-assistant` | 查询关键耗竭基因（TOX, PDCD1, HAVCR2, TIGIT, LAG3）的 NCBI Gene 记录，获取标准基因符号和同义词 | 基因 ID 映射表（确保跨数据集 ID 一致性） |

**检查点**：确认所有矩阵可读取，基因名统一为 HGNC Symbol，metadata 字段完整。

### 阶段 C：单细胞分析流程

由 `ngs-analysis-expert` agent 协调以下步骤。

#### C1. 质量控制

| 步骤 | Skill | 任务 | 参数 |
|------|-------|------|------|
| C1.1 | `scrnaseq-quality-control` | 对每个数据集独立执行 QC 过滤 | min_genes=200, max_genes=5000, max_mt_pct=15%, doublet_method=scrublet |

**QC 过滤标准**：
- 细胞：200 < 检出基因数 < 5000，线粒体基因比例 < 15%
- 基因：在 ≥10 个细胞中表达
- Doublet：Scrublet 预测得分 > 0.25 标记为 doublet 并移除
- 每个数据集独立 QC，记录各步过滤细胞数

**QC 检查点**：
- 各数据集过滤后保留率应 > 70%
- 线粒体基因分布应呈单峰（双峰提示死细胞混入）
- Doublet 比例应 < 10%（10x 平台 ~1-8% 取决于 loading 密度）

#### C2. 跨数据集整合

| 步骤 | Skill | 任务 | 参数 |
|------|-------|------|------|
| C2.1 | `scrnaseq-integration` | 合并 3 个数据集，Harmony 批次校正 | method=harmony, batch_key=dataset, n_hvgs=3000, n_pcs=50 |

**整合策略选择依据**：
- Harmony：CPU 友好、内存效率高、对中等规模数据集（< 500K 细胞）表现稳健
- 不选 scVI：需 GPU，且对本研究规模数据无显著优势
- 不选 Seurat CCA：对大数据集（> 100K 细胞）内存消耗过高

**整合质量评估**：
- UMAP 可视化：按 dataset 着色应混合良好，按 cell type 着色应保持分离
- LISI 指标：iLISI（integration LISI）应接近数据集数量（3），cLISI（cell-type LISI）应接近 1
- 若整合不充分，增加 Harmony 迭代次数或调整 theta 参数

#### C3. 聚类与注释

| 步骤 | Skill | 任务 | 参数 |
|------|-------|------|------|
| C3.1 | `scrnaseq-clustering` | 全细胞群 Leiden 聚类 | resolution=1.0, n_neighbors=15 |
| C3.2 | `scrnaseq-cell-type-annotation` | 细胞类型注释（两轮） | method=combined (singler + manual markers) |

**两轮注释策略**：

第一轮（粗注释）：区分大类
| 细胞类型 | 标记基因 |
|----------|----------|
| CD8+ T | CD8A, CD8B |
| CD4+ T | CD4, IL7R |
| NK | NKG7, KLRD1, CD8A⁻ |
| Treg | FOXP3, IL2RA, CTLA4 |
| 其他免疫 | 标记不符合以上任何类别 |

第二轮（精注释，仅 CD8+ T 细胞子集）：
| 状态 | 标记基因 |
|------|----------|
| Naive | CCR7, TCF7, LEF1, SELL |
| Effector memory | GZMK, EOMES, CD44 |
| Effector | GZMB, PRF1, GNLY, NKG7 |
| Progenitor exhausted | TCF7, PD-1(PDCD1), SLAMF6, CXCR5 |
| Terminally exhausted | HAVCR2(TIM-3), ENTPD1(CD39), TOX, LAYN |

**子集化**：注释完成后，提取全部 CD8+ T 细胞（预估 50K-80K 细胞），用于后续耗竭轨迹分析。对 CD8+ 子集重新执行 HVG 选择 → PCA → Harmony → 聚类 → 精注释。

#### C4. 轨迹分析（核心分析步骤）

| 步骤 | Skill | 任务 | 参数 |
|------|-------|------|------|
| C4.1 | `scrnaseq-trajectory-analysis` | 扩散伪时间（diffusion pseudotime）重建耗竭轨迹 | analysis_type=pseudotime, root_cluster=Naive |

**轨迹分析细节**：
- 使用扩散图（diffusion map）而非 RNA velocity（后者需要 spliced/unspliced 矩阵，GEO 计数矩阵通常不含此信息）
- Root cell 选择：以 Naive CD8 T 细胞（CCR7⁺ TCF7⁺）作为起点
- 预期轨迹方向：Naive → Effector → Progenitor exhausted → Terminally exhausted
- 关键输出：每个细胞的伪时间值（pseudotime score, 0-1 连续值）

**耗竭评分构建**：
- 基于伪时间轴提取沿轨迹变化最显著的基因（top 50 genes with highest pseudotime correlation）
- 用这 50 个基因的加权表达量构建「耗竭评分」（exhaustion score）
- 该评分为连续值，可用于后续统计分析

#### C5. 差异表达分析

| 步骤 | Skill | 任务 | 参数 |
|------|-------|------|------|
| C5.1 | `scrnaseq-differential-expression` | Progenitor exhausted vs Terminally exhausted 差异基因 | method=pseudobulk-deseq2, 按患者聚合 |
| C5.2 | `scrnaseq-differential-expression` | 跨癌种比较：每个癌种的 exhausted 细胞 vs 对应 effector 细胞 | method=wilcoxon |

**伪重复问题处理**：
- 单细胞 DE 分析中，同一患者的细胞不是独立观测
- C5.1 使用 pseudobulk 方法：先按患者+状态聚合为伪批量样本，再用 DESeq2 做差异分析
- C5.2 用于发现性分析（exploratory），Wilcoxon 检验辅以 BH FDR 校正

---

### 阶段 D：统计分析

由 `statistical-analysis-expert` agent 协调方法选择。

#### D1. 数据质量与探索性分析

| 步骤 | Skill | 任务 | 产出 |
|------|-------|------|------|
| D1.1 | `stat-assess-data-quality` | 检查整合后表达矩阵：零值比例、检出基因数分布、各数据集贡献的细胞比例 | 数据质量报告 |
| D1.2 | `stat-analyze-distribution` | 耗竭评分的分布形态分析：各癌种内是否呈双峰（提示离散状态）还是连续梯度 | 密度图 + 正态性/多峰性检验 |
| D1.3 | `stat-pca` | 整合后 CD8 T 细胞的 PCA：按癌种着色 vs 按耗竭状态着色，评估批次残余 | PCA 散点图 × 2 |
| D1.4 | `stat-nonlinear-embedding` | UMAP 降维可视化：叠加伪时间着色、耗竭评分着色、癌种着色 | UMAP 图 × 3 |

**关键决策点**：
- 如果 D1.2 显示耗竭评分呈双峰 → 后续分析同时支持连续（评分）和离散（二分类）两种策略
- 如果 D1.3 显示 PCA 第一主成分仍分离数据集 → 需要增强 Harmony 参数或考虑 per-gene 回归去批次

#### D2. 跨癌种耗竭程序比较

| 步骤 | Skill | 任务 | 产出 |
|------|-------|------|------|
| D2.1 | `stat-compare-multiple-groups` | 4 个癌种（SKCM/NSCLC/RCC/BLCA）的耗竭评分比较：Kruskal-Wallis + Dunn post-hoc | 癌种间评分差异箱线图 + post-hoc 表 |
| D2.2 | `stat-compare-two-groups` | 每对癌种间核心耗竭基因（TOX, PDCD1, HAVCR2, ENTPD1）表达量比较 | 每基因 × 每对癌种的效应量和 p 值 |
| D2.3 | `stat-compare-multiple-groups` | 耗竭细胞亚群占总 CD8 T 的比例 — 按癌种比较（患者级别统计，避免伪重复） | 状态比例条形图 + 检验结果 |

**伪重复控制**：D2.1 和 D2.3 的统计单元是「患者」而非「细胞」。先将每个患者的细胞聚合为一个观测值（取中位耗竭评分或状态比例），再做跨组比较。

#### D3. 耗竭程序的保守性与特异性

| 步骤 | Skill | 任务 | 产出 |
|------|-------|------|------|
| D3.1 | `stat-pairwise-correlation` | 跨癌种耗竭差异基因（C5.2 产出）的基因-基因相关矩阵：哪些基因模块在所有癌种中共相关 | 相关热图 + 共表达模块 |
| D3.2 | `stat-cluster-samples` | 基于耗竭基因表达谱的患者无监督聚类：是否形成与癌种无关的「耗竭亚型」 | 聚类热图 + 最优 K |
| D3.3 | `stat-bayesian-estimation` | 对 D2.2 中核心耗竭基因的跨癌种效应量做贝叶斯层级模型估计 | 后验分布图 + 95% HDI |

**D3.1 的科学假设**：
- 若耗竭程序高度保守 → 各癌种的基因-基因相关结构应高度相似
- 若存在癌种特异性 → 部分基因对的相关方向会在癌种间反转

**D3.3 的贝叶斯层级模型**：
- 第一层：各癌种内的效应量（均值差）
- 第二层：跨癌种的总体效应量（超参数）
- 结果：如果总体后验 95% HDI 不跨零 → 该基因是「保守耗竭标记」
- 如果各癌种的后验显著分散 → 该基因是「癌种特异性标记」

#### D4. 临床应答预测

| 步骤 | Skill | 任务 | 产出 |
|------|-------|------|------|
| D4.1 | `stat-logistic-regression` | 用 D3 数据集（Sade-Feldman）：以耗竭评分 + 状态比例预测 ICB 应答（R vs NR） | AUC-ROC + 系数表 |
| D4.2 | `stat-logistic-regression` | 对比模型：仅用已知标记（TCF7 表达）vs 耗竭评分 vs 状态组成比例 | 三模型 AUC 对比 |
| D4.3 | `stat-compare-two-groups` | D2 数据集（Yost）：anti-PD-1 治疗前后耗竭评分变化（配对比较） | 治疗前后配对差异图 |

**D4.1 特征定义**：
- 特征 1：患者的中位耗竭评分（连续值）
- 特征 2：Progenitor exhausted 占 CD8 T 比例（连续值）
- 特征 3：Terminally exhausted 占 CD8 T 比例（连续值）
- 特征 4：Progenitor / Terminal 比值（连续值）
- 结局变量：ICB 应答（R=1, NR=0）

**样本量限制**：D3 数据集仅 ~20-30 位患者，统计功效有限。因此：
- 使用 leave-one-out 交叉验证（LOOCV）而非 train/test split
- 报告 AUC 的置信区间（bootstrap 1000 次）
- 结论措辞为「探索性发现」，需要更大队列验证

### 阶段 E：结论综合与工具评估

| 步骤 | Skill | 任务 | 产出 |
|------|-------|------|------|
| E1 | `research` | 整合发现：(1) 耗竭程序保守性结论，(2) 癌种特异性发现，(3) 临床预测价值评估，(4) 与现有文献对比 | 结论综合文档 |
| E2 | `research` | 工具链评估：每个 skill 的实际运行情况、遇到的问题、参数调整记录、改进建议 | 工具评估报告 |

---

## 四、混杂因素与偏倚控制

### 技术混杂

| 因素 | 风险 | 控制策略 |
|------|------|----------|
| 数据集批次效应 | 高 — 不同实验室、试剂盒、测序深度 | Harmony 整合 + LISI 评估 + 可视化验证 |
| 测序深度差异 | 中 — 影响基因检出和聚类 | QC 阶段按数据集报告中位基因数；下采样敏感性分析 |
| 基因 ID 不一致 | 低 — 但处理不当会丢失关键基因 | B3 步骤统一为 HGNC Symbol |
| 细胞类型注释偏差 | 中 — 自动注释可能误分类 | 两轮注释（自动+标记基因验证）+ 与原文注释交叉比对 |

### 生物学混杂

| 因素 | 风险 | 控制策略 |
|------|------|----------|
| 患者间异质性 | 高 — 同癌种患者间差异可能大于癌种间差异 | 统计分析以患者为单位（非细胞），报告患者内方差 |
| 肿瘤突变负荷（TMB） | 中 — 影响免疫原性和耗竭程度 | 若元数据可获取则作为协变量；否则声明为 limitation |
| 取样部位（肿瘤中心 vs 边缘） | 中 — 影响免疫浸润组成 | 多数数据集为整块肿瘤消化，空间信息不可获取；声明为 limitation |
| 先前治疗史 | 中 — 化疗/放疗改变免疫状态 | 检查元数据中 treatment-naive vs pre-treated 标注 |

### 统计偏倚

| 因素 | 风险 | 控制策略 |
|------|------|----------|
| 伪重复（pseudoreplication） | 高 — 单细胞分析最常见统计陷阱 | C5.1 用 pseudobulk；D2 以患者为统计单元 |
| 多重比较 | 中 — 跨基因、跨癌种多次检验 | BH FDR 校正，报告校正后 q 值 |
| 过拟合（预测模型） | 高 — 患者样本量小（~30） | LOOCV + bootstrap CI；明确声明为探索性 |
| 选择偏倚（癌种选择） | 低 — 仅选了 4 个癌种 | 选择依据是 ICB 临床相关性，非数据挖掘 |

---

## 五、计算资源需求

| 资源 | 需求量 | 说明 |
|------|--------|------|
| 存储 | **~15-20 GB** | count matrices (~5 GB) + 中间 h5ad 文件 (~10 GB) + 图表 |
| 内存 | **16 GB 够用，32 GB 舒适** | Scanpy 处理 ~150K 细胞的峰值内存 |
| CPU | 4-8 核 | Harmony、Leiden、DE 分析可并行 |
| GPU | **不需要** | 选择 Harmony（非 scVI）、Scrublet（非 CellBender）避免 GPU 依赖 |
| 耗时估计 | **总计 1-2 天** | 见下方分解 |

### 耗时分解

| 阶段 | 预估时间 | 瓶颈 |
|------|----------|------|
| B: 数据下载 | 1-3 小时 | 网络带宽（~5 GB 总下载量） |
| C1: QC | 30 分钟 | Scrublet doublet 检测 |
| C2: 整合 | 1-2 小时 | Harmony 迭代收敛 |
| C3: 聚类+注释 | 1-2 小时 | 手动标记基因验证 |
| C4: 轨迹分析 | 1-2 小时 | Diffusion map 计算 |
| C5: DE | 30 分钟 | Pseudobulk DESeq2 |
| D: 统计分析 | 2-4 小时 | 贝叶斯 MCMC 采样（D3.3） |
| E: 综合 | 2 小时 | 文献交叉比对 |

### 软件依赖

| 包 | 版本建议 | 用途 |
|----|----------|------|
| scanpy | ≥1.9 | 核心分析框架 |
| harmonypy | ≥0.0.9 | 批次整合 |
| scrublet | ≥0.2 | Doublet 检测 |
| diffusion pseudotime (scanpy 内置) | — | 轨迹分析 |
| DESeq2 (R/rpy2) | ≥1.38 | Pseudobulk DE |
| pymc | ≥5.0 | 贝叶斯层级模型 |
| scikit-learn | ≥1.3 | LOOCV、AUC 计算 |

---

## 六、预期产出清单

| 编号 | 产出物 | 格式 | 验证标准 |
|------|--------|------|----------|
| O1 | QC 报告（各数据集） | HTML/PDF × 3 | 过滤保留率 > 70%，doublet < 10% |
| O2 | 整合后 UMAP（按数据集/癌种/细胞类型着色） | PDF × 3 | 数据集批次混合良好，细胞类型保持分离 |
| O3 | CD8 T 细胞亚群注释图 | PDF | 至少识别 Naive/Effector/Progenitor exh/Terminal exh 四个状态 |
| O4 | 耗竭伪时间轨迹图 | PDF | 轨迹方向与已知生物学一致（Naive→Exhausted） |
| O5 | 耗竭评分密度图（按癌种分面） | PDF | 揭示分布形态差异 |
| O6 | 跨癌种耗竭评分比较（箱线图 + 检验） | PDF + TSV | Kruskal-Wallis p < 0.05 |
| O7 | 核心耗竭基因贝叶斯后验分布图 | PDF | TOX, PDCD1, HAVCR2 的 95% HDI 不跨零 |
| O8 | 基因共表达网络（保守模块 vs 特异模块） | PDF + TSV | 至少识别 1 个保守模块和 1 个特异模块 |
| O9 | 患者聚类热图（耗竭基因谱） | PDF | 聚类结果与临床特征有关联 |
| O10 | ICB 应答预测 AUC-ROC 曲线 | PDF | AUC > 0.65 有意义（样本量小，期望保守） |
| O11 | 三模型对比表（评分 vs 比例 vs 基线标记） | TSV | 至少一个模型 AUC > 基线 |
| O12 | 治疗前后耗竭评分变化图（Yost 数据） | PDF | 配对检验结果 |
| O13 | 与文献结论对比表 | Markdown | 核心发现与 Zheng 2021 方向一致率 > 80% |
| O14 | 工具链评估报告 | Markdown | 每个 skill 的运行日志与改进建议 |

---

## 七、Skill/Agent 完整调用映射

```
阶段A (文献)     research × 3 ─────────────────────────────────────────┐
                                                                       │
阶段B (数据)     search-geo × 3                                        │
                  download-geo × 3                                      │
                  ncbi-eutilities-assistant                              │
                                                                       │
阶段C (单细胞)   scrnaseq-quality-control                              │
                  scrnaseq-integration                                   │
                  scrnaseq-clustering                                    │
                  scrnaseq-cell-type-annotation                          │
                  scrnaseq-trajectory-analysis   ← 核心分析              │
                  scrnaseq-differential-expression                       │
                  ↑                                                     │
                  └── ngs-analysis-expert (协调 C1-C5) ───────────────┤
                                                                       │
阶段D (统计)     stat-assess-data-quality                              │
                  stat-analyze-distribution                              │
                  stat-pca                                               │
                  stat-nonlinear-embedding                               │
                  stat-compare-two-groups                                │
                  stat-compare-multiple-groups                           │
                  stat-pairwise-correlation                              │
                  stat-cluster-samples                                   │
                  stat-logistic-regression                               │
                  stat-bayesian-estimation                               │
                  ↑                                                     │
                  └── statistical-analysis-expert (协调 D1-D4) ───────┤
                                                                       │
阶段E (综合)     research × 2 ─────────────────────────────────────────┘
```

### 覆盖统计

- **Agent**：2/2（100%）
- **Skill**：20/51（39%）— 全部 scRNA-seq 技能（除 cellranger-count）+ 10/14 统计技能 + 数据检索 + research
- **未使用的 skill 类别**：
  - NGS 预处理（ngs-quality-control, ngs-read-preprocessing）— 从计数矩阵起步，无需 FASTQ 处理
  - WGS/WES 变异检测 — 与本课题无关
  - RNA-seq 批量转录组 — scRNA-seq 自有流程
  - 宏基因组 — 与本课题无关
  - 蛋白质工程 — 与本课题无关
  - stat-fit-linear-model, stat-fit-glm, stat-learn-bayesian-network, stat-survival-analysis — 与分析设计无直接关联

---

## 八、风险与缓解

| 风险 | 严重性 | 概率 | 缓解策略 |
|------|--------|------|----------|
| GEO 数据格式与预期不符（非标准矩阵格式） | 中 | 中 | 预留格式探索时间；最差情况手写解析脚本 |
| D1 (Zheng) 子集后 T 细胞数量不足 | 低 | 低 | 扩大癌种选择（加入 HNSC、CRC 等） |
| Harmony 整合后批次残余过强 | 中 | 低 | 增加 theta 参数或切换至 BBKNN；执行 per-gene 回归去批次 |
| 轨迹分析方向错误（伪时间方向反转） | 低 | 中 | 通过已知标记基因沿轨迹表达趋势验证方向；手动指定 root cell |
| 预测模型过拟合（D3 仅 ~30 位患者） | 高 | 高 | LOOCV + bootstrap CI；结论限定为探索性；建议外部验证队列 |
| 跨数据集基因交集过少 | 低 | 低 | 使用 inner join 取共有基因；检查关键标记基因是否全部保留 |
| 某数据集原始注释与我们的注释不一致 | 中 | 中 | 以我们的标记基因注释为主，但报告与原文注释的一致率 |

---

## 九、成功标准

### 科学维度

- [ ] 识别出至少 4 个 CD8 T 细胞状态（Naive/Effector/Progenitor exhausted/Terminally exhausted），并经标记基因验证
- [ ] 成功重建从 Naive 到 Terminally exhausted 的连续伪时间轨迹
- [ ] 在 ≥3/4 癌种中发现共享的耗竭基因模块（≥20 个基因，Spearman ρ > 0.3）
- [ ] 识别出至少 1 个癌种特异性耗竭特征
- [ ] ICB 应答预测 AUC > 0.65（考虑到小样本量，这已有意义）

### 方法学维度

- [ ] 全流程从 GEO 下载到最终结论可在单台 16GB RAM 机器上完成
- [ ] 伪重复在所有统计检验中得到正确处理（以患者为统计单元）
- [ ] 批次效应整合经 LISI 指标定量验证
- [ ] 贝叶斯模型收敛诊断通过（R-hat < 1.01, ESS > 400）

### 工具评估维度

- [ ] 20 个 skill 在真实数据上的运行成功率和耗时记录
- [ ] 识别出至少 3 个 skill 的改进方向（文档补充、参数默认值、错误处理）
- [ ] 完成两个 agent 在多步协调中的效率评估（决策正确率、人工干预次数）

---

## 十、时间规划

| 阶段 | 预估周期 | 前置依赖 |
|------|----------|----------|
| A: 文献综合 | 第 1 天 | 无 |
| B: 数据获取 | 第 1-2 天 | A1 完成（确认数据集） |
| C1-C3: QC→聚类→注释 | 第 2-3 天 | B 完成 |
| C4-C5: 轨迹→DE | 第 3-4 天 | C3 完成 |
| D1-D2: 探索性分析 | 第 4-5 天 | C4 完成（需要耗竭评分） |
| D3: 保守性分析 | 第 5-6 天 | D2 完成 |
| D4: 预测模型 | 第 6 天 | D3 完成 |
| E: 综合 | 第 7 天 | D4 完成 |
