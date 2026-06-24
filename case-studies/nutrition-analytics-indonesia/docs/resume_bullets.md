# Resume Bullets

Real numbers throughout — adjust phrasing to match the role, but don't inflate
the figures; they're already real and don't need it.

## Data Analyst version

- Built an end-to-end data pipeline ingesting 7 real datasets from 3 government
  sources (Indonesia's national statistics agency, health ministry, and
  geospatial agency), with automated data-quality contracts catching schema and
  range violations before any downstream analysis
- Diagnosed and fixed a pagination bug in a government API that was silently
  returning only 10 of 1,699 results, and a data-vintage conflict between two
  government endpoints disagreeing on the current administrative boundary count
- Built an interactive Streamlit dashboard (6 pages: executive overview,
  sortable/filterable ranking explorer with CSV export, interactive choropleth
  map, per-region profile pages, and full methodology documentation) serving a
  38-region priority ranking to non-technical stakeholders

## Data Scientist version

- Designed and empirically validated a composite priority index across 38
  regions, including an indicator-collinearity audit (identified r = 0.88
  between two candidate inputs), a PCA-vs-single-indicator methodology
  comparison decided by a 5-criterion decision matrix, and leave-one-indicator-out
  sensitivity analysis
- Validated the index against real-world outcomes (Spearman r = 0.74) and
  weighting-perturbation robustness (rank-order Spearman r > 0.99 across a ±20%
  sensitivity sweep) before publishing any result, reporting the more
  conservative outcome-correlation figure alongside the headline one
- Applied spatial statistics (global and local Moran's I, LISA cluster
  detection with permutation-based significance testing) to confirm
  geographically-clustered structure in the ranking (Moran's I = 0.622,
  p = 0.001), tested across 4 different spatial-neighbor definitions for
  robustness
- Surfaced and documented a non-obvious methodological finding: adaptive
  natural-breaks classification can reclassify the majority of observations
  under small perturbations even when underlying rank order is highly stable —
  recommended rank/percentile over tier labels for downstream decision-making

## BI Analyst version

- Built a 6-page interactive Streamlit dashboard translating a complex,
  multi-phase statistical pipeline into stakeholder-ready views: executive KPI
  summary, sortable/exportable ranking table, switchable choropleth map (score /
  tier / spatial cluster views with hover tooltips), per-region drill-down
  profiles benchmarked against the national median, and a transparent
  methodology explainer
- Generated a reusable, committed data snapshot layer decoupling the dashboard
  from the raw analytical pipeline, enabling instant load without requiring
  end users to hold API credentials or rerun the full pipeline
- Designed visual standards so every chart answers a specific question (e.g. a
  dedicated LISA-cluster map exists specifically to show *whether* an apparent
  pattern is statistically real, not just colored by score)

## Policy Analytics version

- Built a transparent, evidence-based prioritization framework for child-
  nutrition interventions across 38 Indonesian provinces, using exclusively
  real public-sector data (national statistics agency, health ministry,
  geospatial agency) with zero synthetic or simulated values
- Quantified regional disparity for policy targeting: Eastern Indonesia's mean
  priority score is 2.5x Western Indonesia's, confirmed significant by two
  independent statistical tests (ANOVA p = 2.8e-8, Kruskal-Wallis p = 8.1e-5),
  and identified a 6-province statistically significant high-vulnerability
  spatial cluster via local spatial autocorrelation analysis
- Documented every data limitation and methodological judgment call in
  plain language (20+ phase-by-phase decision documents), including honest
  disclosure that a key indicator's outcome correlation is meaningfully weaker
  once incomplete-data provinces are excluded — prioritizing decision-maker
  trust over a more flattering headline number
