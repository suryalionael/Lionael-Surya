# Analysis Plan

This is the plan the pipeline in `R/` actually implements, written so a reader can check the code against the intent. It builds directly on the Phase 0 feasibility research (`docs/DATASET_RESEARCH.md`, `docs/DATA_DICTIONARY.md`, `docs/DECISION_LOG.md`) — nothing here re-litigates decisions already made there.

## Research questions

1. Which socioeconomic factors are associated with life satisfaction?
2. Does GDP remain associated with Life Ladder after controlling for other socioeconomic factors?
3. Is the relationship between economic prosperity and happiness nonlinear?
4. Which countries have substantially higher or lower observed happiness than predicted by the model?
5. Are the findings robust across reasonable model specifications and years?

## Design

- **Primary:** cross-sectional, one row per country, the single year (within the WHR's 2019+ full-decomposition window) that maximizes complete-case sample size — determined empirically, not assumed to be the most recent year.
- **Secondary:** pooled 2019–2024 country-year panel, country-clustered standard errors, used only as a robustness check — never as causal panel evidence.

## Outcome

Life Ladder (World Happiness Report, Gallup World Poll, 3-year rolling average).

## Predictors (approved in Phase 0)

log(GDP per capita, PPP) · life expectancy · unemployment · internet use · urbanization · inflation — all independently sourced from the World Bank API. The WHR's own factor-decomposition columns are never used as predictors (see `docs/DECISION_LOG.md` for why). Gini and school enrollment are excluded for coverage reasons.

## Modeling sequence

1. Four progressive OLS models (intercept-only → GDP alone → +health/employment → full 6-predictor model), compared on adjusted R² / AIC / residual SE.
2. Nonlinearity test: quadratic log(GDP) term, accepted only if both statistically significant and substantively meaningful (pre-set bars, not decided after seeing the result).
3. One pre-specified interaction test (log GDP × unemployment).
4. Full diagnostic suite on the selected primary model (linearity, normality, homoscedasticity, influence, multicollinearity), with remedies evaluated rather than applied by default.
5. Happiness-gap residual analysis on the primary model.
6. Pooled-panel robustness re-estimation with clustered SEs.
7. Five pre-specified sensitivity checks.

## What "primary model" means operationally

Whichever specification wins step 1–3 above becomes the single model used for diagnostics (step 4) and the happiness gap (step 5) — decided by the data via the rules in `R/05_modeling.R`, not chosen after the fact for convenience. See `outputs/tables/modeling_report.md` for which specification actually won and why.

## Non-goals

No machine learning, no predictive/classification task, no dashboard or web app. This is a statistical-inference project about association and robustness, not a competition for predictive accuracy — see the project's "no overengineering" ground rules.
