# TTC Delay Analysis

Where, when, and why do TTC delays concentrate, and what predicts a major
delay? This project answers that question for a service-planning audience
using the City of Toronto's open TTC delay data, an R pipeline, and versioned
SQL views in PostgreSQL.

The analysis contains 1,251,597 reported incidents from 2014-01-01 to
2026-09-30 across subway, bus, and streetcar.

## The Question

Which modes, lines, locations, hours, and causes accumulate the most delay
minutes, and which factors are associated with a reported delay lasting 15
minutes or more?

## Why This Matters

TTC service planning has to allocate limited recovery time, vehicle
availability, and staff attention. A network-wide average hides the fact that
bus, streetcar, and subway delays behave differently, and that a small number
of lines and locations carry a large share of the problem. The analysis also
shows where the measurement itself is weak, which matters before delay
minutes are used as a performance target.

## What I Did

- Downloaded every yearly TTC delay file for 2014-2024 and the rolling
  since-2025 extract from the City's CKAN API, with SHA-256 checksums.
- Harmonised two legacy schemas and the newer 2025 schema across three modes,
  including the 2025 switch from `Route`/`Location`/`Incident` to
  `Line`/`Station`/`Code`.
- Documented every exclusion in a raw-to-clean reconciliation table.
- Loaded the cleaned data into PostgreSQL and put the heavy aggregation in
  versioned SQL views: line and location rankings, daily and monthly series,
  a 28-day rolling average, year-over-year change, hour-by-weekday rates, and
  cause shares.
- Fit a logistic model for the probability of a major delay, with
  cluster-robust standard errors by line group, and a negative binomial model
  for daily incident counts by mode.
- Ran pre-registered diagnostics and robustness checks, and generated the
  findings and this repository's tables and figures from the fitted objects.

## Key Findings

1. **Bus is the delay system.** Bus has 64.8% of incidents and 83.9% of
   reported delay minutes. Streetcar has 13.7% of incidents and 12.6% of
   delay minutes. Subway has 21.6% of incidents but only 3.5% of delay
   minutes.
2. **The overall major-delay rate is 25.7%.** Bus is highest at 34.5%,
   streetcar is 20.5%, and subway is 2.65%.
3. **Delay minutes concentrate on streetcar lines, not bus lines.** The top
   10 bus lines account for 17.4% of bus delay minutes. The top 5 streetcar
   lines account for 74.0%, and line 501 alone is 23.3%. YU and BD together
   are 89.6% of subway delay minutes.
4. **Major delays peak overnight.** The 15-minute-plus rate is highest at
   03:00 for bus (57.3%) and streetcar (53.4%), and at 05:00 for subway
   (4.0%). Hour 3 has an odds ratio of 1.71 relative to midnight; the PM peak
   is lower than midnight. The pre-specified PM-peak hypothesis is not
   supported.
5. **Operations and external causes dominate delay minutes.** They are 75.3%
   of bus delay minutes, 71.6% of streetcar, and 47.6% of subway.
   Plant/infrastructure has higher odds of a major delay than equipment
   (odds ratio 2.17, 95% CI 1.64 to 2.88).
6. **Bus delays are more severe than subway delays.** Subway's odds ratio for
   a major delay is 0.046 relative to bus, and streetcar's is 0.39. The
   pre-specified expectation that subway would be more severe is not supported.
7. **COVID reduced counts, and weekends are quieter.** The negative binomial
   model estimates a COVID-period rate ratio of 0.79 and a year term of 1.005.
   Saturday's rate ratio is 0.85 and Sunday's is 0.72.
8. **A major delay is partly predictable.** On the 2024 holdout the logistic
   model has AUC 0.756 (95% CI 0.753 to 0.759) and a Brier score of 0.1708.
   It under-predicts 2024 severity: mean predicted 24.2% against observed
   28.1%.
9. **Diagnostics are not all clean.** The Poisson dispersion is 10.09, so the
   negative binomial is required (theta 9.56). VIF is 21.5 for
   `line_groupother` because line groups nest inside modes; that specification
   needs care.
10. **Measurement caveats matter.** 1,233 incidents have a 999-minute
    placeholder, concentrated in 2018, and the legacy bus/streetcar files use
    coarse cause labels. Location rankings exclude the `MSTN` placeholder.

The authoritative, generated version of these findings is
[`docs/FINDINGS.md`](docs/FINDINGS.md).

## Statistical Approach

The plan was committed to [`docs/ANALYSIS_PLAN.md`](docs/ANALYSIS_PLAN.md)
before any model was estimated. The logistic model uses hour, weekday, month,
mode, line group, and cause category, with cluster-robust standard errors
clustered by line group. It is trained on 2014-2023 and tested on 2024. The
count model is a negative binomial regression of daily incidents on weekday,
month, mode, a COVID-period indicator, and year. Diagnostics cover
separation, influence, multicollinearity, overdispersion, calibration, and
ROC/AUC. Robustness checks cover excluding 2020-2021, thresholds of 10 and 20
minutes, dropping the top 1% of delays, an alternate hour specification, and
clustering by location.

Full method notes: [`docs/STATISTICAL_METHODS.md`](docs/STATISTICAL_METHODS.md).

## Data

Source: City of Toronto Open Data, TTC Subway, Bus, and Streetcar Delay Data.
Licence: Open Government Licence - Toronto. Dataset research, including the
verified CKAN API host and the schema differences, is in
[`docs/DATASET_RESEARCH.md`](docs/DATASET_RESEARCH.md). The data dictionary is
[`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md).

Raw files are downloaded to `data/raw/` and are gitignored. Only generated
tables, figures, the report, and small lookup files are committed.

## Results

| Output | What it shows |
|---|---|
| [`fig01_daily_incidents_28d.png`](outputs/figures/fig01_daily_incidents_28d.png) | Daily volume, 28-day rolling average, with the COVID period marked. |
| [`fig02_major_delay_heatmap.png`](outputs/figures/fig02_major_delay_heatmap.png) | Major-delay rate by weekday and hour, faceted by mode. |
| [`fig03_top_lines.png`](outputs/figures/fig03_top_lines.png) | Top lines by delay minutes and share of their mode's delay. |
| [`fig04_cause_mix.png`](outputs/figures/fig04_cause_mix.png) | Cause categories as a share of delay minutes. |
| [`fig05_delay_distribution.png`](outputs/figures/fig05_delay_distribution.png) | Distribution of reported delay minutes, 120-minute cap. |
| [`fig06_monthly_delay_minutes.png`](outputs/figures/fig06_monthly_delay_minutes.png) | Monthly delay minutes by mode. |
| [`fig07_line_concentration.png`](outputs/figures/fig07_line_concentration.png) | Cumulative share of delay minutes by ranked line. |
| [`fig08_calibration.png`](outputs/figures/fig08_calibration.png) | Calibration of the logistic model on the 2024 holdout. |
| [`fig09_roc.png`](outputs/figures/fig09_roc.png) | ROC curve and AUC on the 2024 holdout. |
| [`fig10_robustness_forest.png`](outputs/figures/fig10_robustness_forest.png) | Selected odds ratios across robustness specifications. |

The stakeholder report is
[`reports/ttc_delay_report.html`](reports/ttc_delay_report.html).

## Limitations

Reporting bias, no ridership or weather denominator, coarse legacy cause
labels, a 999-minute placeholder, a schema break in 2025, a partial final
month, high VIF from the line-group specification, and a single-year holdout
all limit the conclusions. Every model result is an association, not a causal
effect. The full list is in [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md).

## How to Run

With Docker:

```bash
docker compose up -d postgres
make deps
make pipeline
```

The compose database is `ttc_delays` on port 5434 with user `ttc`. To use an
existing local PostgreSQL instead:

```bash
createdb ttc_delays
TTC_DB_PORT=5432 TTC_DB_USER="$USER" TTC_DB_PASSWORD= make pipeline
```

Or run the scripts directly:

```bash
Rscript scripts/run_all.R
```

The pipeline downloads data, cleans and reconciles it, loads PostgreSQL,
builds the SQL views, runs EDA, fits and diagnoses both models, runs the
robustness checks, writes `docs/FINDINGS.md`, runs the tests, and renders the
report. `make test` runs the assertions alone.

## Repository map

```
R/                  numbered pipeline scripts, 00_config.R to 08_findings.R
scripts/run_all.R   one-command pipeline
sql/                schema, staging, analytical views, data-quality checks
docs/               research, plan, methods, dictionary, findings, limitations
outputs/            generated figures and tables (committed)
reports/            R Markdown source and rendered HTML
tests/testthat/     pipeline assertions
```

## Licence

Code is MIT licensed. The data is published by the City of Toronto under the
Open Government Licence - Toronto.
