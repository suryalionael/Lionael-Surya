# Happiness Gap Report

_Generated 2026-08-25 by `R/08_findings.R`. Model: m3 (full main-effects model)_

## What this is -- and is not

The "happiness gap" is the residual from the primary regression model: `observed Life Ladder - predicted Life Ladder`, where the prediction comes from a country's GDP, life expectancy, unemployment, internet use, urbanization, and inflation.

**This is unexplained variation under one specific, deliberately modest model. It is not a measure of true well-being, national success, or happiness `"deserved"` by a country's economics.** A positive gap means a country reports a higher Life Ladder score than six socioeconomic variables alone would predict -- it does not mean that country is objectively happier than a country with a smaller gap and a higher absolute Life Ladder score. Read it as: "this country's reported life evaluation is not fully explained by the socioeconomic factors in this model," full stop.

## Top 15 positive gaps (higher observed Life Ladder than predicted)

| Country | Observed | Predicted | Gap |
|---|---|---|---|
| Finland | 7.81 | 6.45 | +1.36 |
| Costa Rica | 7.12 | 5.81 | +1.31 |
| Pakistan | 5.69 | 4.63 | +1.06 |
| Nicaragua | 6.14 | 5.10 | +1.04 |
| Uzbekistan | 6.26 | 5.25 | +1.01 |
| Congo | 5.19 | 4.19 | +1.01 |
| Honduras | 5.95 | 5.02 | +0.93 |
| Guatemala | 6.40 | 5.49 | +0.91 |
| Denmark | 7.65 | 6.80 | +0.85 |
| Niger | 4.91 | 4.09 | +0.81 |
| El Salvador | 6.35 | 5.57 | +0.78 |
| Brazil | 6.38 | 5.65 | +0.73 |
| Austria | 7.29 | 6.57 | +0.72 |
| Switzerland | 7.56 | 6.86 | +0.70 |
| Sweden | 7.35 | 6.65 | +0.70 |

## Top 15 negative gaps (lower observed Life Ladder than predicted)

| Country | Observed | Predicted | Gap |
|---|---|---|---|
| Hong Kong SAR of China | 5.51 | 7.02 | -1.51 |
| Botswana | 3.48 | 4.84 | -1.36 |
| Afghanistan | 2.57 | 3.91 | -1.34 |
| India | 3.57 | 4.80 | -1.23 |
| Tanzania | 3.48 | 4.60 | -1.12 |
| Egypt | 4.15 | 5.21 | -1.06 |
| Ukraine | 4.56 | 5.61 | -1.05 |
| Bulgaria | 5.10 | 6.13 | -1.03 |
| Japan | 5.87 | 6.82 | -0.94 |
| Lebanon | 4.77 | 5.70 | -0.93 |
| Malaysia | 5.38 | 6.30 | -0.92 |
| Singapore | 6.38 | 7.28 | -0.90 |
| Kuwait | 6.10 | 6.96 | -0.85 |
| Bahrain | 6.23 | 7.04 | -0.82 |
| Republic of Korea | 5.87 | 6.68 | -0.80 |

## Interpretive notes

- Countries with large positive gaps are frequently Latin American nations -- a pattern also noted by the World Happiness Report's own authors and in academic literature on social/family cohesion not captured by GDP-style socioeconomic indicators. This model cannot test that explanation directly (it has no social-support variable, per `docs/DECISION_LOG.md`), so it is offered as a hypothesis, not a finding.
- Countries with large negative gaps are worth interpreting cautiously: a large negative residual can reflect a genuinely lower reported life evaluation than peers, OR it can reflect country-specific circumstances the model's six variables do not capture (conflict, political instability, recent crisis) -- the model has no way to distinguish these.
- This ranking will shift under a different model specification (see the sensitivity analysis in `outputs/tables/sensitivity_analysis.csv`); the broad top/bottom groupings are reasonably stable across the tested specifications, but exact ranks within the middle of the distribution are not a precise, stable ordering.
