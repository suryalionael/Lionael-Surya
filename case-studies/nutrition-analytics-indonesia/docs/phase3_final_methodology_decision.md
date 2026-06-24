# Phase 3C Final Extension — PCA vs. Expenditure-Only Deep Dive and Final Decision

`docs/phase3_methodology_comparison.md` found that `expenditure_per_capita` alone
correlates with real stunting outcomes at least as well as the PCA composite and
preserves the same top-5 provinces with the smallest divergence of the three
single-indicator alternatives tested — making it the only alternative worth a full
head-to-head against PCA. This document runs that head-to-head and makes the final
methodology call. Same convention as the prior two validation documents: no full
province list or published ranking appears below; named provinces are robustness
findings, not a ranking.

## 1. Weight sensitivity (±20% grid, top-10)

| Perturbation | PCA: rank r vs. its own baseline | PCA: top-10 overlap | Expenditure-only: rank r vs. its own baseline | Expenditure-only: top-10 overlap |
|---|---|---|---|---|
| -20% | 0.991 | 9/10 | 0.992 | 10/10 |
| -10% | 0.997 | 9/10 | 0.998 | 10/10 |
| 0% (baseline) | 1.000 | 10/10 | 1.000 | 10/10 |
| +10% | 0.999 | 9/10 | 0.996 | 9/10 |
| +20% | 0.997 | 9/10 | 0.993 | 9/10 |

**Both methodologies are essentially equally robust to the top-level weighting
choice** — neither degrades meaningfully faster than the other across the full
±20% range tested. Weight sensitivity is not a differentiator between them.

## 2. Top-10 stability: PCA vs. Expenditure-only directly

| Metric | Value |
|---|---|
| Rank Spearman r (PCA vs. Expenditure-only) | 0.940 |
| Top-10 overlap | 9/10 (90%) |
| Largest single shift | Maluku Utara, 9 ranks |

Consistent with the top-5 result in `docs/phase3_methodology_comparison.md`
(5/5 overlap there) — the two methodologies agree closely at the very top and
diverge somewhat further down, never dramatically.

## 3. Leave-one-indicator-out: structural relevance, not a repeated grid

LOIO does not apply symmetrically to the two methodologies, and that asymmetry is
itself the finding:

- **PCA** combines 3 indicators with row-wise **complete-case** logic
  (`src/scoring/pca_composite.py`: `normalized_df[columns].notna().all(axis=1)`) — a
  province missing even *one* of `poverty_rate`/`ipm`/`expenditure_per_capita`
  would be entirely excluded (NaN) from Socioeconomic Vulnerability under PCA. With
  today's data this never triggers (all three are 100% complete across all 38
  provinces, confirmed in `docs/phase2_indicator_audit.md`), but it is a real,
  latent fragility: if any one of the three ever develops a publication gap the way
  `population`/`participation_rate` already have for the 4 newest Papua provinces
  (`docs/missing_data_report.md`), PCA would lose the *entire* dimension for the
  affected provinces, not just one-third of its input.
- **Expenditure-only** depends on exactly one indicator. It has no redundancy to
  lose — but also nothing to lose *gracefully*: if `expenditure_per_capita`
  specifically ever went missing, the dimension fails completely, with no fallback
  to `poverty_rate` or `ipm` the way PCA could (in principle) fall back to 2 of 3
  indicators if its complete-case restriction were relaxed in a future revision.

**Net assessment: PCA's theoretical redundancy advantage is not currently realized
in code** (the complete-case implementation forfeits it), so on the *current*
implementation, neither methodology is meaningfully more resilient to a future
missing-data gap than the other — this is a property of the implementation, not an
inherent property of "PCA" as a method, and is recorded here as a concrete
improvement opportunity if PCA is retained in any capacity (see Recommendation).

## 4. Outlier sensitivity

- **PCA** has a small but nonzero outlier-driven instability in its *fitting step*:
  `docs/phase3_validation_results.md` §4 found a maximum loading shift of 0.077
  (Dki Jakarta) across 38 leave-one-province-out refits — small, but real, because
  PCA's loadings are a function of which provinces are in the data.
- **Expenditure-only has zero such fitting-related sensitivity by construction** —
  there is no fitting step, so no province's presence or absence can shift "what the
  indicator means." Its only outlier exposure is that extreme real values
  (Dki Jakarta highest, Papua Pegunungan lowest, per the IQR check in
  `docs/phase3_dry_run.md`) land at the 0/1 extremes of the min-max scale — which is
  *correct* behavior for genuinely extreme real data, not instability.

**Expenditure-only is structurally immune to the one (small) instability mode PCA
has.**

## Decision matrix

Scored qualitatively against the evidence gathered across this and the prior two
validation documents (5 = clearly best, 3 = adequate/tied, 1 = clearly worst):

| Criterion | PCA | Expenditure-only | Evidence |
|---|---|---|---|
| Predictive performance | 3 | 4 | §1 of `phase3_methodology_comparison.md`: expenditure-only ahead on all 4 correlation figures, margins +0.01 to +0.03 |
| Interpretability | 2 | 5 | A "first principal component" requires explaining loadings and variance explained to a non-technical audience; "average spending per person" does not |
| Robustness | 3 | 4 | Tied on weight sensitivity (§1 above); expenditure-only has zero fitting-related outlier sensitivity (§4); PCA's complete-case LOIO fragility is currently latent, not active (§3) |
| Reproducibility | 3 | 5 | Both deterministic per-run; PCA's loadings are a function of the current dataset's covariance and could drift with future years' data (flagged in `docs/phase2_weighting_options.md`); expenditure-only has no fitted parameters to drift at all |
| Policy communication | 2 | 5 | Same gap as interpretability, specifically in the audience this project targets (recruiters, policymakers, non-technical stakeholders — `docs/phase2_framework_design.md`) |
| **Total** | **13/25** | **23/25** | |

## Final recommendation: Maintain both — Expenditure-only as primary, PCA as a documented sensitivity benchmark

Not a straight "replace PCA," and not "keep PCA as-is" — the evidence across all
three validation documents in this phase doesn't support either extreme cleanly:

- **Promote `expenditure_per_capita`-only to the primary methodology** for the
  Socioeconomic Vulnerability dimension. It wins or ties on every criterion in the
  decision matrix, with the gap being largest on exactly the two criteria
  (interpretability, policy communication) this project's stated audience cares
  about most.
- **Retain the PCA composite as a documented, regularly-recomputed sensitivity
  benchmark**, not delete it. Reasons this isn't simply "keep PCA equally as a
  second primary methodology": (a) it already exists, tested, and validated
  (Phases 3A-3B); (b) it provides an ongoing cross-check — if a future data update
  (new years, the 4 partial-coverage provinces eventually getting filled in) shifts
  the relationship between `poverty_rate`/`ipm`/`expenditure_per_capita`, comparing
  the two methodologies again would surface that shift immediately, whereas relying
  on expenditure-only alone would not; (c) the underlying textbook rationale for
  PCA (don't double-count collinear indicators) was correct and well-evidenced in
  `docs/phase2_indicator_audit.md` — it simply didn't translate into a *measurably
  better* index on this specific dataset's current snapshot, which is a fact about
  this dataset today, not a refutation of the method in general.
- **Tradeoff being accepted:** maintaining two methodologies costs more to document
  and explain than picking one cleanly, and risks the perception of not having a
  single clear answer. This is accepted because the alternative — quietly dropping
  PCA — would forfeit the early-warning value described above, and the alternative
  of keeping PCA as sole primary would mean shipping the *less* interpretable, *no
  better-performing* option to the audience this project is built for.

**Not implemented in this phase:** this document does not change
`config/npi_weights.yml` or any production code's default behavior — doing so is a
deliberate follow-up step requiring separate sign-off, consistent with this
phase's instruction to stop after the methodology decision rather than act on it
unilaterally.
