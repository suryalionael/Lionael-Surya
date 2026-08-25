# Model Diagnostics Report

_Generated 2026-08-25 by `R/06_diagnostics.R`. Primary model: m3 (full main-effects model)_

## 1. Linearity & homoscedasticity

See `outputs/figures/diag_residuals_vs_fitted.png`. No strong systematic curvature is visible in the LOESS smooth, consistent with Phase 7's finding that a quadratic GDP term was not statistically or substantively justified.

## 2. Residual normality

- Shapiro-Wilk test: W = 0.9912, p = 0.5111 -- no evidence against normality of residuals
- See `outputs/figures/diag_qq_plot.png`.

## 3. Homoscedasticity

- Breusch-Pagan test: BP = 6.9076, df = 6, p = 0.3295 -- no evidence of heteroscedasticity
- See `outputs/figures/diag_scale_location.png`.
- No remedy needed.

## 4. Influence & leverage

- 7 of 144 observations exceed the conventional Cook's distance threshold (4/n = 0.0278). See `outputs/tables/diag_influential_observations.csv` and `outputs/figures/diag_cooks_distance.png` / `diag_leverage.png`.
- These observations are carried forward into the Phase 12 sensitivity analysis (re-fitting the model with them excluded) rather than dropped here -- an observation with a large Cook's distance is not automatically an error.

## 5. Multicollinearity

| Term | VIF |
|---|---|
| log_gdp_pc | 8.49 |
| life_expectancy | 4.42 |
| unemployment_pct | 1.07 |
| internet_use_pct | 8.74 |
| urban_pop_pct | 2.79 |
| inflation_pct | 1.03 |

- Maximum VIF = 8.74 -- some predictors show elevated but not severe collinearity (conventional concern threshold: VIF > 5, some references use >10)

## Summary

- Normality: no evidence against
- Homoscedasticity: holds
- Influential observations: 7 flagged, retained and tested in sensitivity analysis (Phase 12)
- Multicollinearity: some elevated VIF, documented
- None of these issues change the modeling conclusions materially (see `outputs/tables/sensitivity_analysis.csv` from Phase 12 for confirmation).
