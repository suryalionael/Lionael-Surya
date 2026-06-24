# Phase 3B — Validation Results

Executes the procedures specified in `docs/phase3_validation_design.md` against the
real pipeline (`src/scoring/validation.py`) and the real merged dataset (38
provinces). Every number below is computed, not illustrative.

**Convention used throughout this document, stated explicitly because some of these
checks inherently require comparing province orderings to measure stability:** no
full sorted province list, percentile, or priority tier appears anywhere in this
report. Where a specific province is named, it is named because it is the subject of
a *stability/instability finding* (e.g. "this province's rank is unusually sensitive
to indicator X"), never as part of a presented ranking. Internal rank computation is
a measurement tool here, not a publication.

## 1. Outcome Validation

Spearman correlation is the primary metric (rank-based, robust to the right-skewed
NPI distribution noted in `docs/phase3_dry_run.md`); Pearson is reported alongside
since the brief asked for both.

| Metric | All 38 provinces | Full-coverage provinces only (34) |
|---|---|---|
| Pearson r | 0.643 (p = 1.3e-05) | 0.453 |
| Spearman r | 0.717 (p = 4.1e-07) | 0.633 |

**Both are statistically significant and at least moderately strong — this passes
the pre-registered threshold from `docs/phase3_validation_design.md` (Spearman r >
0.5).** But the full-coverage-only figures are honestly weaker than the all-38
figures (Pearson drops from 0.64 to 0.45). This is not the index "performing worse
on better data" — it's because the 4 partial-coverage provinces (scored on
Socioeconomic Vulnerability alone, per the renormalization policy) include some of
the most extreme poverty/IPM/expenditure values in the dataset *and* some of the
most extreme stunting rates, which mechanically strengthens the pooled correlation.
**The honest correlation to trust for the bulk of the country is the 34-province
figure (Pearson 0.45, Spearman 0.63), not the inflated 38-province figure.**

### Scatter diagnostics (linear fit: stunting_rate ≈ 19.08 × npi + 17.98)

Four provinces have standardized residuals with |z| > 1.5 — real outcomes diverging
meaningfully from what the input-driven NPI alone predicts:

| Province | NPI | Actual stunting | Residual | Interpretation |
|---|---|---|---|---|
| Nusa Tenggara Timur | 0.351 | 37.0% | +12.3 (z=+2.42) | Actual stunting far worse than risk factors alone predict — suggests a driver outside this dataset's 4 input indicators (program delivery, geography, etc.) |
| Sulawesi Barat | 0.276 | 35.4% | +12.1 (z=+2.38) | Same pattern as NTT |
| Papua | 0.763 | 24.7% | -7.8 (z=-1.54) | Actual stunting notably *better* than its high risk-factor score predicts |
| Bali | 0.080 | 8.7% | -10.8 (z=-2.12) | Already the lowest-risk province; actual outcome is even better than predicted |

NTT and Sulawesi Barat are the two clearest "outcomes worse than risk factors
explain" cases — exactly the kind of signal this validation step was designed to
surface (per `docs/phase2_sensitivity_design.md`'s residual-analysis rationale): a
policy-relevant flag to investigate local implementation factors, not a flaw in the
index.

## 2. Weight Sensitivity

Grid: Socioeconomic Vulnerability share at 30%/40%/50% (baseline)/60%/70%
(Education Access taking the complement), top-4 used as the "short list" size (per
`docs/phase3_validation_design.md`'s rationale that top-10 is too large a fraction
of a 38-province country to be a meaningful short list).

| Perturbation | Weights (Vuln:Educ) | Rank Spearman r vs. baseline | Top-4 overlap | Largest single shift |
|---|---|---|---|---|
| -20% | 30:70 | 0.991 | 4/4 | 4 ranks |
| -10% | 40:60 | 0.997 | 4/4 | 3 ranks |
| 0% (baseline) | 50:50 | 1.000 | 4/4 | 0 |
| +10% | 60:40 | 0.999 | 4/4 | 1 rank |
| +20% | 70:30 | 0.997 | 4/4 | 2 ranks |

**The NPI is highly robust to the top-level weighting choice across the full ±20%
range tested:** rank correlation never drops below 0.99, and the top-4 set is
identical at every grid point. This is a strong robustness result for the specific
methodological choice made in `docs/phase2_weighting_options.md` (equal weighting
across the two top-level dimensions) — even a meaningfully different weighting
philosophy wouldn't materially change who shows up at the top.

## 3. Leave-One-Indicator-Out Analysis

| Dropped indicator | Rank Spearman r vs. full | Top-4 overlap | Largest shift | PCA variance explained (with → without) |
|---|---|---|---|---|
| `poverty_rate` | **0.948** (lowest) | **3/4** (only case where top-4 membership changes) | Jawa Timur, 9 ranks | 86.0% → 94.0% |
| `ipm` | 0.988 | 4/4 | Di Yogyakarta, 5 ranks | 86.0% → 87.1% |
| `expenditure_per_capita` | 0.985 | 4/4 | Kalimantan Utara, 6 ranks | 86.0% → 90.8% |
| `participation_rate` | 0.989 | **2/4** (largest top-4 churn of any test in this report) | Papua, 5 ranks | n/a (collapses education_access entirely) |

**`poverty_rate` is the most influential indicator** by every metric here (lowest
rank correlation, only case where the top-4 *set* actually changes, largest single
province shift) — consistent with it also carrying the highest PCA loading (0.715,
`docs/phase3_dry_run.md`). Two independent diagnostics agreeing is meaningful
corroboration, not a coincidence.

**`participation_rate`'s removal is a separate, important finding:** its aggregate
rank correlation (0.989) looks almost as stable as `ipm`'s or `expenditure_per_
capita`'s removal — but its top-4 overlap (2/4) shows the *most* churn of any test
in this report. **Aggregate Spearman correlation alone would have hidden this.**
Removing Education Access entirely doesn't move the bulk of the country much, but
it does change which provinces sit at the very top — exactly the part of the output
a policymaker would look at first. This is the clearest argument in this whole
validation exercise for *keeping* Education Access as a dimension rather than
demoting it to a reported-only indicator, despite its weak raw correlation with
`stunting_rate` (r = -0.16, noted in the indicator audit) — its operational/ranking
relevance is higher than its statistical correlation alone would suggest.

## 4. PCA Stability (leave-one-province-out)

Refit the Socioeconomic Vulnerability PCA 38 times, each excluding one province,
and compared loadings to the full-data fit (loadings: `poverty_rate` 0.715, `ipm`
0.511, `expenditure_per_capita` 0.478; 86.0% variance explained).

| Statistic | Value |
|---|---|
| Mean loading shift (L2 distance) across all 38 leave-one-out refits | 0.0099 |
| Max loading shift | 0.0773 (Dki Jakarta) |
| Std of loading shift | 0.0181 |

**The PCA basis is highly stable — no single province's exclusion meaningfully
changes what "Socioeconomic Vulnerability" means.** The largest shifts are small in
absolute terms (0.077 out of loadings on a unit-norm scale) and belong to exactly
the three provinces already flagged as statistical extremes in
`docs/phase3_dry_run.md`'s outlier review: **Dki Jakarta** (shift 0.077, the
extreme low-vulnerability end), **Papua Tengah** (0.066), and **Papua Pegunungan**
(0.061) (the extreme high-vulnerability end). Three independent diagnostics — the
raw-indicator IQR outlier check, the composite-score outlier check, and this
leave-one-province-out PCA stability check — all converge on the same three
provinces. That convergence is itself evidence the PCA composite is behaving
sensibly (reacting most to genuinely extreme real data, not to noise), not a sign of
instability.

## Limitations

- **The full-coverage-vs-all-38 correlation gap (§1) means the headline 0.72
  Spearman figure partly reflects the 4 partial-coverage provinces' extremity, not
  uniformly strong predictive power across the whole country.** Any future
  publication of this index should report the 34-province figure as the honest
  baseline.
- **All sensitivity checks here perturb only the top-level dimension split and
  single-indicator removal — not the PCA method itself** (e.g. not compared against
  a non-PCA alternative like picking one representative indicator, which
  `docs/phase2_weighting_options.md` named as a simpler fallback). That comparison
  is not yet done.
- **Single-year cross-section.** Every check here is internal to one snapshot of
  data; none of it validates temporal stability (whether next year's data would
  produce a similar index), which `docs/phase2_sensitivity_design.md` separately
  flagged as untested.
- **n = 38 is a small sample for PCA and correlation statistics generally** — the
  leave-one-province-out check (§4) partially compensates by showing no single
  province dominates, but small-n caveats apply to every coefficient in this report.

## Interpretation

The methodology is **robust to the specific judgment calls this project's
researcher made** (the 50:50 weighting choice, the PCA-for-collinearity approach)
and **honestly correlated with real outcomes**, with the important caveat that the
correlation is meaningfully weaker once the 4 partial-coverage provinces are set
aside. The most actionable finding is the asymmetry between `poverty_rate` (high
influence, corroborated two ways) and `participation_rate` (weak raw correlation
with the outcome, but disproportionate effect on *which provinces rank at the top*)
— both are worth flagging explicitly if this methodology is presented to a
non-technical audience.
