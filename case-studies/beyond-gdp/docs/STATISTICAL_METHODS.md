# Statistical Methods

**Audience:** written for a Data Analyst hiring manager or recruiter — no advanced statistics background assumed, but no dumbing-down of what was actually done either.

---

## Study design

This project is a **cross-sectional, country-level, observational** study. That phrase matters, so here's what each word means for what the results can and cannot say:

- **Cross-sectional:** the primary analysis compares different countries to each other at one point in time (2019 — see "Why 2019" below), not the same country over time.
- **Country-level:** every row is a country, not a person. A result like "GDP is associated with Life Ladder" describes a pattern *across countries*, and says nothing about whether a given individual would be happier with more money (that would be an "ecological fallacy" if claimed — see `docs/LIMITATIONS.md`).
- **Observational:** nothing was experimentally manipulated. Countries were not randomly assigned different GDP levels. This rules out causal language throughout the project — every result is described as an **association**, never as GDP "causing" happiness.

### Why a single year, and why 2019 specifically

The World Happiness Report's Life Ladder score is a 3-year rolling average, which is a different kind of measurement than World Bank's single-year annual indicators (see `docs/DATASET_RESEARCH.md` §9 for the full reasoning). Rather than force these together into a panel and treat year-to-year movement as meaningful, the primary design uses one cross-section. The year itself was **not** picked because it's the most recent — it was picked because it has the largest number of countries with complete data on every required variable (144 countries in 2019, versus 128–140 in other years — see `outputs/tables/analytical_dataset_report.md`). 2020–2024 all have smaller complete-case samples, likely reflecting pandemic-era disruption to national statistical reporting.

---

## Outcome variable

**Life Ladder** (also called the Cantril Ladder): a 0–10 self-reported life-evaluation score from the Gallup World Poll, published by the World Happiness Report as a 3-year rolling average per country.

## Predictors

Six independently-sourced World Bank indicators (see `docs/DATA_DICTIONARY.md` for exact definitions and why each was included/excluded):

- **log(GDP per capita, PPP)** — logged, not raw. See "Why log GDP" below.
- **Life expectancy at birth**
- **Unemployment rate**
- **Internet use (% of population)**
- **Urban population (%)**
- **Inflation (annual % change in consumer prices)**

Two variables World Happiness Report tutorials commonly use — the Gini index and secondary school enrollment — were deliberately excluded because their World Bank data coverage is too incomplete (33% and 65% of country-years respectively) to include without cutting the usable sample roughly in half. Full reasoning in `docs/DECISION_LOG.md`.

**A methodological note that matters more than it might look:** the World Happiness Report's own free download includes six "Explained by:" columns that look like they could be predictors (GDP, social support, health, freedom, generosity, corruption). They are not used here. Those columns are the report's own regression *output* — they were verified in this project to sum exactly to the Life Ladder score by construction (see `docs/DECISION_LOG.md`). Using them as predictors of Life Ladder would be close to circular. Every predictor in this project's models comes independently from the World Bank instead.

### Why log(GDP), not raw GDP

Raw GDP per capita is strongly right-skewed (skewness = 1.48 in this sample) — a handful of very high-income countries (Luxembourg, Singapore, Ireland) stretch the scale, bunching most countries into a narrow low-to-middle range. Log-transforming GDP reduces the skew to near-symmetric (skewness = −0.36) and produces a visibly more linear relationship with Life Ladder (compare the two panels in `outputs/figures/eda_life_ladder_vs_gdp_raw_and_log.png`). This is standard practice in the happiness-economics literature (it is how the World Happiness Report itself treats GDP) and is empirically justified here, not just assumed.

---

## Multiple regression

The primary model is ordinary least squares (OLS) multiple linear regression:

```
Life Ladder ~ log(GDP per capita) + Life expectancy + Unemployment
              + Internet use + Urban population + Inflation
```

Four models were fit in increasing order of complexity (intercept-only → GDP alone → GDP + health + employment → the full model above), and compared on adjusted R², AIC, and residual standard error — not on R² alone, since R² mechanically increases with every added variable regardless of whether it's justified. See `outputs/tables/model_comparison_0_to_3.csv`.

## Nonlinear extension

A quadratic term, log(GDP)², was added to test whether the GDP–happiness relationship flattens or reverses at high income (a commonly hypothesized "diminishing returns" pattern). It was tested with a nested F-test and evaluated against two pre-set bars — statistical significance **and** a minimum practical size of effect — before being accepted or rejected. It did not clear the statistical bar (p = 0.222), so the simpler linear specification was kept. See `docs/FINDINGS.md`, Finding 3.

## Interaction term

One interaction — log(GDP) × unemployment — was tested to see whether the GDP–happiness association differs by labor-market conditions. It was not statistically significant (p = 0.259) and was not carried forward as a headline result. Only this single interaction was tested, decided in advance, to avoid "fishing" for a significant result across many possible combinations.

---

## Model diagnostics

Every assumption behind OLS regression was checked directly on the primary model, not assumed to hold:

| Assumption | Test / plot | Result |
|---|---|---|
| Linearity | Residuals vs. fitted plot | No systematic curvature |
| Normal residuals | Shapiro-Wilk test, Q-Q plot | p = 0.511 — no evidence against normality |
| Constant variance (homoscedasticity) | Breusch-Pagan test, scale-location plot | p = 0.330 — no evidence of heteroscedasticity |
| No excessive influence | Cook's distance, leverage | 7 of 144 observations flagged; retained and separately tested (see "Sensitivity analysis" below) |
| No severe multicollinearity | Variance Inflation Factor (VIF) | GDP and internet use both exceed the conventional VIF > 5 threshold — reported directly as a limitation, not hidden |

## Confidence intervals and effect sizes

Every coefficient in this project is reported with a 95% confidence interval, not just a p-value or a "significant/not significant" label. A CI communicates both the estimated size of an association and how precisely it's been pinned down — e.g., "each doubling of GDP per capita is associated with roughly a 0.2–0.5 point increase in Life Ladder" is a more honest and more useful statement than "GDP is significant (p < 0.001)."

## Robust and clustered standard errors

Because the Breusch-Pagan test found no heteroscedasticity, heteroscedasticity-robust (HC1) standard errors were **not** applied as the default reporting method for the primary model — only tested as one of five sensitivity checks, to confirm directly that they wouldn't have changed anything (they don't). This follows the project rule of not applying a remedy reflexively when the diagnostic that would justify it comes back clean.

For the secondary pooled-panel robustness check (below), country-clustered standard errors *are* used, because that data structure genuinely violates the independence assumption (the same country contributes up to 6 rows).

## Pooled panel robustness check (secondary design)

The World Happiness Report and World Bank data were also combined into a 2019–2024 pooled panel (809 country-year observations, 146 countries) and the same regression re-estimated with standard errors clustered by country. This is used **only** to check whether the primary cross-sectional finding survives being re-estimated on a larger, multi-year sample — it is explicitly **not** presented as causal panel evidence, and no country fixed-effects model is used (see `docs/DECISION_LOG.md` for why a fixed-effects design would not suit this particular data). The GDP coefficient in the pooled model (0.497, 95% CI [0.269, 0.726]) closely matches the cross-sectional estimate (0.462, 95% CI [0.212, 0.711]).

## Sensitivity analysis

Five pre-specified checks (decided before fitting, not selected afterward) tested whether the core GDP finding depends on: excluding the single most influential observation, excluding all influential observations, using robust standard errors, or using a different analysis year. The coefficient stayed within a narrow band (0.409–0.497) across all five. See `outputs/tables/sensitivity_analysis.csv`.

## Residual interpretation ("the happiness gap")

For each country, `predicted Life Ladder` (from the primary model) is subtracted from `observed Life Ladder` to get a residual — labeled the "happiness gap" in this project. This is **unexplained variation under one specific six-variable model**, not a measure of a country's true well-being. A country with a large positive gap simply reports a higher life evaluation than its GDP, health, employment, connectivity, urbanization, and inflation would predict; the model has no way to say *why*. See `docs/FINDINGS.md`, Finding 5, for the full interpretive framing and caveats.

## Observational-data limitations

Every result in this project is described using association language ("is associated with," "predicts," "correlates with") — never causal language ("causes," "leads to," "drives"). See `docs/LIMITATIONS.md` for the full discussion of why causal claims are not supported by this design.
