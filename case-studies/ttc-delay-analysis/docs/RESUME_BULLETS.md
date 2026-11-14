# Resume bullets

Every number below appears in the generated outputs of the two repositories.
Do not round these into a different claim without re-running the code.

## TTC delay analysis

- Built a reproducible R + PostgreSQL pipeline over 1,251,597 TTC delay
  incidents (2014-2026), harmonising two legacy schemas and a 2025 schema
  across subway, bus, and streetcar.
- Found that bus carries 64.8% of incidents and 83.9% of reported delay
  minutes, while the top 5 streetcar lines account for 74.0% of streetcar
  delay minutes; major delays peak overnight rather than in the PM rush.
- Modelled P(delay >= 15 minutes) with cluster-robust logistic regression and
  achieved AUC 0.756 on a 2024 time-based holdout; quantified a 0.79 COVID
  count rate ratio with negative binomial regression (Poisson dispersion
  10.09).
- Documented 1,233 records containing a 999-minute placeholder and coarse
  legacy cause labels, showing why delay minutes need a measurement audit
  before use as a KPI.

## dbt analytics layer

- Added six window-function and CASE-driven dbt marts (RFM, cohort
  retention, revenue growth, category product ranks, Pareto/ABC, order gaps)
  on the real Olist dataset, with schema tests and four singular tests.
- Built customer RFM segmentation across 95,420 customers; 22,767 (23.9%) are
  At Risk and hold 24.2% of historical revenue, while 6,628 Champions (6.9%)
  hold 13.2%.
- Quantified Pareto concentration: 9,252 products (28.1%) generate 80.0% of
  revenue, giving a defensible A/B/C inventory split.
- Measured low repeat purchasing: 2,913 of 95,420 customers (3.1%) order more
  than once; month-1 cohort retention is 0.46%, and the median gap between
  repeat orders is 29 days (p90 242 days).
