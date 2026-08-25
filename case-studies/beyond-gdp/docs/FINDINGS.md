# Findings

**Project:** Beyond GDP — A Statistical Investigation into the Economics of Happiness
**Primary dataset:** cross-sectional, N = 144 countries, 2019 (see `docs/ANALYSIS_PLAN.md` for why 2019, not the most recent year)
**Primary model:** `Life Ladder ~ log(GDP per capita) + life expectancy + unemployment + internet use + urbanization + inflation`

All statistics below are read directly from the generated outputs in `outputs/tables/` and `outputs/figures/` — none are asserted from memory. Re-run `Rscript scripts/run_all.R` to reproduce every number here.

---

## Finding 1 — GDP per capita is associated with Life Ladder, and the association survives controlling for other factors

**Question:** Does GDP remain associated with Life Ladder after controlling for other socioeconomic factors?

**Evidence:** `outputs/tables/gdp_coefficient_stability.csv`, `outputs/figures/model_gdp_coefficient_stability.png`, `outputs/tables/model3_coefficients.csv`

**Statistical result:** The log(GDP per capita) coefficient is 0.768 [0.670, 0.865] in the bivariate model (Model 1), shrinks to 0.653 [0.475, 0.832] once life expectancy and unemployment are added (Model 2), and settles at 0.462 [0.212, 0.711], p < 0.001, in the full six-predictor model (Model 3). It remains statistically significant and substantively large at every step.

**Interpretation:** Roughly a doubling of GDP per capita (a ~0.69 increase in log-GDP) is associated with about a 0.32-point increase in Life Ladder (0.462 × 0.69), holding the other five predictors constant — a meaningful shift on a 0–10 scale. The coefficient shrinking as more covariates are added is expected (GDP is correlated with the other predictors) and does not indicate the relationship is spurious; it stabilizes rather than collapsing to zero.

**Limitation:** This is an **association**, not a causal effect. The data are observational and cross-sectional; GDP could partly proxy for institutional quality, historical development, or other unmeasured factors. See `docs/LIMITATIONS.md`.

---

## Finding 2 — Unemployment, urbanization, and inflation are independently associated with Life Ladder; life expectancy and internet use are not, once GDP is in the model

**Question:** Which socioeconomic factors are associated with life satisfaction?

**Evidence:** `outputs/tables/model3_coefficients.csv`, `outputs/figures/model_coefficient_plot.png`, `outputs/tables/eda_correlation_matrix.csv`

**Statistical result (Model 3, full main-effects model):**

| Predictor | Coefficient | 95% CI | p-value |
|---|---|---|---|
| log(GDP per capita) | 0.462 | [0.212, 0.711] | < 0.001 |
| Unemployment (%) | −0.054 | [−0.072, −0.036] | < 0.001 |
| Urban population (%) | 0.010 | [0.002, 0.018] | 0.010 |
| Inflation (%) | −0.005 | [−0.010, −0.001] | 0.022 |
| Life expectancy | 0.009 | [−0.015, 0.033] | 0.454 |
| Internet use (%) | 0.004 | [−0.007, 0.014] | 0.465 |

**Interpretation:** Unemployment has a clearly independent negative association with Life Ladder — and is more precisely estimated (tighter CI) than any predictor besides GDP. Urbanization and inflation are also independently associated, in the expected directions, though with smaller effect sizes. Life expectancy and internet use, despite each having a strong *zero-order* correlation with Life Ladder (r = 0.73 and r = 0.76 respectively — see `outputs/tables/eda_correlation_matrix.csv`), lose statistical significance once GDP and the other predictors are in the model. This is consistent with the multicollinearity documented in Phase 9 (VIF = 4.4 for life expectancy, VIF = 8.7 for internet use — see `outputs/tables/diag_vif.csv`): these variables move so closely with GDP across countries that the model cannot cleanly separate their independent contribution from GDP's.

**Limitation:** "Not statistically significant once GDP is controlled for" is not the same as "irrelevant to happiness" — it means this dataset cannot separate their unique contribution from GDP's shared variance. A larger or differently-structured sample might resolve this.

---

## Finding 3 — No support for a nonlinear ("diminishing returns" or "threshold") relationship between GDP and Life Ladder in this model

**Question:** Is the relationship between economic prosperity and happiness nonlinear?

**Evidence:** `outputs/figures/model_nonlinearity_gdp.png`, `outputs/tables/modeling_report.md`

**Statistical result:** Adding a quadratic log(GDP)² term to the full model produced a coefficient with p = 0.222 (nested F-test also non-significant), and the predicted Life Ladder curves from the linear and quadratic specifications diverge by at most 0.27 points across the entire observed GDP range.

**Interpretation:** This is a **null finding, reported as such rather than discarded.** The visual EDA (raw-scale scatterplot) suggested a possible flattening at very high GDP, but that impression does not survive formal testing once GDP is log-transformed and other predictors are controlled — the log transformation itself already captures most of the "diminishing returns" pattern, leaving little room for an additional quadratic term to matter. No "happiness plateau" or "wealth threshold" claim is supported by this analysis.

**Limitation:** Statistical power for detecting nonlinearity in a 144-country cross-section is limited, especially at the sparse high-GDP tail (Luxembourg, Singapore, Ireland — see the outlier notes in `docs/LIMITATIONS.md`). Absence of evidence is not strong evidence of absence here.

---

## Finding 4 — No evidence that unemployment moderates the GDP-Life Ladder relationship

**Question:** Does social/economic context change the strength of the GDP-happiness association? (Phase 8)

**Evidence:** `outputs/tables/modeling_report.md`

**Statistical result:** The log(GDP) × unemployment interaction term has p = 0.259.

**Interpretation:** Another honest null finding. Only one interaction was tested — chosen in advance for conceptual relevance, not selected after searching multiple combinations for significance — and it did not clear the significance bar. This is documented and not carried forward as a headline result.

**Limitation:** The project's approved predictor set does not include a genuine social-support measure (Phase 0 found WHR's own social-support variable is not independently available — see `docs/DECISION_LOG.md`), so this test cannot speak to the more commonly hypothesized "does social support buffer the income-happiness link" question at all — only to unemployment as a much narrower proxy for economic hardship.

---

## Finding 5 — The Happiness Gap: several Latin American countries score well above what the model predicts; several high-income East Asian economies score below

**Question:** Which countries have substantially higher or lower observed happiness than predicted by the model?

**Evidence:** `outputs/tables/happiness_gap_full_ranking.csv`, `outputs/figures/happiness_gap_ranked_bars.png`, `outputs/figures/happiness_gap_predicted_vs_observed.png`

**Statistical result:** Largest positive residuals: Finland (+1.36), Costa Rica (+1.31), Pakistan (+1.06), Nicaragua (+1.04), Uzbekistan (+1.01), Congo (+1.01), Honduras (+0.93), Guatemala (+0.91). Largest negative residuals: Hong Kong SAR of China (−1.51), Botswana (−1.36), Afghanistan (−1.34), India (−1.23), Tanzania (−1.12), Egypt (−1.06), Ukraine (−1.05), Bulgaria (−1.03), Japan (−0.94).

**Interpretation:** Several Central/Latin American countries (Costa Rica, Nicaragua, Honduras, Guatemala, El Salvador) report noticeably higher Life Ladder scores than their GDP, health, employment, and other measured conditions alone would predict — a pattern also remarked on in the World Happiness Report's own commentary and in academic work on regional social/family cohesion. Several high-income East Asian/Gulf economies (Hong Kong, Japan, Singapore, Republic of Korea, Kuwait, Bahrain) score *below* what their strong socioeconomic indicators predict.

**These are residuals under one specific six-variable model — unexplained variation, not a measure of "true" national happiness or well-being.** A country's gap says only that its reported life evaluation is not fully accounted for by GDP, life expectancy, unemployment, internet use, urbanization, and inflation. It is not evidence about *why*, since the model has no social-support, trust, or cultural variable to test candidate explanations directly. See the explicit framing note in `outputs/tables/happiness_gap_report.md`.

**Limitation:** Rankings in the middle of the distribution are not precisely stable across model specifications (see Finding 6); only the broad top/bottom groupings should be treated as a reasonably stable pattern.

---

## Finding 6 — The core GDP finding is robust across five sensitivity checks and a pooled multi-year panel

**Question:** Are the findings robust across reasonable model specifications and years?

**Evidence:** `outputs/tables/sensitivity_analysis.csv`, `outputs/figures/sensitivity_analysis.png`, `outputs/tables/robustness_gdp_coefficient_comparison.csv`, `outputs/figures/robustness_gdp_coefficient_comparison.png`

**Statistical result:** The log(GDP) coefficient stays in a narrow band — [0.409, 0.497] — across: the baseline model, excluding the single most influential observation (Zimbabwe), excluding all 7 Cook's-distance-flagged observations, using heteroscedasticity-robust standard errors, using an alternate analysis year (2024), and re-estimating on the pooled 2019–2024 panel (146 countries, 809 country-year observations) with country-clustered standard errors (0.497 [0.269, 0.726]). Every specification agrees on direction and statistical significance.

**Interpretation:** The central finding — a positive, significant association between GDP and Life Ladder that survives controlling for health, employment, connectivity, urbanization, and inflation — is not an artifact of the specific year chosen, a handful of unusual countries, or the standard-error method. This is a meaningfully stronger evidentiary basis than a single cross-sectional regression alone would provide.

**Limitation:** The pooled panel result is explicitly a robustness check, **not causal panel evidence** — no country fixed-effects model is used, and no claim is made about within-country change over time (see `docs/DECISION_LOG.md` for the reasoning). Both designs remain observational and cross-country in nature.

---

## Finding 7 — Model diagnostics reveal no major violations, but real multicollinearity between GDP and internet use

**Question:** Is the primary model statistically well-behaved?

**Evidence:** `outputs/tables/diagnostics_report.md`, `outputs/tables/diag_vif.csv`, `outputs/figures/diag_residuals_vs_fitted.png`, `outputs/figures/diag_qq_plot.png`, `outputs/figures/diag_scale_location.png`

**Statistical result:** Shapiro-Wilk test for residual normality: p = 0.511 (no evidence against normality). Breusch-Pagan test for heteroscedasticity: p = 0.330 (no evidence of heteroscedasticity). Maximum VIF = 8.74 (internet use), 8.49 (log GDP) — both above the conventional VIF > 5 concern threshold; all other predictors have VIF < 4.5.

**Interpretation:** The model's residuals behave well (normal, constant variance), so no standard-error correction was needed (confirmed unnecessary directly, not assumed — see the HC1-robust-SE sensitivity check in Finding 6, which shows it changes nothing). The elevated VIF for GDP and internet use is a real, reportable limitation: it is the statistical signature of Finding 2 (internet use loses significance once GDP is controlled for) and means the model cannot fully disentangle "wealthy" from "digitally connected" in this sample.

**Limitation:** One observation (Zimbabwe, Cook's distance = 1.20, driven by 255% inflation) has outsized influence on the fitted model. It is retained (not deleted — its extreme inflation is a real, documented economic condition, not a data error), and Finding 6 shows the core conclusions are unchanged whether it is included or excluded.
