# 肠道菌群跨队列元分析用于结直肠癌早期检测

Cross-Cohort Meta-Analysis of Gut Microbial Signatures for Colorectal Cancer Detection

**状态**: 研究计划（待启动）
**版本**: v0.2 — 评审修订版
**日期**: 2026-03-16

---

## 一、课题定位与差异化

### 科学问题

> 哪些肠道微生物的分类学与功能学特征能在多个独立队列中稳定区分结直肠癌患者与健康对照，并支撑一个跨队列泛化的早期诊断模型？

### 三个子问题

1. **差异特征发现**：各队列内部哪些菌种/通路在 CRC vs 健康对照间显著差异？
2. **跨队列稳健性**：哪些特征在 ≥3/4 队列中一致显著？元分析效应量有多大？
3. **诊断模型泛化**：联合分类学+功能学特征的模型 AUC 能否在 LODO 验证中 > 0.80？

### 与现有工作的差异化（关键）

Thomas et al. 2019 (Nature Medicine) 已对类似数据集进行了元分析。本研究**不是对其结果的简单重复**，而是：

1. **方法论示范**：展示 AI 辅助流程（structured-intelligence 工具组合）能否完整复现并扩展已发表的元分析结论 — 这是**计算可复现性**的元科学研究
2. **功能层面扩展**：Thomas 等人侧重分类学特征，我们增加 HUMAnN3 功能通路分析并构建联合诊断模型
3. **贝叶斯效应量估计**：用 PyMC 对核心差异菌种的效应量做后验分布估计，提供比频率主义 p 值更丰富的统计推断
4. **工具链压力测试**：系统记录每个 skill 在真实研究中的表现、瓶颈与改进方向

---

## 二、数据来源

### 四个公开宏基因组队列

| 队列编号 | 来源文献 | BioProject | 国家 | 样本量 (CRC/CTR) | 测序平台 |
|----------|----------|------------|------|-------------------|----------|
| C1 | Wirbel et al. 2019 Nat Med | PRJEB27928 | 德/法/日/美/中 | 149 / 217 | Illumina HiSeq |
| C2 | Yu et al. 2017 Nat Microbiol | PRJEB12449 | 中国 | 74 / 54 | Illumina HiSeq |
| C3 | Zeller et al. 2014 Mol Syst Biol | ERP005534 | 法国 | 53 / 61 | Illumina HiSeq |
| C4 | Feng et al. 2015 Nat Commun | PRJEB10878 | 奥地利 | 46 / 63 | Illumina HiSeq |

**总计**: ~322 CRC + ~395 对照 = ~717 样本

### 注意事项

- C1 (Wirbel) 是多国汇总数据，内部可能含亚批次
- C3 (Zeller) 和 C4 (Feng) 数据较老，测序深度可能偏低
- 所有元数据须在 SRA 检索阶段确认：年龄、性别、BMI、CRC 分期、用药史

---

## 三、研究流程（修订版）

### 阶段 A：文献综合与假设构建

| 步骤 | Skill / Agent | 任务 | 产出 |
|------|--------------|------|------|
| A1 | `research` | 综述 CRC-菌群元分析文献（Thomas 2019, Wirbel 2019 等），提取已知差异菌种列表 | 假设清单、已知 CRC 标志菌种表 |
| A2 | `research` | 调研组成型数据分析方法（CLR, ANCOM-BC），确定统计策略 | 方法选择依据文档 |

### 阶段 B：数据获取与预处理

| 步骤 | Skill / Agent | 任务 | 产出 |
|------|--------------|------|------|
| B1 | `search-sra` ×4 | 检索 4 个 BioProject，获取样本列表和元数据 | 样本清单 TSV（含表型注释） |
| B2 | `download-sra` ×4 | 下载原始 FASTQ | 原始测序数据（预估 400-600 GB） |
| B3 | `ngs-quality-control` | FastQC + MultiQC 对 4 个队列统一质控 | 每队列 MultiQC HTML 报告 |
| B4 | `ngs-read-preprocessing` | fastp 去接头、去低质量碱基、长度过滤 | 清洁 FASTQ + fastp JSON 统计 |
| B5 | `metagenome-host-removal` | Bowtie2 比对 GRCh38 去宿主 | 去宿主 FASTQ + 去除率统计 |

**质控检查点**：
- 各队列过滤后保留率应 > 80%
- 去宿主后宿主比例应 < 5%（粪便样本通常 < 1%）
- 若某样本测序深度 < 1M 读段，标记为低质量并在后续分析中评估其影响

### 阶段 C：微生物组学分析

| 步骤 | Skill / Agent | 任务 | 产出 |
|------|--------------|------|------|
| C1 | `metagenome-taxonomic-profiling` | Kraken2/Bracken 分类 + MetaPhlAn4 交叉验证 | 物种丰度矩阵（样本×物种） |
| C2 | `metagenome-functional-profiling` | HUMAnN3 功能注释 | 基因家族丰度表 + MetaCyc 通路丰度表 |

**阶段协调**：`ngs-analysis-expert` agent 统筹 B1–C2 全过程，处理失败样本、参数调整。

**双平台验证策略**：Kraken2 和 MetaPhlAn4 使用不同算法（k-mer vs marker gene），两者一致的差异菌种具有更高可信度。

### 阶段 D：统计分析

统计分析分四层递进，由 `statistical-analysis-expert` agent 协调方法选择。

#### D1. 数据质量与探索性分析

| 步骤 | Skill | 任务 | 产出 |
|------|-------|------|------|
| D1.1 | `stat-assess-data-quality` | 检查合并丰度矩阵的缺失率、零膨胀度、异常值 | 数据质量报告 |
| D1.2 | `stat-analyze-distribution` | α 多样性（Shannon/Simpson）分布分析 | 各队列多样性箱线图 + 正态性检验 |
| D1.3 | `stat-pca` | CLR 变换后 PCA 可视化（按队列着色 + 按疾病着色） | PCA 散点图 → 判断批次效应严重程度 |
| D1.4 | `stat-nonlinear-embedding` | UMAP 降维可视化 | UMAP 图（辅助 PCA 的非线性视角） |

**关键决策点**：如果 PCA 第一主成分主要分离队列而非疾病状态，则必须在后续分析前引入批次校正（ComBat-seq 或 per-feature 线性回归去批次）。

#### D2. 队列内差异分析

| 步骤 | Skill | 任务 | 产出 |
|------|-------|------|------|
| D2.1 | `stat-compare-two-groups` ×4 | 每个队列内 CRC vs CTR 物种丰度比较（Wilcoxon + BH FDR） | 4 张差异物种表（log2FC, p, q） |
| D2.2 | `stat-compare-two-groups` ×4 | 每个队列内 CRC vs CTR 通路丰度比较 | 4 张差异通路表 |
| D2.3 | `stat-compare-multiple-groups` | 跨队列批次效应检验（4 个队列对照组间 Kruskal-Wallis） | 受批次影响严重的特征列表 |

**组成型数据处理**：物种丰度在差异分析前须进行 CLR（centered log-ratio）变换，或使用 ANCOM-BC 方法直接处理组成型数据。这是评审修订中补充的关键步骤。

#### D3. 跨队列元分析与网络分析

| 步骤 | Skill | 任务 | 产出 |
|------|-------|------|------|
| D3.1 | `stat-bayesian-estimation` | 对 D2.1 中在 ≥2 队列显著的菌种做贝叶斯效应量估计（PyMC 层级模型） | 后验分布图 + 可信区间表 |
| D3.2 | `stat-pairwise-correlation` | 跨队列一致差异菌种间 SparCC/Spearman 相关分析 | 共存/排斥网络 + 相关热图 |
| D3.3 | `stat-cluster-samples` | 基于差异特征的无监督样本聚类 | 聚类热图 + 最优 K 值 |

**元分析策略**：对每个特征的 4 个队列效应量（CLR 均值差）做随机效应模型（DerSimonian-Laird），报告汇总效应量和异质性 I²。

#### D4. 诊断模型构建

| 步骤 | Skill | 任务 | 产出 |
|------|-------|------|------|
| D4.1 | `stat-logistic-regression` | 以跨队列一致特征为输入，LODO 交叉验证 | AUC-ROC 曲线 × 4（每次留一个队列做测试集） |
| D4.2 | 自行编写脚本 | 随机森林对比模型（scikit-learn） | AUC 对比表 |
| D4.3 | `stat-logistic-regression` | 分类学-only vs 功能-only vs 联合模型对比 | 三种模型 AUC 对比图 |

**LODO 验证协议**：
- 训练集：3 个队列合并
- 测试集：第 4 个队列
- 重复 4 次，报告平均 AUC ± 标准差
- 若 AUC > 0.80 表明模型具有跨队列泛化能力

### 阶段 E：结论综合

| 步骤 | Skill | 任务 | 产出 |
|------|-------|------|------|
| E1 | `research` | 将发现与 Thomas 2019 对比：哪些结论复现、哪些不一致、新发现是什么 | 对比总结表 |
| E2 | `research` | 方法可复现性报告：每个 skill 在流程中的实际表现、报错、参数调整记录 | 工具评估文档 |

---

## 四、混杂因素控制策略

### 已知混杂因素

| 混杂因素 | 影响机制 | 控制方法 |
|----------|----------|----------|
| 年龄 | 菌群多样性随年龄变化 | 逻辑回归中作为协变量 |
| 性别 | 部分菌种有性别差异 | 同上 |
| BMI | 肥胖与菌群组成强相关 | 同上（若元数据可获取） |
| 二甲双胍使用 | 显著改变肠道菌群 | 排除或标记使用者 |
| CRC 分期 | 早期 vs 晚期菌群特征不同 | 分层分析（若分期信息可获取） |
| 测序深度 | 影响物种检出灵敏度 | 稀释（rarefaction）或回归校正 |
| 地理/饮食 | 基线菌群组成差异 | 随机效应元分析模型吸收 |

### 元数据可获取性评估

在 B1（search-sra）阶段需确认每个队列提供了哪些元数据字段。若关键混杂因素数据缺失，需在结论中声明为 limitation。

---

## 五、计算资源需求

| 资源 | 需求量 | 说明 |
|------|--------|------|
| 存储 | ~800 GB | 原始 FASTQ + 中间文件 + 数据库 |
| 内存 | ≥64 GB | Kraken2 Standard DB 需 ~70 GB RAM |
| CPU | ≥16 核 | fastp、BWA-MEM2、HUMAnN3 均可多线程 |
| 耗时估计（单队列） | ~2-3 天 | QC→去宿主→分类→功能全流程 |
| 耗时估计（统计分析） | ~1 天 | 含贝叶斯 MCMC 采样 |

### 数据库预装

- Kraken2 Standard DB (~70 GB)
- Bracken DB (与 Kraken2 配套)
- MetaPhlAn4 DB (~15 GB)
- ChocoPhlAn + UniRef90 for HUMAnN3 (~35 GB)
- GRCh38 Bowtie2 索引 (~8 GB)

---

## 六、预期产出清单

| 编号 | 产出物 | 格式 | 验证标准 |
|------|--------|------|----------|
| O1 | 数据质量报告 | MultiQC HTML × 4 | 各队列过滤保留率 > 80% |
| O2 | 物种丰度矩阵 | TSV（717 样本 × N 物种） | Kraken2 分类率 > 40% |
| O3 | 功能通路丰度矩阵 | TSV（717 样本 × M 通路） | 通路覆盖率 > 60% |
| O4 | 差异物种火山图 | PDF × 4 队列 | 已知标志菌种（F. nucleatum 等）应在显著区 |
| O5 | 元分析效应量森林图 | PDF | ≥5 物种 q < 0.05 且 I² < 75% |
| O6 | 贝叶斯后验分布图 | PDF | 核心菌种 95% HDI 不跨零 |
| O7 | 菌种相关网络图 | PNG + Cytoscape 格式 | Hub 菌种应与文献吻合 |
| O8 | 样本聚类热图 | PDF | 至少部分分离 CRC/CTR |
| O9 | LODO 诊断 AUC-ROC 曲线 | PDF | 平均 AUC > 0.75 有意义，> 0.80 优秀 |
| O10 | 模型对比表 | TSV | 联合模型 AUC ≥ 单特征模型 |
| O11 | 与 Thomas 2019 结果对比表 | Markdown | 逐菌种方向一致性 > 80% |
| O12 | 工具链评估报告 | Markdown | 每个 skill 的运行日志与改进建议 |

---

## 七、Skill/Agent 完整调用映射

```
阶段A (文献)     research ─────────────────────────────────────────────┐
                                                                       │
阶段B (数据)     search-sra → download-sra → ngs-quality-control       │
                  → ngs-read-preprocessing → metagenome-host-removal    │
                  ↑                                                     │
                  └── ngs-analysis-expert (协调 B1-C2) ───────────────┤
                                                                       │
阶段C (组学)     metagenome-taxonomic-profiling                        │
                  metagenome-functional-profiling                       │
                                                                       │
阶段D (统计)     stat-assess-data-quality                              │
                  stat-analyze-distribution                             │
                  stat-pca                                              │
                  stat-nonlinear-embedding                              │
                  stat-compare-two-groups                               │
                  stat-compare-multiple-groups                          │
                  stat-bayesian-estimation                              │
                  stat-pairwise-correlation                             │
                  stat-cluster-samples                                  │
                  stat-logistic-regression                              │
                  ↑                                                     │
                  └── statistical-analysis-expert (协调 D1-D4) ───────┤
                                                                       │
阶段E (综合)     research ─────────────────────────────────────────────┘
```

**覆盖统计**：
- Agent：2/2（100%）
- Skill：17/51（33%）— 覆盖了全部宏基因组技能 + 全部数据检索技能 + 10/14 统计技能 + research
- 未使用的统计技能：`stat-fit-linear-model`, `stat-fit-glm`, `stat-learn-bayesian-network`, `stat-survival-analysis`（与本课题无直接关联）

---

## 八、风险与缓解

| 风险 | 严重性 | 缓解策略 |
|------|--------|----------|
| SRA 下载速度慢或中断 | 中 | 使用 prefetch + fasterq-dump 分批下载，保留 .sra 缓存 |
| 某队列元数据不完整（缺少混杂因素） | 中 | 降级为无协变量分析，在 limitations 中声明 |
| 批次效应过强导致队列无法合并 | 高 | 先用 per-dataset 分析确认信号存在，再用随机效应模型 |
| Kraken2 内存不足 | 中 | 降级为 MiniKraken2 DB 或仅用 MetaPhlAn4 |
| HUMAnN3 运行时间过长 | 中 | 选择子集样本（每组 30 例）做功能分析 |
| 诊断模型 AUC 低于预期 | 低 | 本身即有意义结论（负面结果），同时排查特征选择策略 |

---

## 九、成功标准

本研究将在以下三个维度评价成功与否：

### 科学维度
- [ ] 识别出 ≥5 个跨队列一致的差异菌种，且与已有文献（Thomas 2019）方向一致率 > 80%
- [ ] LODO 诊断模型平均 AUC > 0.75
- [ ] 功能通路层面发现与分类学层面互补的生物学信号

### 方法学维度
- [ ] 全流程可从原始数据到最终结论一键复现
- [ ] 每个分析步骤的参数选择有明确依据记录
- [ ] 统计方法选择经过假设检验验证（如正态性→参数/非参数选择）

### 工具评估维度
- [ ] 每个 skill 在真实数据上的运行成功率和耗时
- [ ] 识别出至少 3 个 skill 改进方向
- [ ] 完成两个 agent 在多步流程中的协调效率评估
