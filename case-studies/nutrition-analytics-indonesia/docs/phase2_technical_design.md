# Phase 2 — Technical Design: `src/features/` and `src/scoring/`

Defines the implementation architecture Phase 3 will build, following this project's
existing conventions (config-driven decisions, generated-not-hand-written
documentation, data contracts, append-only provenance). Nothing in this document is
implemented yet — Phase 2 is design-only.

## New config files (decisions encoded as version-controlled data, not hardcoded)

- **`config/indicator_directionality.yml`** — one entry per indicator: which NPI
  dimension it belongs to (per `docs/phase2_framework_design.md`) and its
  directionality (`higher_is_worse` / `higher_is_better`), so direction-flipping logic
  in code never hardcodes per-indicator assumptions.
- **`config/npi_weights.yml`** — the hybrid weighting decision from
  `docs/phase2_weighting_options.md`: the top-level dimension split (Socioeconomic
  Vulnerability vs. Education Access) and which method (PCA vs. single-representative
  indicator) is used within the vulnerability dimension. Changing the methodology
  later means editing this file, not code — and the change is visible in `git log`.

## `src/features/`

**Purpose:** transform the Phase 1 merged table into a form scoring can consume —
normalization and directionality alignment only. No weighting or combination happens
here.

| Module | Input | Output | Responsibility |
|---|---|---|---|
| `directionality.py` | `data/processed/merged_provincial_indicators.csv` + `config/indicator_directionality.yml` | in-memory DataFrame, sign-flipped so every column points "higher = more vulnerable" | Never silently assumes direction — raises if an indicator in the merged table has no entry in the config, rather than guessing. |
| `normalize.py` | directionality-aligned DataFrame | in-memory DataFrame, each indicator scaled (min-max 0–1, recommended for interpretability — "0 = least vulnerable province observed, 1 = most") | Scaling is fit only on present (non-null) values per indicator; never imputes to compute a scaling statistic. |
| `missing_value_policy.py` | normalized DataFrame | DataFrame + a per-province "coverage" flag (e.g. `n_indicators_available`) | Implements whichever policy Phase 3's sensitivity testing (`docs/phase2_sensitivity_design.md` Question 3.2) selects — renormalize-within-available or exclude-incomplete — as an explicit, swappable function, not inline logic buried in the scoring step. |

## `src/scoring/`

**Purpose:** combine the prepared features into the NPI, per
`docs/phase2_framework_design.md`'s structure and `docs/phase2_weighting_options.md`'s
hybrid method.

| Module | Input | Output | Responsibility |
|---|---|---|---|
| `pca_composite.py` | normalized `poverty_rate`, `ipm`, `expenditure_per_capita` | one composite "Socioeconomic Vulnerability" score per province + a loadings/variance-explained record | Uses `sklearn.decomposition.PCA(svd_solver="full")` (deterministic, no randomized solver) so reruns on identical input are byte-identical. Raises if the retained component explains an implausibly low share of variance (the data not actually being collinear enough to justify PCA would be a real finding, not silently swallowed). |
| `npi.py` | Socioeconomic Vulnerability composite + `participation_rate` (Education Access) + `config/npi_weights.yml` | `data/processed/npi_scores.csv`: province, both dimension sub-scores, final NPI, reach-modifier metrics (`population × stunting_rate`, `population × NPI percentile`), priority tier | The only module that actually produces a ranking. Outcome variables (`stunting_rate`, `stunting_category`) are joined into the output for reporting/validation but never enter the weighted sum, per the framework design's anti-circularity decision. |
| `sensitivity.py` | `npi.py`'s output + the alternative weighting variants from `docs/phase2_weighting_options.md` | `docs/phase3_sensitivity_report.md` (generated, not hand-written) | Implements all four checks from `docs/phase2_sensitivity_design.md`: weight perturbation, leave-one-indicator-out, the four named assumption stress-tests, and outcome-correlation validation. |

## Validation checks (extending this project's existing `src/validation/contracts.py` pattern)

A new contract, e.g. `docs/data_contracts/npi_scores.yml`, should specify:
- Required columns: `province`, the two dimension sub-scores, `npi`, `npi_percentile`,
  `priority_tier`.
- `province`: `unique_count_min`/`max` 30–40, as used throughout this project — and a
  duplicate check (already implemented generically in `src/validation/contracts.py`).
- `npi`: numeric range appropriate to the chosen normalization (e.g. 0–1 if dimension
  scores are min-max scaled and equally weighted).
- A **new check type** not yet needed by Phase 0/1 contracts: PCA variance-explained
  threshold (e.g. first component must explain ≥ 50% of the vulnerability trio's
  variance) — `contracts.py` would need a small extension to support this, or
  `pca_composite.py` can enforce it directly and raise before scoring proceeds.
- Reach-modifier outputs must be non-negative and `null` (not zero) for the 4
  provinces missing `population`, never silently computed against a fabricated
  population figure.

## Reproducibility requirements

- **Deterministic PCA**: `svd_solver="full"`, no random initialization — same input
  always produces the same loadings and scores.
- **Config-driven, not code-driven, methodology**: the weighting split and
  directionality assignments live in YAML, reviewable in `git diff`/`git log` like
  every other decision in this project (`config/datasets.yml` set the precedent in
  Phase 0).
- **Generated, not hand-written, reports**: `docs/phase3_sensitivity_report.md` and
  any PCA-loadings summary are written by code from real computed output, matching
  `docs/data_inventory.md` and `docs/missing_data_report.md`'s existing pattern in
  this project — never hand-edited to "look right."
- **A computation manifest**, parallel to `data/raw/_manifest.jsonl` but for derived
  (not fetched) artifacts — e.g. `data/processed/_scoring_manifest.jsonl` — recording
  the git commit hash, the config file checksums used (`npi_weights.yml`,
  `indicator_directionality.yml`), the input file's checksum (from the existing raw
  manifest), the output checksum, and a timestamp. This lets a reviewer verify which
  exact code + config + data combination produced a given `npi_scores.csv`, the same
  auditability goal the Phase 0 manifest serves for ingestion.
- **Tests**: unit tests for `directionality.py` (raises on an unmapped indicator),
  `normalize.py` (correct min-max bounds, ignores nulls when fitting), the missing-
  value policy function (both variants produce documented, different, non-fabricated
  results), and `pca_composite.py` (a small fixture with a known, hand-computable
  expected loading direction) — following the existing `tests/test_cleaning.py`
  pattern of testing logic against fixtures, not live data.
