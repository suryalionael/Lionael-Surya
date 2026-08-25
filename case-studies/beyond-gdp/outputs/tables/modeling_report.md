# Modeling Report

_Generated 2026-08-25 by `R/05_modeling.R`. N=144 countries, year=2019._

## Progressive models (Phase 6)

| Model | Formula | N | Adj. R2 | AIC | Residual SE |
|---|---|---|---|---|---|
| m0 | `life_ladder ~ 1` | 144 | 0.000 | 439.7 | 1.102 |
| m1 | `life_ladder ~ log_gdp_pc` | 144 | 0.628 | 298.1 | 0.672 |
| m2 | `life_ladder ~ log_gdp_pc + life_expectancy + unemployment_pct` | 144 | 0.689 | 274.5 | 0.615 |
| m3 | `life_ladder ~ log_gdp_pc + life_expectancy + unemployment_pct +      internet_use_pct + urban_pop_pct + inflation_pct` | 144 | 0.713 | 265.8 | 0.591 |

log(GDP per capita) alone explains a large share of cross-country variance; adding life expectancy, unemployment, and the remaining covariates improves fit further but with diminishing returns (see adjusted R2 / AIC above), and the log(GDP) coefficient stays in a similar range across specifications (see `outputs/figures/model_gdp_coefficient_stability.png`) -- consistent with, but not proof of, a robust association rather than one driven by omitted-variable confounding from the specific covariates tested here.

## Nonlinearity test (Phase 7)

- Quadratic term (log GDP squared): estimate = 0.0486, p = 0.2219
- Nested F-test (linear vs. quadratic): F = 1.51, p = 0.2219
- Max divergence in predicted Life Ladder across the observed GDP range: 0.266 (0-10 scale)
- **Decision: Linear log(GDP) specification retained as the primary model.** The quadratic term did not clear both the statistical-significance and substantive-magnitude bars set in advance, so no 'happiness threshold' claim is made.

## Interaction test (Phase 8)

Only one interaction was tested (log(GDP) x unemployment), chosen for conceptual relevance and because both terms are in the approved predictor set -- not selected by searching many combinations for significance.

- Interaction term estimate = 0.0141, SE = 0.0125, p = 0.2589
- **Decision: Interaction not statistically significant at the 0.05 level; documented here and not carried forward as a headline finding, per the no-fishing rule set in advance.**

## Primary model selected for diagnostics and the happiness-gap analysis

**m3 (full main-effects model)**

All coefficients in this project are interpreted as **associations**, not causal effects -- this is observational, cross-sectional, country-level data (see `docs/LIMITATIONS.md`).
