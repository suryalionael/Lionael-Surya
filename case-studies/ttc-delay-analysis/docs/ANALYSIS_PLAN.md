# Analysis plan (pre-registered before modelling)

Committed before any model was estimated. Changes after this point are
recorded in `docs/DECISION_LOG.md` with a date and reason.

## Question

Where, when, and why do TTC delays concentrate, and what predicts a major
delay? The intended user is TTC service planning, not the travelling public.

## Unit and outcome

- Unit of analysis: one reported delay incident.
- Primary outcome: `major_delay = 1` when `delay_minutes >= 15`.
- Sensitivity thresholds: 10 minutes and 20 minutes, pre-specified.
- Delay minutes are as reported by the TTC. They are not independently
  verified against vehicle tracking.

## Descriptive questions

1. Which modes, lines, and locations accumulate the most delay minutes, and
   how concentrated are they? Minimum group size for a ranking: 100 incidents.
2. How do incident counts and major-delay rates vary by hour, weekday, and
   month?
3. What share of delay minutes comes from each cause category (equipment,
   operations, plant/infrastructure, security, transportation)?
4. How did volumes and severity change across 2014-2026, including the
   COVID-19 period?

Descriptive answers are counts, shares, medians, and percentiles. They are
not causal estimates.

## Hypotheses (directional where stated)

- **H1 (when):** major delays are more likely during weekday PM peak hours
  (15:00-19:00) than overnight hours (00:00-05:00).
- **H2 (why):** equipment/operations causes are the most frequent, while
  plant/infrastructure and weather/external causes have a higher share of
  major delays than equipment causes.
- **H3 (where):** delay minutes are concentrated in a small set of lines and
  locations; the top 10% of lines account for more than half of delay
  minutes.
- **H4 (mode):** bus incidents are more numerous than subway and streetcar
  incidents, but subway incidents are more likely to be major.
- **H5 (time):** daily incident counts are lower during the COVID period
  (2020-03-15 through 2022-12-31) than outside it, after weekday and month
  adjustment.

## Statistical models

### Logistic regression: P(major delay | incident)

- Outcome: `major_delay` at the 15-minute threshold.
- Predictors: hour of day (factor, 24 levels), weekday (factor), month
  (factor), mode (factor), line group (the 19 lines with the most incidents
  plus `other`), cause category (first letter of the delay code, plus
  `Unknown`).
- Estimation: `glm(family = binomial)`.
- Inference: cluster-robust standard errors clustered by line group
  (`sandwich::vcovCL`), reported as odds ratios with 95% confidence
  intervals.
- Holdout: train on 2014-2023, test on 2024. The 2025-2026 rows use a
  different source schema, so they are not used to score this model.

### Negative binomial regression: daily incident counts

- Unit: calendar date x mode.
- Outcome: count of reported delay incidents.
- Predictors: weekday (factor), month (factor), mode (factor), COVID-period
  indicator (2020-03-15 to 2022-12-31), calendar year (continuous).
- Estimation: `MASS::glm.nb` with a log link.
- Reporting: rate ratios with 95% confidence intervals, plus the estimated
  theta and a overdispersion check against a Poisson model.

## Diagnostics

- Separation / extreme coefficients in the logistic model.
- Overdispersion test for the negative binomial model.
- Influence: maximum absolute dfbeta and the share of observations with
  |dfbeta| above 1.
- Multicollinearity: variance inflation factors for the model matrix.
- Calibration on the 2024 holdout: decile calibration table and plot.
- Discrimination on the 2024 holdout: ROC curve and AUC.

## Robustness checks (all pre-specified)

1. Exclude 2020-2021 from the logistic model.
2. Re-estimate the logistic model at the 10-minute and 20-minute thresholds.
3. Drop the top 1% of delay minutes (winsorised severity) and re-estimate.
4. Alternate logistic specification: hour as a linear + quadratic term
   instead of 24 factors, no line group.
5. Cluster standard errors by location instead of line group.
6. Refit the negative binomial model without the COVID indicator.

Uncomfortable or null results are reported, not hidden.

## Cleaning and exclusion rules

- Drop records with missing or unparseable date or time.
- Drop negative delay minutes.
- Drop delay minutes above 1,440 (24 hours) as implausible for a single
  reported incident.
- Drop exact duplicates on mode, date, time, line, location, delay code, and
  delay minutes.
- Keep records with a missing location for incident-level models, but exclude
  them from location rankings.
- Map unrecognised delay codes to cause category `Unknown`; do not drop them.
- Report every exclusion count and a raw-to-clean reconciliation table.

## Current-period warning

The since-2025 extract is a rolling file. The final month in any download can
be partial. Monthly trend charts show counts so a partial month is visible,
and no trend claim is made about the final month.

## Language

All model results are described as associations. No result in this project
identifies a causal effect of any cause category, line, station, or hour on
delay severity.
