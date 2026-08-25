# Limitations

Good analytical work defines its own boundaries. This document is deliberately thorough — none of it undermines the findings in `docs/FINDINGS.md`; it defines exactly what those findings do and do not support.

---

## 1. Observational data — no causal claims

Nothing in this project was experimentally manipulated. Countries were not randomly assigned different GDP levels, employment rates, or inflation rates. Every regression coefficient describes an **association** observed in the data, not a causal effect. Throughout this project, "GDP is associated with Life Ladder" is used; "GDP causes happiness" is not, and should not be inferred from any figure or table here.

## 2. Country-level (ecological) inference

Every row in the analytical dataset is a country, not a person. A country-level association between GDP and Life Ladder does **not** imply that a wealthier individual within a country is happier than a poorer one — that would be an ecological fallacy, inferring individual-level relationships from aggregate data. This project makes no individual-level claims.

## 3. Cross-sectional primary design

The primary model compares 144 countries at a single point in time (2019). It cannot speak to how a given country's happiness would change if its GDP changed — that is a within-country, over-time question that this design is not built to answer. The secondary pooled-panel check (§6 below) partially addresses this but is explicitly not causal panel evidence either.

## 4. Possible omitted-variable bias

The model includes six predictors. It does not include social support, trust, political freedom, income inequality, culture, history, or dozens of other plausible influences on national happiness — some because Phase 0 research found no adequate free, independent data source (social support, freedom — see `docs/DECISION_LOG.md`), others because they were simply out of scope for a six-variable model. Any of these omitted factors could be correlated with both GDP and Life Ladder, which would bias the estimated GDP coefficient in an unknown direction. The stability of the GDP coefficient across many specifications (Finding 6) is reassuring but does not rule this out.

## 5. Measurement differences across countries

Life Ladder is a self-reported survey measure. Cross-cultural research suggests response styles to 0–10 scale questions can differ systematically by culture (e.g., some cultures may be more prone to extreme or midpoint responses), independent of "true" underlying well-being. This project cannot separate that from genuine cross-country differences in happiness.

## 6. Life Ladder is a 3-year rolling average; predictors are single-year

This is a genuine structural mismatch, investigated directly in Phase 0 (see `docs/DATASET_RESEARCH.md` §9). The outcome variable smooths over three years of survey data while every predictor is a single-year snapshot. This is the primary reason the project favors a cross-sectional design over a strict annual panel — see `docs/STATISTICAL_METHODS.md` for the full reasoning.

## 7. Missing data, handled by exclusion, not imputation

144 of 151 countries with 2019 WHR data have complete predictor data; 7 were excluded (Kosovo, Tajikistan, Turkmenistan, Venezuela, DR Congo, Yemen, South Sudan — see `outputs/tables/analytical_dataset_report.md` for which variable was missing in each case). No values were imputed anywhere in this project. If the excluded countries differ systematically from the included ones (several are conflict-affected or have historically poor statistical infrastructure), the analytical sample may not be perfectly representative of all 144+ countries with WHR data, let alone the full ~195 countries in the world.

## 8. Country comparability

A small number of entities in the WHR data (Taiwan, North Cyprus, Somaliland) have no World Bank equivalent at all, due to disputed political status, and are excluded from every analysis in this project — not because of a data-processing failure, but because no official World Bank statistics exist for them (see `docs/DATASET_RESEARCH.md`). Separately, Puerto Rico appears in the data as a country-like entity despite being a U.S. territory without independent macroeconomic policy; it was not excluded from the primary analysis, which is a debatable choice worth flagging explicitly.

## 9. Residual ("happiness gap") interpretation

The happiness-gap ranking (Finding 5) reflects unexplained variation under one specific six-variable model — it is not a measure of a country's "true" happiness, well-being, or quality of life, and should never be read as a claim that one country is objectively happier or better-run than another. A different (equally reasonable) model specification would produce a somewhat different ranking, especially for countries in the middle of the distribution. Only the broad top/bottom groupings are reasonably stable.

## 10. Model specification uncertainty

Only one primary model was ultimately selected (the full six-predictor main-effects model), after formally testing — and rejecting — a quadratic GDP term and a GDP×unemployment interaction. Other reasonable specifications (different variable transformations, different predictor sets, different functional forms) were not exhaustively explored, by design (the project rules explicitly prohibit testing "dozens of specifications" in search of significance). The sensitivity analysis (Finding 6) shows the core GDP finding is robust to the variations that *were* tested, but this is not proof of robustness to every conceivable alternative specification.

## 11. Small-sample high-income tail

The observed GDP range includes a handful of extreme high-income outliers (Luxembourg, Singapore, Ireland — flagged directly in `outputs/tables/eda_outliers_flagged.csv`). These are retained (they are real, not data errors) but mean that any inference about the very top of the GDP distribution rests on very few observations, which limits confidence in, e.g., the nonlinearity test at the high end (Finding 3).

## 12. Multicollinearity between GDP and internet use

Diagnostics (Finding 7) found GDP per capita and internet use are highly collinear (VIF ≈ 8.5–8.7 for both). This means the model cannot cleanly separate "a country is wealthy" from "a country has high internet penetration" — internet use's true independent association with Life Ladder, if any, may be masked by this overlap rather than genuinely absent.

## 13. Scope of the geographic/economic coverage

OECD data was investigated in Phase 0 and excluded from this project because its well-being datasets cover only ~38–41 countries, versus 144–168 for the WHR/World Bank combination used here. This means dimensions OECD uniquely offers (detailed inequality, work-life balance, housing quality) are entirely absent from this analysis, by design — a deliberate scope trade-off in favor of broader country coverage, documented in `docs/DECISION_LOG.md`.
