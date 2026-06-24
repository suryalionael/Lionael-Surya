# Phase 3C — Methodology Comparison: PCA vs. Single-Representative-Indicator

Compares the recommended PCA composite for Socioeconomic Vulnerability
(`docs/phase2_weighting_options.md`) against the simpler alternative named in that
same document but never previously tested for real: picking one representative
indicator (`poverty_rate`, `ipm`, or `expenditure_per_capita` alone) instead of
combining all three. `src/scoring/npi.py`'s `socioeconomic_single_indicator`
parameter implements the single-indicator path by bypassing PCA entirely and using
that one normalized indicator directly as the dimension score.

All four variants use the same Education Access dimension, the same 50:50 top-level
weighting, and the same renormalization policy for the 4 partial-coverage provinces
— only the construction of the Socioeconomic Vulnerability dimension differs. Same
convention as `docs/phase3_validation_results.md`: rank comparisons below are a
robustness-measurement tool, not a published ranking; no full province list is
shown.

## 1. Outcome correlation with `stunting_rate`

| Methodology | Pearson r (all 38) | Spearman r (all 38) | Pearson r (34 full-coverage) | Spearman r (34 full-coverage) |
|---|---|---|---|---|
| **PCA composite (current)** | 0.643 | 0.717 | 0.453 | 0.633 |
| Poverty only | 0.603 | 0.621 | 0.388 | 0.506 |
| IPM only | 0.650 | 0.666 | 0.449 | 0.568 |
| **Expenditure only** | **0.657** | **0.741** | **0.480** | **0.667** |

**Expenditure-only correlates with real stunting outcomes at least as well as the
PCA composite, on every one of the four correlation figures** — and slightly better
on three of the four. Poverty-only is the weakest of the four methods despite
`poverty_rate` carrying the highest PCA loading (0.715) and the largest
leave-one-indicator-out effect in `docs/phase3_validation_results.md` — a
genuinely interesting result discussed in §4.

## 2. Rank stability vs. the PCA baseline (top-5 used per this comparison's brief)

| Methodology | Rank Spearman r vs. PCA | Top-5 overlap | Largest single shift |
|---|---|---|---|
| Poverty only | 0.924 | 5/5 | Di Yogyakarta, 17 ranks |
| IPM only | 0.911 | 5/5 | Kalimantan Selatan, 13 ranks |
| **Expenditure only** | **0.941** (closest to PCA) | 5/5 | Maluku Utara, 9 ranks (smallest of the three) |

**Every alternative preserves the same top-5 set as PCA.** Below the top-5,
expenditure-only diverges from PCA the least (highest rank correlation, smallest
largest-single-shift), poverty-only and IPM-only diverge somewhat more. None of the
three single-indicator alternatives reorders the country dramatically relative to
PCA — the three economic indicators really are different views onto largely the
same underlying signal, consistent with the collinearity already established in
`docs/phase2_indicator_audit.md`.

## 3. Sensitivity behavior (qualitative here; quantitative deep-dive in
`docs/phase3_final_methodology_decision.md`)

`docs/phase3_validation_results.md` §2 already established that PCA's ranking is
robust to ±20% top-level weight perturbation (Spearman r > 0.99 throughout). Because
expenditure-only is the closest alternative to PCA by both outcome correlation and
rank stability (§1-2), it is the only one of the three single-indicator alternatives
carried forward for a full weight-sensitivity and leave-one-indicator-out comparison
against PCA — done separately in `docs/phase3_final_methodology_decision.md` rather
than repeating that grid for all three weaker alternatives.

## 4. Evaluation: interpretability, robustness, reproducibility, policy usefulness

| Criterion | PCA composite | Poverty only | IPM only | Expenditure only |
|---|---|---|---|---|
| **Interpretability** | Moderate — requires explaining a "component" and loadings to a non-technical audience (`docs/phase2_weighting_options.md` already flagged this as PCA's weakest property) | High — "poverty rate" is immediately understood | High — IPM is an internationally-recognized index, but is *already* a composite the audience may not realize bundles 3 sub-indicators itself | **Highest** — "average spending per person" is the most concrete, immediately graspable number of the four |
| **Robustness** | Statistically optimal use of all 3 indicators' shared signal (86.0% variance explained, `docs/phase3_dry_run.md`); validated stable in `docs/phase3_validation_results.md` | Single point-in-time poverty line is sensitive to where that line is drawn; weakest outcome correlation of the four | Robust as an index but inherits any volatility in its own 3 internal sub-components, invisibly | Single indicator, no cross-indicator averaging to smooth outliers — but in §1-2 it was in practice the *most* stable and best-correlated of the four |
| **Reproducibility** | Deterministic (`svd_solver="full"`) but the *loadings themselves* are a function of this dataset's current covariance structure — re-running with next year's data could shift them slightly (flagged as an open risk in `docs/phase2_weighting_options.md`) | Trivially reproducible — no fitting step at all | Trivially reproducible, but inherits IPM's *own* annual recalculation methodology, which this project doesn't control | Trivially reproducible — no fitting step at all |
| **Policy usefulness** | Defensible as "we used statistics to avoid double-counting," but that defense itself requires the audience to trust a method they may not follow | Immediately actionable ("focus where poverty is highest") but the weakest predictor of the four, real-world risk of pointing policy at the wrong provinces | Leverages an indicator policymakers already trust and use elsewhere, but as a *composite of a composite* if used inside another composite, transparency suffers | High — concrete, well-correlated with the actual outcome, and BPS already publishes it as a stand-alone development indicator |

## Does PCA provide meaningful value beyond the simpler alternatives?

**Mostly no, on the evidence gathered here.** PCA was adopted specifically to solve
the collinearity problem identified in the indicator audit — but expenditure-only
solves the *same* underlying problem (not double-counting 3 correlated indicators)
by simply not combining them at all, and does so while correlating *at least as
well* with real outcomes and preserving the *same* top-5 provinces as PCA. The
PCA composite's only remaining advantage over expenditure-only is using more of the
available data (3 indicators' combined signal instead of 1) and being the
methodologically "correct" answer to a multi-indicator collinearity problem in a
textbook sense — but this dataset's results don't show that translating into a
*measurably better* index by either of the two criteria (outcome correlation, rank
stability) this comparison was asked to test.

This finding — that a simpler method performs at least as well as the more
sophisticated one — is reported honestly rather than defended past what the
evidence supports, per this task's explicit instruction. A full head-to-head
between PCA and expenditure-only specifically (the strongest alternative found
here) is carried out in `docs/phase3_final_methodology_decision.md`, where the final
methodology choice is made.
