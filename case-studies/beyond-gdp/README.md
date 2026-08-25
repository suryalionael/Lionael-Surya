# Beyond GDP

### A Statistical Investigation into the Economics of Happiness

A reproducible R statistics pipeline testing whether GDP per capita is actually associated with self-reported life satisfaction — and, more importantly, whether that association survives controlling for health, employment, connectivity, urbanization, and inflation, formal nonlinearity/interaction testing, full residual diagnostics, and two independent robustness checks.

## The Question

Does being richer actually make people happier? The World Happiness Report and World Bank both publish official data that speaks to this — but combining them correctly turned out to be less obvious than it looks.

## Overview

Most public treatments of this question reuse the World Happiness Report's own "Explained by: GDP / Social support / Health / ..." columns as if they were independent predictor variables. A Phase 0 data-feasibility investigation (`docs/DATASET_RESEARCH.md`) found — and numerically verified — that those columns are the report's own regression *output*: they sum exactly to the Life Ladder score by construction (max discrepancy 0.003 on a 0–10 scale, across 1,013 fully-decomposed rows). Regressing Life Ladder on them would be close to circular. Every predictor used in this project is instead sourced independently from the World Bank API, and that one finding shaped the entire downstream methodology.

## What I Did

1. **Data feasibility research first, code second** — investigated the World Happiness Report, World Bank, and OECD as candidate sources before writing any analysis code; OECD was ruled out because its well-being data covers only ~38–41 countries against 144–168 for WHR/World Bank.
2. **Built an 8-stage reproducible R pipeline** (`R/01_ingestion.R` → `R/08_findings.R`) that pulls data directly from official APIs, joins it via a documented country-code crosswalk (98.7% match rate, 22 manual name overrides, 3 permanently unmatched political-status edge cases), and produces a complete-case analytical dataset with every exclusion counted.
3. **Modeled progressively** — intercept-only → GDP alone → +health/employment → full six-predictor model — comparing on adjusted R²/AIC, not R² alone.
4. **Formally tested and rejected** a quadratic GDP term (diminishing-returns hypothesis) and a GDP×unemployment interaction, both against pre-set statistical *and* substantive bars, rather than assuming either.
5. **Ran a full diagnostic suite** (linearity, normality, homoscedasticity, Cook's distance, VIF) and reported a real multicollinearity issue instead of a suite that only shows what looks clean.
6. **Stress-tested the headline result** five pre-specified ways plus an independent 2019–2024 pooled panel with country-clustered standard errors.

## Key Findings

- **GDP per capita is positively associated with Life Ladder, and it survives controlling for five other factors**: coefficient 0.462 [95% CI 0.212, 0.711], p < 0.001, N = 144 countries (2019).
- **Unemployment, urbanization, and inflation are also independently associated with Life Ladder; life expectancy and internet use are not**, once GDP is in the model — a genuine multicollinearity effect (VIF ≈ 8.5–8.7 for GDP and internet use), not evidence that health/connectivity don't matter.
- **No evidence of a nonlinear "diminishing returns" relationship** between GDP and happiness (quadratic term p = 0.222) — tested and rejected, reported honestly rather than dropped.
- **No evidence that unemployment moderates the GDP–happiness relationship** (interaction p = 0.259) — the one interaction tested, pre-specified, not fished for.
- **The core finding is stable**: GDP coefficient stayed in a 0.409–0.497 range across 5 sensitivity checks (influential-observation exclusion, robust SEs, alternate year) plus an independent pooled-panel re-estimation (146 countries, 809 country-year observations).
- **Several Latin American countries score well above what the model predicts (Costa Rica +1.31, Nicaragua +1.04); several high-income East Asian/Gulf economies score below (Hong Kong SAR −1.51, Japan −0.94)** — reported strictly as unexplained model residuals, never as a claim about which country is "really" happier.

Full write-up, evidence, and stated limitations for every finding: [`docs/FINDINGS.md`](docs/FINDINGS.md).

## Statistical Techniques

**Stack:** R · tidyverse (dplyr/tidyr/readr/purrr) · ggplot2 · broom · car · lmtest · sandwich · testthat · renv

- Cross-sectional multiple linear regression (OLS), 144 countries, six independently-sourced predictors
- Formal nonlinearity test (quadratic term, nested F-test) and one pre-specified interaction test
- Full residual diagnostics: Shapiro-Wilk, Breusch-Pagan, Cook's distance/leverage, VIF — heteroscedasticity-robust (HC1) SEs evaluated directly rather than applied by default
- Secondary pooled 2019–2024 panel with country-clustered standard errors, used only as a robustness check (explicitly not causal panel evidence — no fixed-effects claims)
- Five pre-specified sensitivity checks (not a search across arbitrary specifications)
- Residual ("happiness gap") analysis: observed − predicted Life Ladder, ranked and visualized

Every coefficient is reported with a 95% CI, described as an **association**, never a causal effect. Full explanation written for a non-statistician: [`docs/STATISTICAL_METHODS.md`](docs/STATISTICAL_METHODS.md).

## Visualizations

19 ggplot2 figures in [`outputs/figures/`](outputs/figures/), including the GDP–Life Ladder relationship (raw vs. log scale), the full model coefficient plot, the linear-vs-quadratic nonlinearity comparison, the complete diagnostic suite (residuals-vs-fitted, Q-Q, Cook's distance, leverage), the happiness-gap ranked bar chart, and the sensitivity/robustness coefficient comparisons.

## Data Sources

- **[World Happiness Report 2026](https://www.worldhappiness.report/data-sharing/)** — Life Ladder (outcome variable), Gallup World Poll, official free download.
- **[World Bank Open Data](https://data.worldbank.org/)** — GDP per capita (PPP), life expectancy, unemployment, internet use, urbanization, inflation, pulled directly via the official REST API.

Both official, free, publicly documented. Data feasibility research (coverage, licensing, join quality, rejected variables/sources) in [`docs/DATASET_RESEARCH.md`](docs/DATASET_RESEARCH.md), [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md), and [`docs/DECISION_LOG.md`](docs/DECISION_LOG.md).

## Important Limitations

- **Observational, cross-sectional, country-level data.** Every result is an association, never a causal claim, and says nothing about individuals.
- **The model omits social support, trust, and inequality** — Phase 0 found no adequate free, independent data source for them (WHR's own social-support variable is only available as a non-independent regression contribution, not a raw value).
- **GDP and internet use are collinear enough (VIF ≈ 8.5–8.7)** that internet use's independent association, if any, can't be cleanly separated from GDP's.
- **Life Ladder is a 3-year rolling average matched to single-year World Bank predictors** — a structural mismatch that motivated the cross-sectional-first design over a strict annual panel.
- **The primary year (2019) was chosen for maximum complete-case coverage, not recency** — 2020–2024 all have smaller usable samples, likely reflecting pandemic-era disruption to national statistical reporting.

Thirteen limitations documented in full, nothing softened: [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md).

## Reproduce

Requires R (≥ 4.3) and [renv](https://rstudio.github.io/renv/). No paid software; raw data is re-downloaded directly from the official APIs above, not committed to this repo (see [`data/README.md`](data/README.md)).

```bash
cd case-studies/beyond-gdp
Rscript -e 'renv::restore()'   # installs the exact package versions in renv.lock
Rscript scripts/run_all.R      # re-downloads raw data, rebuilds every processed
                                # dataset, table, and figure from scratch
Rscript tests/testthat.R       # 19 tests / 38 expectations
```

This was actually torn down and rebuilt from scratch during development — identical analytical sample size, identical GDP coefficient to 4 decimal places, identical happiness-gap rankings. Full verification log in [`docs/PROJECT_COMPLETION.md`](docs/PROJECT_COMPLETION.md).

## Project Structure

```
R/               01_ingestion -> 08_findings, run in order by scripts/run_all.R
docs/            Phase 0 data research + analysis plan, findings, methods, limitations
outputs/
  figures/         19 ggplot2 figures (tracked)
  tables/          markdown reports (tracked); CSV backing tables regenerate via the pipeline
  models/          saved model objects (regenerate via the pipeline, not tracked)
tests/testthat/  19 automated pipeline tests
renv.lock        exact reproducible package versions
```

---
Back to [main portfolio](../../README.md).
