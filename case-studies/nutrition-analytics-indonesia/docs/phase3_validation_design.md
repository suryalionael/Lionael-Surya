# Phase 3 — Validation Design

Specifies exactly how the 4 validation procedures will be implemented against the
real pipeline built in `src/features/` and `src/scoring/` (confirmed working in
`docs/phase3_dry_run.md`). This document is a design, not a result: none of these
procedures are executed against real rankings in this phase, because every one of
them inherently compares orderings of provinces, which is the rankings step this
phase is explicitly stopping before. It supersedes the more abstract version of this
plan in `docs/phase2_sensitivity_design.md` now that real code and real diagnostic
numbers (loadings, variance explained, the 34/4 completeness split) exist to design
against concretely.

## 1. Correlation with observed stunting

**Why this is valid, not circular:** `stunting_rate` is excluded from the NPI's
weighted inputs by construction (`docs/phase2_framework_design.md`'s outcome-layer
design), so correlating the index against it is a genuine face-validity check, not
comparing a number to a restatement of itself.

**Implementation:** `src/scoring/validation.py::correlate_with_outcome(npi_df)` will
compute Spearman rank correlation between `npi` and `stunting_rate` across the 38
provinces, plus the same correlation restricted to the 34 `data_completeness ==
"full"` provinces only (isolating whether the 4 partial-coverage provinces behave
differently). Reports the correlation coefficient and p-value, not a ranked list.

**Pass/fail threshold (set now, before seeing the result, to avoid the same
post-hoc-threshold problem flagged in `docs/phase2_sensitivity_design.md`):**
Spearman r > 0.5, consistent with the strength of the raw pairwise correlations
already observed in the indicator audit (`ipm` and `expenditure_per_capita` each
individually correlate with `stunting_rate` at |r| ≈ 0.71-0.73). A composite NPI
correlating noticeably *below* its strongest individual input component would
indicate the combination step is destroying signal, not adding value, and the
framework would need to be revisited before any score is published.

## 2. Rank stability checks

**Implementation:** `src/scoring/validation.py::rank_stability(npi_df, variants)`
will accept a list of alternative scoring runs (e.g. pure equal-weighting instead of
PCA-for-vulnerability, or different top-level dimension splits per
`docs/phase2_weighting_options.md`) and compute, against the baseline hybrid-weighted
run:
- Spearman rank correlation of the full ordering.
- Jaccard overlap of the top-decile (top ~4 provinces) membership between baseline
  and each variant — chosen over "top 10" because this dataset only has 38
  provinces, where top-10 is over a quarter of the country; top-decile is a more
  meaningful "short list" size for a national prioritization exercise.
- The single largest per-province rank shift, with that province named — a
  policymaker representing that specific province will care about *their* province's
  robustness more than an aggregate correlation number.

**Will exercise:** the dry run already confirms the pipeline produces a real `npi`
per province; rank stability simply needs ≥2 scoring runs (e.g. baseline +
pure-equal-weighting) computed via the existing `compute_npi()`, with weights swapped
via `config/npi_weights.yml` variants, not new scoring logic.

## 3. Weight sensitivity checks

**Implementation:** `src/scoring/validation.py::weight_perturbation_grid(merged_df,
weight_grid)` will recompute `compute_npi()` across a grid of top-level dimension
splits (e.g. socioeconomic_vulnerability:education_access at 70:30, 60:40, 50:50
[baseline], 40:60, 30:70) and report, per grid point, the same Spearman/top-decile
metrics as §2 against the 50:50 baseline. This directly operationalizes
`docs/phase2_sensitivity_design.md` Question 1 now that the actual weight
configuration (`config/npi_weights.yml`) exists to perturb.

**Known structural sensitivity to test for specifically:** because the 4
partial-coverage provinces get 100% weight on `socioeconomic_vulnerability` when
`education_access` is unavailable (per the renormalization policy), those 4
provinces' scores are, by construction, *insensitive* to the top-level weight split
in a way the other 34 aren't — they always score on vulnerability alone regardless
of how the 50:50 split is perturbed. This grid should explicitly check whether that
makes the 4 provinces' *relative* ranking among themselves vs. the other 34
artificially stable (an artifact of missing data, not real robustness) and flag it
as such if found, rather than reporting it as good news.

## 4. Leave-one-indicator-out (LOIO) tests

**Implementation:** `src/scoring/validation.py::leave_one_indicator_out(merged_df)`
will, for each of the 4 input indicators (`poverty_rate`, `ipm`,
`expenditure_per_capita`, `participation_rate`), recompute the pipeline with that
indicator removed:
- For the 3 vulnerability-trio indicators: refit `fit_pca_composite()` on the
  remaining 2, which changes both the loadings and the variance-explained
  diagnostic — report the new variance explained alongside the rank-shift metrics,
  since a 2-indicator PCA losing much less variance than the 3-indicator version
  (86.0% baseline, per the dry run) would itself be informative about which
  indicator was carrying unique signal.
- For `participation_rate`: removing it collapses `education_access` entirely,
  making every province's NPI equal to `socioeconomic_vulnerability` alone — this
  LOIO variant is structurally identical to the "100% vulnerability" case the 4
  partial-coverage provinces already experience permanently (§3), so this test
  doubles as a check on whether that already-degraded case behaves sensibly for the
  other 34 provinces too.
- Reports the same Spearman/top-decile/largest-single-shift metrics as §2 and §3.

## Reporting (when this is run, not now)

All four checks write to one generated `docs/phase4_validation_report.md` (numbered
Phase 4 since running it produces the rank comparisons Phase 3 is stopping before),
following this project's standing convention that generated reports are written by
code from real computed output (`docs/data_inventory.md`,
`docs/missing_data_report.md`) — never hand-assembled. The report should present
correlation coefficients, overlap percentages, and named largest-shift provinces, but
should still avoid presenting a full sorted province list unless and until publishing
a ranking is separately authorized.

## Readiness

Every function named above has a direct, already-built dependency to call
(`compute_npi()`, `fit_pca_composite()`, the config files) — no further pipeline code
is needed to implement `src/scoring/validation.py` itself, only the validation
functions described here plus tests against small fixtures (mirroring
`tests/test_scoring.py`'s existing pattern). This is recorded as a build task for
the next phase, not built in this one.
