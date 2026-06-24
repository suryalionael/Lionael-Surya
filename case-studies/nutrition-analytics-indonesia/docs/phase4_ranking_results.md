# Phase 4 — Ranking Results

Real output from `python -m src.scoring.build_rankings`, methodology fixed by
`docs/phase4_ranking_design.md` (expenditure-only primary score, Jenks natural-breaks
as the primary tier). Full machine-readable output: `data/processed/npi_rankings.csv`
(38 provinces, all four tier methods, PCA benchmark score, rank, percentile).

## Methodology recap

- **Score:** NPI = 0.5 × Socioeconomic Vulnerability (`expenditure_per_capita`
  alone, min-max scaled, higher = more vulnerable) + 0.5 × Education Access
  (`participation_rate`, min-max scaled), renormalized per-province if a dimension
  is unavailable (`docs/phase3_missing_data_decision.md`).
- **Rank:** 1 = highest NPI = most vulnerable. **Percentile:** 100 = most
  vulnerable.
- **Primary tier:** Jenks natural breaks, 4 classes, breakpoints at **0.183 /
  0.330 / 0.438** (computed from this exact 38-province snapshot — see caveats).

## Full ranking

| Rank | Province | Percentile | NPI | Tier (Jenks) | Tier (Quartile) |
|---|---|---|---|---|---|
| 1 | Papua Pegunungan | 100.0 | 1.000 | Critical | Critical |
| 2 | Papua Tengah | 97.4 | 0.853 | Critical | Critical |
| 3 | Papua | 94.7 | 0.815 | Critical | Critical |
| 4 | Papua Barat Daya | 92.1 | 0.783 | Critical | Critical |
| 5 | Papua Selatan | 89.5 | 0.722 | Critical | Critical |
| 6 | Nusa Tenggara Timur | 86.8 | 0.438 | High *(boundary)* | Critical |
| 7 | Papua Barat | 84.2 | 0.432 | High *(boundary)* | Critical |
| 8 | Maluku Utara | 81.6 | 0.393 | High | Critical |
| 9 | Sulawesi Barat | 78.9 | 0.388 | High | Critical |
| 10 | Sulawesi Tengah | 76.3 | 0.373 | High | Critical |
| 11 | Maluku | 73.7 | 0.369 | High | High |
| 12 | Kalimantan Barat | 71.1 | 0.366 | High | High |
| 13 | Kalimantan Utara | 68.4 | 0.358 | High | High |
| 14 | Sulawesi Tenggara | 65.8 | 0.344 | High *(boundary)* | High |
| 15 | Aceh | 63.2 | 0.330 | Medium *(boundary)* | High |
| 16 | Gorontalo | 60.5 | 0.328 | Medium *(boundary)* | High |
| 17 | Lampung | 57.9 | 0.308 | Medium | High |
| 18 | Nusa Tenggara Barat | 55.3 | 0.305 | Medium | High |
| 19 | Sumatera Utara | 52.6 | 0.304 | Medium | High |
| 20 | Jambi | 50.0 | 0.301 | Medium | Medium |
| 21 | Bengkulu | 47.4 | 0.297 | Medium | Medium |
| 22 | Kalimantan Tengah | 44.7 | 0.292 | Medium | Medium |
| 23 | Sumatera Barat | 42.1 | 0.291 | Medium | Medium |
| 24 | Sulawesi Utara | 39.5 | 0.291 | Medium | Medium |
| 25 | Sumatera Selatan | 36.8 | 0.290 | Medium | Medium |
| 26 | Jawa Barat | 34.2 | 0.289 | Medium | Medium |
| 27 | Riau | 31.6 | 0.288 | Medium | Medium |
| 28 | Sulawesi Selatan | 28.9 | 0.275 | Medium | Medium |
| 29 | Jawa Tengah | 26.3 | 0.274 | Medium | Low |
| 30 | Jawa Timur | 23.7 | 0.257 | Medium | Low |
| 31 | Banten | 21.1 | 0.252 | Medium | Low |
| 32 | Kalimantan Selatan | 18.4 | 0.248 | Medium | Low |
| 33 | Kep. Bangka Belitung | 15.8 | 0.239 | Medium | Low |
| 34 | Kalimantan Timur | 13.2 | 0.220 | Medium | Low |
| 35 | Bali | 10.5 | 0.183 | Low *(boundary)* | Low |
| 36 | Kep. Riau | 7.9 | 0.176 | Low *(boundary)* | Low |
| 37 | Di Yogyakarta | 5.3 | 0.167 | Low *(boundary)* | Low |
| 38 | Dki Jakarta | 2.6 | 0.008 | Low | Low |

**8 of 38 provinces (21%) are flagged tier-boundary-ambiguous** (within 0.02 of a
Jenks breakpoint) — their Jenks tier should be read as approximate, not a confident
classification. Note the 5 newest-split Papua provinces sweep the entire "Critical"
tier under *both* Jenks and quartile methods — consistent with every prior
diagnostic in this project (the dry run's outlier review, the PCA leave-one-
province-out check) repeatedly flagging this same cluster as statistically extreme
on every economic indicator measured.

## Robustness diagnostics

### 1-3. Ranking, top-5, and top-10 stability under ±20% weight perturbation

| Perturbation | Rank Spearman r | Top-5 overlap | Top-10 overlap |
|---|---|---|---|
| -20% | 0.992 | 5/5 | 10/10 |
| -10% | 0.998 | 5/5 | 10/10 |
| 0% (baseline) | 1.000 | 5/5 | 10/10 |
| +10% | 0.996 | 5/5 | 9/10 |
| +20% | 0.993 | 5/5 | 9/10 |

**The rank order itself is highly robust** — consistent with every prior weight-
sensitivity test in this project (Phases 3B and 3C).

### 4. Tier stability — the most important finding in this document

**Jenks tier *labels* are dramatically less stable than the underlying rank order,
for a specific, identifiable reason: Jenks recomputes its breakpoints fresh against
whatever score distribution it's given.**

| Perturbation | Rank Spearman r (for reference) | Provinces changing Jenks tier (breakpoints **recomputed** each time) | Provinces changing tier vs. a **fixed** baseline breakpoint |
|---|---|---|---|
| -20% | 0.992 | 29/38 (76%) | 20/38 |
| -10% | 0.998 | 1/38 | 8/38 |
| +0% | 1.000 | 0/38 | 0/38 |
| +10% | 0.996 | 1/38 | 22/38 |
| +20% | 0.993 | 1/38 | 31/38 |

**Why these two columns disagree so much, and why that matters:** when Jenks is
*recomputed* on each perturbed score distribution, the algorithm adaptively
redraws its boundaries to fit whatever the new (slightly shifted) distribution
looks like — which can make tier assignments look artificially stable (only 1
province changes at ±10%/+20%) because the breakpoints move *with* the data,
masking real underlying score movement. Applying the *original, fixed* baseline
breakpoints instead — i.e. asking "did this province's score cross a fixed line in
the sand" — reveals far more actual movement (8 to 31 provinces, depending on
direction). **Neither column is "the" correct answer; they answer different
questions** (recomputed: "what would the natural groupings look like under this
scenario," fixed: "did this specific province's status change relative to today's
declared cutoffs") **and conflating them would materially mislead a reader about
how stable the tiers really are.**

**Practical consequence:** if this index is ever recomputed on a future year's
data, the choice of whether to refit Jenks fresh or hold this year's breakpoints
fixed is not a neutral implementation detail — it determines whether year-over-year
tier comparisons are even meaningful. This decision is recorded here as an open
question for any future production use, not resolved by this document.

### PCA benchmark vs. expenditure-only primary

| Metric | Value |
|---|---|
| Rank Spearman r | 0.940 |
| Top-5 overlap | 5/5 |
| Top-10 overlap | 9/10 |
| Jenks tier agreement (breakpoints independently recomputed for each methodology) | 12/38 (32%) |

**The two methodologies agree closely at the very top (same top-5, 9/10 in the
top-10) but only roughly a third of provinces land in the same Jenks tier when
each methodology's breakpoints are computed independently against its own score
distribution.** This is the same "recomputed breakpoints" effect as above, now
driven by the two methodologies producing genuinely different score
*distributions* (not just different rank orders) — `npi_pca_benchmark` is recorded
in `data/processed/npi_rankings.csv` precisely so this comparison remains
re-checkable.

## Caveats, uncertainty, and missing-data impact

- **Tier assignment is meaningfully less certain than rank order.** Treat the
  ranking (and percentile) as the more reliable output of this analysis; treat
  tier labels, especially for the 8 boundary-flagged provinces, as approximate.
- **Jenks breakpoints are a property of this exact 38-province, single-year
  snapshot** (0.183 / 0.330 / 0.438) — not a fixed standard that travels
  unchanged to a future year's data, per the tier-stability finding above.
- **Missing-data impact on the primary ranking: none.** `expenditure_per_capita`
  has zero missing values across all 38 provinces (`docs/phase2_indicator_audit.md`),
  so no rank, percentile, or tier in this ranking is affected by the renormalization
  policy from `docs/phase3_missing_data_decision.md`. That policy remains active
  only for the Education Access half of the score and for the PCA benchmark
  column, both secondary to the primary ranking.
- **`docs/phase3_validation_results.md`'s outcome-correlation caveat still
  applies**: the correlation between this score and real stunting outcomes is
  meaningfully weaker once the 4 newest Papua provinces are set aside (Pearson
  0.48 vs. 0.66 pooled) — their dominance of the "Critical" tier here is real and
  evidence-based, but the index's predictive power for the other 34 provinces is
  more modest than the headline figures would suggest.
- **This is a single-year cross-section.** No claim is made here about trend,
  trajectory, or how stable a province's *real-world* circumstances are over time
  — only how stable this specific computed score and tiering is under
  methodological perturbation.
