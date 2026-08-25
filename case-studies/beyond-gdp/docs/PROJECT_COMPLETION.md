# Project Completion Report

**Project:** Beyond GDP — A Statistical Investigation into the Economics of Happiness
**Status:** Complete
**Date:** 2026-08-24

---

## 1. Final research question

"Does being richer actually make people happier?" — investigated alongside four related questions (which socioeconomic factors are associated with life satisfaction; does GDP survive controlling for them; is the relationship nonlinear; which countries deviate most from what the model predicts; and are the findings robust). See `docs/ANALYSIS_PLAN.md`.

## 2. Final dataset

- **Sources:** World Happiness Report 2026 (Life Ladder, official free download) + World Bank Open Data (six independently-sourced predictors, official API). No Kaggle, no scraped data, no unofficial mirrors, at any stage.
- **Primary design:** cross-sectional, one row per country, **year 2019** — selected because it maximizes complete-case sample size among the years the WHR provides its full decomposition (2019+), not because it's the most recent year. See `outputs/tables/analytical_dataset_report.md`.
- **Primary analytical N:** 144 countries (7 excluded for missing predictor data: Kosovo, Tajikistan, Turkmenistan, Venezuela, DR Congo, Yemen, South Sudan).
- **Secondary design:** pooled 2019–2024 panel, 809 country-year observations, 146 countries, used only for robustness (not causal panel evidence).

## 3. Final model

```
Life Ladder ~ log(GDP per capita, PPP) + Life expectancy + Unemployment
             + Internet use + Urban population + Inflation
```

- **Adjusted R²:** 0.713
- **Residual SE:** 0.591
- **N:** 144

| Predictor | Coefficient | 95% CI | p-value |
|---|---|---|---|
| log(GDP per capita) | 0.462 | [0.212, 0.711] | < 0.001 |
| Unemployment (%) | −0.054 | [−0.072, −0.036] | < 0.001 |
| Urban population (%) | 0.010 | [0.002, 0.018] | 0.010 |
| Inflation (%) | −0.005 | [−0.010, −0.001] | 0.022 |
| Life expectancy | 0.009 | [−0.015, 0.033] | 0.454 (n.s.) |
| Internet use (%) | 0.004 | [−0.007, 0.014] | 0.465 (n.s.) |

A quadratic GDP term (p = 0.222) and a GDP × unemployment interaction (p = 0.259) were formally tested and rejected — not included in the final specification.

## 4. Key statistical findings

- GDP per capita is positively and significantly associated with Life Ladder, and this survives controlling for five other socioeconomic factors — see `docs/FINDINGS.md`, Finding 1.
- Unemployment, urbanization, and inflation are also independently associated with Life Ladder; life expectancy and internet use lose significance once GDP is controlled for, consistent with real multicollinearity (VIF ≈ 8.5–8.7) documented in diagnostics — Finding 2.
- No evidence of a nonlinear "diminishing returns" GDP relationship, and no evidence of a GDP × unemployment interaction — both formally tested and rejected, not merely unexamined — Findings 3–4.
- Model diagnostics found no violations of normality or homoscedasticity; one influential observation (Zimbabwe, driven by 255% inflation) was identified, retained, and shown not to change the conclusions — Finding 7.

## 5. Happiness-gap findings

**Top positive gaps** (observed Life Ladder well above what the model predicts): Finland (+1.36), Costa Rica (+1.31), Pakistan (+1.06), Nicaragua (+1.04), Uzbekistan (+1.01), Congo (+1.01), Honduras (+0.93), Guatemala (+0.91).

**Top negative gaps** (observed well below predicted): Hong Kong SAR of China (−1.51), Botswana (−1.36), Afghanistan (−1.34), India (−1.23), Tanzania (−1.12), Egypt (−1.06), Ukraine (−1.05), Bulgaria (−1.03).

Framed throughout as unexplained model residuals, never as a verdict on which countries are "truly" happier — see `docs/FINDINGS.md`, Finding 5, and the explicit caveats in `outputs/tables/happiness_gap_report.md`.

## 6. Robustness findings

The GDP coefficient ranged from **0.409 to 0.497** across: the baseline model, exclusion of the single most influential observation, exclusion of all 7 Cook's-distance-flagged observations, heteroscedasticity-robust standard errors, an alternate analysis year (2024), and an independent re-estimation on the 2019–2024 pooled panel with country-clustered standard errors (146 countries, 809 observations). Every specification agreed on direction and statistical significance. **The central finding did not survive by accident of a single model choice.**

## 7. Major limitations

Thirteen documented in full in `docs/LIMITATIONS.md`; the most consequential:

- Observational, cross-sectional data — associations only, never causal claims.
- Country-level data — no individual-level inference is supported.
- The model omits social support, trust, and inequality, since Phase 0 found no adequate free/independent data source for them.
- GDP and internet use are collinear enough (VIF ≈ 8.5–8.7) that internet use's independent association, if any, cannot be cleanly isolated.
- Life Ladder (3-year rolling average) is matched to single-year World Bank predictors — a structural mismatch that motivated the cross-sectional-first design over a strict annual panel.

## 8. Reproducibility status

**Verified, not just claimed.** The entire pipeline was actually torn down and rebuilt from scratch during this project:

```
rm -rf data/raw/* data/processed/* outputs/figures/* outputs/tables/* outputs/models/*
Rscript scripts/run_all.R   # re-downloads from official APIs, rebuilds everything
Rscript tests/testthat.R    # re-run after rebuild
```

Result: identical analytical sample size (N=144), identical GDP coefficient (0.4617 to 4 decimal places), identical happiness-gap rankings, all 19 figures and 27 tables regenerated, all tests passing. `renv.lock` pins exact package versions; `renv::restore()` reproduces the environment on a fresh machine.

## 9. Test count

**19 `test_that()` blocks across 4 test files, 38 individual expectations, 0 failures, 0 skipped** (run against the fully rebuilt pipeline). Covers: expected columns, unique grain, no duplicate country-year rows, valid Life Ladder range, GDP > 0 and log(GDP) finite before/after transformation, expected join behavior (ISO3 always resolved, always 3 characters), sample size within the documented range, model coefficients present, predictions finite, happiness gap = observed − predicted exactly, no duplicated country rankings, and sensitivity-analysis directional stability.

## 10. Files created

- **9 R scripts** (`R/00_config.R` through `R/08_findings.R`) + `scripts/run_all.R`
- **7 project docs** (`docs/DATASET_RESEARCH.md`, `DATA_DICTIONARY.md`, `DECISION_LOG.md`, `ANALYSIS_PLAN.md`, `FINDINGS.md`, `STATISTICAL_METHODS.md`, `LIMITATIONS.md`) + this completion report
- **4 raw data files** + **5 processed data files**
- **19 figures**, **27 tables/reports**, **6 saved model objects**
- **4 test files** (19 test blocks / 38 expectations)
- `README.md`, `renv.lock`, `.gitignore`, `.Rprofile`, `Beyond-GDP.Rproj`

## 11. Unresolved issues

None blocking. Two items are documented as known, accepted limitations rather than defects:

- GDP–internet-use multicollinearity (VIF ≈ 8.5–8.7) limits how finely the model can separate their independent contributions — documented in Findings 2 and 7 and in Limitations §12, not hidden.
- The primary cross-section year (2019) is six years old as of this writing, a direct consequence of post-2019 data-coverage decline (likely pandemic-related) rather than a choice for convenience — documented in `outputs/tables/analytical_dataset_report.md` and `docs/STATISTICAL_METHODS.md`.

## 12. Recommended portfolio presentation

Lead with `README.md` (the question, the key findings, the honest robustness/limitations framing) and the happiness-gap ranked bar chart (`outputs/figures/happiness_gap_ranked_bars.png`) as the visual hook — it's the most immediately legible result. For a technical interviewer, `docs/STATISTICAL_METHODS.md` and `docs/FINDINGS.md` demonstrate the statistical reasoning directly; the WHR-decomposition-circularity finding in `docs/DECISION_LOG.md` is worth calling out specifically in an interview, since it's the one methodological decision in this project least likely to appear in a typical tutorial treatment of this dataset.
