在现代生物研究中，统计方法几乎贯穿**实验设计、数据分析、结果解释与模型构建**的全过程。不同分支（分子生物学、基因组学、生态学、神经科学等）所用方法有所侧重，但整体可以从**六类统计结构**来理解：**描述统计、假设检验、回归模型、方差分析、多变量统计、以及概率模型与贝叶斯方法**。如果从研究流程结构来看，这些方法基本构成了生物数据分析的核心工具箱。

---

## 一、描述统计（Descriptive Statistics）

这是所有分析的第一层结构，用来**概括数据分布特征**。

常见指标包括：

* **均值（Mean）**
* **中位数（Median）**
* **标准差（Standard Deviation）**
* **方差（Variance）**
* **四分位数（Quartiles）**
* **分布密度**

常见可视化：

* 直方图
* 箱线图
* 密度图
* 散点图

在实验生物学中，例如：

* 基因表达量分布
* 蛋白浓度变化
* 细胞数量统计

这些通常先通过描述统计了解数据结构。

---

## 二、假设检验（Hypothesis Testing）

这是生物实验中**最经典的一类统计方法**，用于判断实验组和对照组是否存在显著差异。

最常见的方法包括：

### 1 t检验

* **Student's t-test**

用途：

* 比较两个样本均值

常见情境：

* 药物处理 vs 对照组
* 基因敲除 vs 野生型

类型：

* 独立样本 t-test
* 配对 t-test

---

### 2 非参数检验

当数据不满足正态分布假设时使用：

* **Mann–Whitney U test**
* **Wilcoxon signed-rank test**
* **Kruskal–Wallis test**

在小样本生物实验中非常常见。

---

### 3 卡方检验（Chi-square test）

用于**分类变量分析**：

例如：

* 基因型频率
* 表型比例
* 遗传分离比

---

## 三、方差分析（ANOVA）

当实验包含**多个组**时，通常使用方差分析。

常见类型：

### 单因素方差分析

* **One-way ANOVA**

例子：

比较三种培养条件下的细胞增殖率。

---

### 双因素方差分析

* **Two-way ANOVA**

用于研究：

* 两个因素
* 以及它们的交互作用

例如：

* 药物 × 时间
* 基因型 × 环境

---

## 四、回归分析（Regression）

回归模型是生物研究中**最重要的结构建模方法之一**。

### 1 线性回归

研究变量之间的线性关系：

例如：

* 基因表达 vs 年龄
* 蛋白浓度 vs 代谢速率

基本模型：

y = β0 + β1x + ε

---

### 2 逻辑回归（Logistic Regression）

用于**二分类结果**：

例如：

* 是否患病
* 是否表达某基因

在医学和流行病学中极其常见。

---

### 3 广义线性模型（GLM）

扩展线性模型，用于：

* count data
* binary data
* non-normal distributions

例如：

* Poisson regression（计数数据）

---

## 五、多变量统计（Multivariate Statistics）

随着高通量技术发展，这类方法在生物学中变得极其重要。

尤其是在：

* 基因组学
* 蛋白组学
* 代谢组学
* 神经科学

---

### 主成分分析（PCA）

用途：

* 降维
* 发现数据结构

例如：

RNA-seq 数据中寻找样本群体结构。

---

### 聚类分析（Clustering）

用于发现样本或基因的相似性结构：

常见方法：

* Hierarchical clustering
* k-means clustering

应用：

* 基因表达模式
* 细胞类型分类

---

### 判别分析

例如：

* LDA（Linear Discriminant Analysis）

用于：

* 分类
* 特征提取

---

## 六、贝叶斯统计（Bayesian Methods）

近年来在生物研究中越来越重要。

核心思想：

**概率表达不确定性**

基本公式：

P(θ|data) ∝ P(data|θ)P(θ)

---

典型应用：

* 系统生物学模型
* 进化树推断
* 单细胞数据分析
* 基因调控网络

例如：

* 贝叶斯网络
* MCMC推断

---

## 七、专门为生物数据发展的统计方法

由于生物数据有特殊结构，一些统计方法是**专门发展出来的**。

例如：

### 差异表达分析

用于：

* RNA-seq
* microarray

常用模型：

* negative binomial model

常用工具：

* DESeq2
* edgeR

---

### 多重检验校正

在基因组学中需要进行**成千上万次假设检验**。

因此必须进行校正：

* Bonferroni correction
* False Discovery Rate (FDR)

常用方法：

* Benjamini–Hochberg

---

### 生存分析（Survival Analysis）

在医学研究中常见。

方法包括：

* Kaplan–Meier curve
* Cox proportional hazards model

用于研究：

* 患者生存时间
* 疾病风险

---

# 一个结构性的理解

如果从**统计结构层级**来看，生物统计方法可以看成五层：

**Level 1 数据描述**

描述统计、可视化

**Level 2 差异检测**

t-test、ANOVA、非参数检验

**Level 3 关系建模**

回归、GLM

**Level 4 高维结构发现**

PCA、聚类、降维

**Level 5 概率模型**

贝叶斯模型、图模型

---

如果你的目标是构建 **agent-native scientific skills**，那么关键不只是列出统计方法，而是要把统计方法**重构成可组合、可调用、可推理的能力单元（capability units）**。
换句话说：**统计方法 ≠ agent skill**。
agent skill 是一种 **操作型能力（operational capability）**，它必须：

* 有清晰 **输入数据结构**
* 有明确 **统计假设**
* 有稳定 **输出结构**
* 能被 agent **自动决策是否调用**

因此，一个好的设计方式是把统计方法映射为 **Statistical Analysis Skills（统计分析技能体系）**。

下面给出一个适合 **AI-native science platform / agent runtime** 的设计框架。

---

# 一、Agent 统计技能的核心结构

每个 skill 都应该遵循统一 schema：

```
Skill {
  name
  description
  input_schema
  assumptions
  parameters
  output_schema
  interpretation_schema
}
```

例如：

```
skill: compare_two_groups_mean

input:
  dataset
  group_variable
  value_variable

assumptions:
  normal_distribution
  equal_variance

output:
  statistic
  p_value
  effect_size
  confidence_interval
```

关键是：
**输出必须是结构化的科学结果，而不是文本。**

---

# 二、第一类 Skill：数据描述（Data Characterization）

这是 agent 进行分析前的**环境感知能力**。

### 1 数据分布分析

```
skill: analyze_distribution
```

输入

* 数值变量

输出

* mean
* median
* variance
* skewness
* kurtosis
* normality_test

用途

agent 判断：

* 是否接近正态
* 是否需要非参数方法

---

### 2 数据质量评估

```
skill: assess_data_quality
```

输出

* missing_rate
* outlier_rate
* sample_size
* variance_structure

---

### 3 相关性扫描

```
skill: compute_pairwise_correlation
```

输出

* correlation_matrix
* p_values

适用于：

* 基因表达
* 神经元活动

---

# 三、第二类 Skill：差异分析（Differential Analysis）

生物研究最常见任务。

---

### 4 两组比较

```
skill: compare_two_groups
```

内部自动选择：

* t-test
* Mann–Whitney test

输入

```
dataset
group_variable
value_variable
```

输出

```
method_used
p_value
effect_size
confidence_interval
```

---

### 5 多组比较

```
skill: compare_multiple_groups
```

方法：

* ANOVA
* Kruskal–Wallis

输出

```
p_value
posthoc_tests
effect_sizes
```

---

### 6 差异表达分析

这是 **genomics 专用 skill**。

```
skill: differential_expression
```

输入

```
gene_expression_matrix
sample_groups
```

输出

```
gene_id
log2_fold_change
p_value
adjusted_p_value
```

---

# 四、第三类 Skill：关系建模（Relationship Modeling）

用于发现变量之间的结构关系。

---

### 7 线性关系建模

```
skill: fit_linear_model
```

模型：

y = β0 + β1x

输出

```
coefficients
p_values
r_squared
confidence_intervals
```

---

### 8 二分类预测

```
skill: logistic_regression
```

应用

* disease prediction
* phenotype classification

输出

```
odds_ratio
model_coefficients
auc
```

---

### 9 广义线性模型

```
skill: fit_glm
```

支持

* Poisson
* Binomial
* Gaussian

---

# 五、第四类 Skill：高维结构发现（High-Dimensional Structure Discovery）

这是 **omics / neuroscience** 的核心技能。

---

### 10 PCA

```
skill: principal_component_analysis
```

输出

```
principal_components
variance_explained
sample_coordinates
```

---

### 11 聚类

```
skill: cluster_samples
```

方法

* k-means
* hierarchical

输出

```
cluster_labels
cluster_centers
silhouette_score
```

---

### 12 降维（非线性）

```
skill: nonlinear_embedding
```

方法

* t-SNE
* UMAP

输出

```
embedding_coordinates
```

---

# 六、第五类 Skill：概率推断（Probabilistic Inference）

更高级的科学推理能力。

---

### 13 贝叶斯参数估计

```
skill: bayesian_parameter_estimation
```

输出

```
posterior_distribution
credible_interval
```

---

### 14 贝叶斯网络

```
skill: learn_bayesian_network
```

输出

```
graph_structure
conditional_probabilities
```

用于：

* gene regulatory networks

---

# 七、第六类 Skill：时间与生存分析

医学研究核心。

---

### 15 生存分析

```
skill: survival_analysis
```

方法

* Kaplan-Meier
* Cox regression

输出

```
survival_curve
hazard_ratio
p_value
```

---

# 八、Skill 层级结构（非常关键）

这些 skill 不应该是平铺的，而应该形成**结构稳定的能力层级**：

```
Level 1
Data Characterization
  analyze_distribution
  assess_data_quality

Level 2
Differential Analysis
  compare_two_groups
  compare_multiple_groups

Level 3
Relationship Modeling
  linear_model
  logistic_regression

Level 4
High-dimensional discovery
  PCA
  clustering
  embedding

Level 5
Probabilistic inference
  Bayesian models
  graphical models
```

这五层实际上就是：

**科学统计推理的结构稳定层级。**

---

# 九、关键设计原则（非常重要）

如果是 **agent-native skill system**，必须遵循三个原则。

---

## 1 方法抽象 > 工具抽象

不要设计

```
run_t_test
run_deseq2
run_pca
```

而要设计

```
compare_two_groups
differential_expression
discover_latent_structure
```

因为 agent 需要的是：

**任务能力（capability）**

而不是：

**软件命令（tool wrapper）**

---

## 2 自动方法选择

例如：

```
compare_two_groups
```

内部自动判断：

* 正态性
* 方差齐性

然后选择：

* t-test
* Welch test
* Mann–Whitney

---

## 3 输出必须是科学对象

而不是文本：

例如：

```
StatisticalResult
  test_type
  p_value
  effect_size
  confidence_interval
```

这样 agent 才能继续推理。

---

# 十、真正强大的 Skill：Scientific Question Skills

更高级的一层不是统计方法，而是：

```
detect_differential_signal
discover_clusters
infer_regulatory_relationships
identify_predictive_features
```

这些是：

**Goal-oriented scientific skills**

而统计方法只是其内部机制。

---
