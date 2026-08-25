# Robustness & Sensitivity Analysis Report

_Generated 2026-08-25 by `R/07_robustness.R`_

## Phase 11: Pooled panel robustness (2019-2024)

- Pooled panel: N = 809 country-year observations, 146 countries, country-clustered standard errors.
- GDP coefficient, primary cross-section (2019): 0.462 [0.212, 0.711]
- GDP coefficient, pooled panel (clustered SE): 0.497 [0.269, 0.726]
- Same direction: TRUE. 95% CIs overlap: TRUE.
- **Conclusion: the broad GDP-happiness association survives when re-estimated on the pooled multi-year sample with clustered standard errors.** This is a robustness check, not causal panel evidence -- no country fixed-effects model is used here, per the reasoning documented in `docs/DECISION_LOG.md` (the 3-year-rolling-average structure of Life Ladder means the relationship of interest is fundamentally a between-country comparison, which a fixed-effects specification would mostly absorb).

## Phase 12: Sensitivity analysis

Five pre-specified checks (not a search across arbitrary specifications):

| Specification | N | log(GDP) coefficient | 95% CI | Adj. R2 |
|---|---|---|---|---|
| Baseline (Model 3, N=144) | 144 | 0.462 | [0.212, 0.711] | 0.713 |
| Excluding Zimbabwe (highest Cook's D) | 143 | 0.443 | [0.190, 0.696] | 0.706 |
| Excluding all 7 Cook's-D-flagged observations | 137 | 0.458 | [0.202, 0.713] | 0.731 |
| HC1-robust SE (same point estimate as baseline) | 144 | 0.462 | [0.211, 0.713] | 0.713 |
| Alternate year: 2024 cross-section (N=133) | 133 | 0.409 | [0.136, 0.682] | 0.684 |

- Coefficient range across all checks: [0.409, 0.462].
- **Conclusion: the core finding is stable across all sensitivity checks.** The direction, approximate magnitude, and statistical significance of the log(GDP)-Life Ladder association are unaffected by excluding influential observations, by using heteroscedasticity-robust standard errors, or by moving to a different analysis year.
- No specification was excluded from this table after the fact; all five were pre-specified before fitting.
