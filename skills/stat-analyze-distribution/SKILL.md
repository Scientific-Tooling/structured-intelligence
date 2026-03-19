---
name: stat-analyze-distribution
description: Characterize the distribution of one or more numeric variables with summary statistics, normality tests, and diagnostic plots.
---

# Skill: Statistical Distribution Analysis

## Use When

- User wants to understand the distribution of a numeric variable before choosing a statistical test
- User needs to check whether data is approximately normally distributed
- User wants summary statistics (mean, median, variance, skewness, kurtosis) for one or more columns
- User is preparing an EDA (exploratory data analysis) report

## Inputs

- Required:
  - Data table (CSV or TSV) with at least one numeric column
- Optional:
  - Column(s) to analyze (default: all numeric columns)
  - Normality test method: `shapiro` (default, n ≤ 5000) or `anderson` (Anderson-Darling, recommended for larger samples)
  - Output directory (default: `./dist_output`)

## Workflow

1. Read the data file; identify numeric columns to analyze (or use user-specified subset).
2. For each target column, compute summary statistics: mean, median, standard deviation, variance, min, max, 25th/75th percentiles, skewness, kurtosis.
3. Run normality test:
   - Shapiro-Wilk when n ≤ 5000
   - Anderson-Darling when n > 5000
   Report test statistic, p-value (or significance level where applicable), and sample size.
4. Classify each variable as `approximately_normal` or `non_normal` using both test output and Q-Q plot inspection (do not classify from hypothesis-test p-value alone).
5. Generate plots for each variable: histogram with density overlay, Q-Q plot.
6. If multiple variables, produce a summary table across all variables.
7. Write summary statistics table (TSV) and plots (PDF) to output directory.
8. Save an executable analysis script (`analysis_code.py` or `analysis_code.R`) and software version manifest (`session_info.txt`) used to produce results.
9. Report which variables appear normally distributed and suggest appropriate downstream tests.

## Output Contract

- Summary statistics table (TSV): variable, n, mean, median, sd, variance, skewness, kurtosis, normality_test, test_statistic, p_value_or_significance, normality_call
- Histogram + density plot per variable (PDF)
- Q-Q plot per variable (PDF)
- Reproducibility artifacts: `analysis_code.py` or `analysis_code.R`, plus `session_info.txt`

## Limits

- Shapiro-Wilk test is unreliable for very large n; use Anderson-Darling and visual diagnostics instead.
- Avoid one-sample KS tests against a fitted normal distribution unless a corrected procedure is explicitly implemented.
- Normality tests have low power for small samples (n < 20); visual inspection of Q-Q plot is recommended.
- Does not handle categorical or date columns; these are silently skipped.
- Common failure: non-numeric columns passed explicitly cause an error — pre-filter if needed.
