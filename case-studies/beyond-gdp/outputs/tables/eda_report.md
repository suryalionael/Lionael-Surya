# Exploratory Data Analysis Report

_Generated 2026-08-25 by `R/04_eda.R`. Primary cross-section, year=2019, N=144 countries._

## Raw vs. log GDP per capita

- Raw GDP per capita skewness: 1.48 (strongly right-skewed -- a small number of very high-income countries stretch the distribution)
- log(GDP per capita) skewness: -0.36 (much closer to symmetric)
- The Life Ladder vs. raw-GDP scatterplot bunches most countries into a narrow low-GDP band with a long right tail of high-income outliers, while the log-GDP scatterplot spreads observations more evenly and shows a visibly more linear relationship with Life Ladder. This is the empirical (not just theoretical) justification for using log(GDP) in every model in this project.

## Outliers

- 10 observation-variable pairs were flagged at |z| > 2.5 (see `outputs/tables/eda_outliers_flagged.csv`). None were removed -- each reflects a real, plausible country-level condition (e.g., a small oil-rich state with extreme GDP per capita, or a country experiencing high inflation), not a data-entry error. These are retained through modeling and revisited in the diagnostics phase (Cook's distance, leverage) to see whether any exert disproportionate influence on the regression -- being an outlier in one variable's distribution does not automatically mean an observation distorts the model.

## Correlation structure

See `outputs/figures/eda_correlation_matrix.png` and `outputs/tables/eda_correlation_matrix.csv`. Notable pairwise correlations are interpreted in `docs/FINDINGS.md`; multicollinearity among predictors is formally assessed via VIF in the diagnostics phase, not just from this matrix.
