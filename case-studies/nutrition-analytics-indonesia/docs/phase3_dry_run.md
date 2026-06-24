# Phase 3 — Dry Run: Diagnostics Only, No Rankings

Runs the full scoring pipeline built in `src/features/` and `src/scoring/` against
the real Phase 1 merged dataset to produce diagnostic output: PCA loadings, variance
explained, indicator distributions, normalization diagnostics, and outlier review.

**This document deliberately does not sort, rank, or tier any province.** The
intermediate result (`data/interim/npi_dry_run.csv` — gitignored, like all
`data/interim/` content) does contain a real, computed `npi` value per province,
because the validation work in `docs/phase3_validation_design.md` and any future
sensitivity analysis genuinely needs that continuous score to exist. But it is
written in source province order, with no `rank`, `percentile`, or `priority_tier`
column — turning these scores into an ordered, published ranking is an explicitly
separate, not-yet-authorized step.

## Pipeline run

```
merged_provincial_indicators.csv (Phase 1, 38 provinces)
  -> align_to_higher_is_worse()        config/indicator_directionality.yml
  -> min_max_scale()                   per-indicator, nulls ignored when fitting
  -> fit_pca_composite()               poverty_rate, ipm, expenditure_per_capita -> socioeconomic_vulnerability
  -> min_max_scale() (rescale PCA output to [0,1] for interpretability)
  -> renormalize_weights_per_row()     config/npi_weights.yml + docs/phase3_missing_data_decision.md policy
  -> npi (continuous score) + data_completeness flag + estimated_children_affected
```

Ran successfully end-to-end against all 38 provinces, 0 exceptions.

## PCA loadings and variance explained

| Indicator | Loading |
|---|---|
| `poverty_rate` | 0.715 |
| `ipm` | 0.511 |
| `expenditure_per_capita` | 0.478 |

**Variance explained by the first component: 86.0%.** Well above the 50% threshold
`pca_composite.py` enforces — confirms the audit's finding
(`docs/phase2_indicator_audit.md` §7) that these three indicators are genuinely
collinear enough to justify a single composite, not three independent inputs. All
three loadings came out positive under the forced sign convention (higher composite
= more vulnerable), with `poverty_rate` contributing the most to the composite.
38/38 provinces had complete data for this fit — no exclusions needed (poverty,
IPM, and expenditure are the three indicators with zero missing provinces, per
`docs/missing_data_report.md`).

## Normalization diagnostics (real min/max used for scaling)

| Indicator | Min (post-alignment) | Max (post-alignment) | n present | n missing |
|---|---|---|---|---|
| `poverty_rate` | 3.42 | 29.45 | 38 | 0 |
| `ipm` (flipped) | -83.08 | -53.42 | 38 | 0 |
| `expenditure_per_capita` (flipped) | -20,676 | -5,861 | 38 | 0 |
| `participation_rate` (flipped) | -99.76 | -83.61 | 34 | 4 |

(`ipm`, `expenditure_per_capita`, and `participation_rate` are shown post-flip,
since they're `higher_is_better` in the raw data and get negated before scaling so
every indicator points "higher = worse," per
`config/indicator_directionality.yml`.)

## Data completeness

| Status | Count |
|---|---|
| `full` | 34 |
| `partial: education_access unavailable` | 4 |

Exactly the 4 provinces identified in `docs/phase3_missing_data_decision.md`
(Papua Selatan, Papua Tengah, Papua Pegunungan, Papua Barat Daya) — confirms the
renormalization policy engaged precisely where expected and nowhere else.

## NPI score distribution (statistics only, not a ranking)

| Statistic | Value |
|---|---|
| count | 38 |
| mean | 0.264 |
| std | 0.225 |
| min | 0.008 |
| 25% | 0.152 |
| 50% (median) | 0.191 |
| 75% | 0.256 |
| max | 1.000 |

Right-skewed (mean > median) — most provinces cluster at lower vulnerability with a
smaller number of high-vulnerability provinces pulling the mean up. This shape is
expected for socioeconomic indicators and is reported here purely as a distribution
diagnostic.

## Outlier review (IQR method, 1.5×IQR fences — diagnostic, not prioritization)

Per-indicator outliers (statistical extremes in the *raw, pre-normalization* data):

| Indicator | Outlier provinces (value) |
|---|---|
| `poverty_rate` | Papua Pegunungan (27.21), Papua Tengah (29.45) |
| `ipm` | Di Yogyakarta (81.55), Dki Jakarta (83.08), Papua Pegunungan (53.42), Papua Tengah (59.75) |
| `expenditure_per_capita` | Dki Jakarta (20,676), Papua Pegunungan (5,861) |
| `participation_rate` | Papua (83.61), Papua Barat (98.41), Sulawesi Barat (98.31), Sulawesi Tengah (98.34) |

Outliers on the **Socioeconomic Vulnerability composite** itself: Dki Jakarta
(0.000 — the extreme *low*-vulnerability end), Papua Tengah (0.928), Papua
Pegunungan (1.000 — the extreme *high*-vulnerability end). This is consistent
across both the raw-indicator outlier check and the composite — Dki Jakarta and the
two newest, highest-poverty Papua provinces sit at the statistical extremes of
*every* socioeconomic measure in this dataset, not just one. That consistency is a
data-quality signal worth noting (it is not an artifact of one indicator behaving
oddly), but is reported here as a distributional fact about the input data, not as
a priority conclusion.

## What this dry run did not do

- No row was sorted, ranked, or assigned a percentile or priority tier.
- No "top N" or "lowest N" list was produced or displayed.
- The Reach Modifier's percentile-dependent variant (`population × NPI percentile`,
  per `docs/phase2_technical_design.md`) was not computed — it requires a rank-based
  transform, deferred along with ranking itself. Only `estimated_children_affected`
  (`population × stunting_rate`, which needs no ranking) was computed, and even that
  is reported as a per-province statistic, not sorted.
