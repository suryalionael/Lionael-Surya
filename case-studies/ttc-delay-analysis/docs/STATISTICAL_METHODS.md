# Statistical methods

This project uses two models, both pre-registered in
`docs/ANALYSIS_PLAN.md` before estimation.

## Logistic regression for a major delay

The outcome is an indicator for a reported delay of 15 minutes or more.
The model is a binomial GLM with a logit link and these predictors: hour of
day (24 levels), weekday (7), month (12), mode (3), line group (the 19
lines with the most incidents plus `other`), and cause category (5).
Standard errors are cluster-robust, clustered by line group, so rows from
the same line do not count as independent evidence.

The model is trained on 2014-2023 (972,168 incidents, 240,355 major delays) and scored once on 2024 (99,984 incidents, 28,051 major delays). The holdout AUC is 0.756 (95% CI 0.753 to 0.759). Calibration is shown in `outputs/figures/fig08_calibration.png` and discrimination in `fig09_roc.png`.

## Negative binomial regression for daily counts

The count model uses one row per calendar date and mode, including days
with zero reported incidents. The outcome is the number of incidents.
Predictors are weekday, month, mode, a COVID-period indicator
(2020-03-15 to 2022-12-31), and calendar year. The negative binomial link
is log, and rate ratios are reported with 95% confidence intervals.

The Poisson dispersion is 10.09 on 13,946 residual degrees of freedom, which is strong evidence of overdispersion; the negative binomial theta is 9.56. The pre-registered model is therefore the count model reported in the findings.

## Diagnostics

- Separation: no fitted probabilities at exactly 0 or 1.
- Influence: dfbeta on a fixed 50,000-row sample; no row exceeded |dfbeta| = 1.
- Multicollinearity: the largest VIF is 21.5 for `line_groupother`; line groups nest inside modes, so this is expected and is reported rather than hidden.
- Overdispersion: Poisson dispersion is far above 1, supporting the negative binomial.
- Calibration and ROC are evaluated on the 2024 holdout, not the training data.

## Robustness

The checks are: exclude 2020-2021; thresholds of 10 and 20 minutes; drop
the top 1% of delay minutes; hour as a linear plus quadratic term with no
line group; cluster standard errors by location instead of line group; and
a negative binomial model without the COVID indicator. Results are in
`outputs/tables/robustness_logistic.csv`, `robustness_nb.csv`, and
`outputs/figures/fig10_robustness_forest.png`.
