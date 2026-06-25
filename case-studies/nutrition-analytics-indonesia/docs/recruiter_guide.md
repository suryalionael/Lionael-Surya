# Recruiter Guide

A 5-minute path through this project, organized by what you're evaluating.

## If you have 2 minutes

1. Open the **[live dashboard](https://nutrition-analytics-indonesia.streamlit.app)** (free tier — may take ~30s to wake up on first visit).
2. Read the [Executive Summary](executive_summary.md).

Prefer to run it locally instead? `make install && streamlit run dashboard/Home.py`
(uses a committed data snapshot — no API keys needed to view it).

## If you want to evaluate technical depth

This project is structured so you can see the *thinking*, not just the output:

- **Real-world data wrangling, not a clean Kaggle CSV**: `docs/known_limitations.md`
  documents 5 distinct real obstacles (an undocumented API pagination bug, a
  stale-vs-current province scheme conflict, no scriptable source for one
  dataset, etc.) and exactly how each was diagnosed and resolved.
- **Statistical rigor with self-correction visible in the commit history**:
  `docs/phase3_methodology_comparison.md` shows a more sophisticated method
  (PCA) being empirically out-performed by a simpler one, and the simpler one
  being honestly promoted to primary instead of defending the more impressive-
  sounding choice.
- **Spatial statistics, not just choropleth maps**: `docs/phase5_spatial_results.md`
  — global/local Moran's I with permutation-based significance testing,
  multiple neighbor-definition sensitivity checks, and a documented decision to
  reject a more "ready-made" geometry source (GADM) because it would have
  silently broken the spatial statistics for 4 provinces.
- **67 automated tests**, run on every push via GitHub Actions
  (`.github/workflows/`), testing logic against fixtures — not the real
  pipeline output, which is the point: bugs get caught by tests written
  *before* trusting a result, several real bugs were caught and fixed this way
  during development (see `CHANGELOG.md`).

## If you want to evaluate communication skills

- [PROJECT_ROADMAP.md](../PROJECT_ROADMAP.md) — the full phase-by-phase plan,
  written for a non-technical reader to follow the project's progression.
- The dashboard's **Methodology** and **Robustness & Uncertainty** pages —
  built specifically to explain *why* a decision was made, including the
  project's most counter-intuitive finding (rank order is highly stable;
  adaptive tier labels are not) in plain language.
- Every `docs/phase*.md` file follows the same structure: methodology, real
  results, limitations, interpretation — written to be skimmable by a
  policymaker, not just a fellow analyst.

## What hiring signal each part of the repo demonstrates

| Repo area | Signal |
|---|---|
| `src/ingestion/` | Real API integration, retry/backoff, data contracts, provenance/audit trails |
| `src/cleaning/`, `src/reference/` | Data quality engineering, entity resolution (province name standardization) |
| `src/scoring/`, `src/features/` | Statistical methodology (PCA, normalization), empirical model comparison |
| `src/geospatial/` | Spatial statistics (Moran's I, LISA), geospatial data engineering |
| `dashboard/` | Full-stack analytics product: data pipeline → interactive app |
| `docs/` | Technical writing, stakeholder communication, intellectual honesty under uncertainty |
| `tests/` | Test-driven validation of statistical/data logic |

## Talk to me about

- Why the project changed its primary scoring methodology mid-project (the
  honest answer, not the simple one: see `docs/phase3_final_methodology_decision.md`)
- How I'd extend this to other policy domains (the framework — real data only,
  validate before publish, document every limitation — isn't nutrition-specific)
