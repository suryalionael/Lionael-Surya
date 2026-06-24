# Phase 4 — Ranking and Priority Tier Design

Designs how the continuous NPI score (now computed via the expenditure-only primary
methodology approved in `docs/phase3_final_methodology_decision.md`) becomes a rank,
percentile, and priority tier. Written before generating the final results
(`docs/phase4_ranking_results.md`) so the tiering method is chosen on stated
evidence, not picked after seeing which one looks best.

## Score distribution (real, computed — the evidence this design reasons from)

| Statistic | Value |
|---|---|
| n | 38 |
| mean | 0.364 |
| std | 0.204 |
| min | 0.008 |
| 25th pct | 0.274 |
| median | 0.302 |
| 75th pct | 0.372 |
| max | 1.000 |
| **skewness** | **1.70 (strongly right-skewed)** |

Most provinces cluster tightly between roughly 0.27 and 0.40, with a smaller number
of provinces stretching the distribution's right tail out to 1.0. **Any tiering
method that ignores this shape will produce misleading groups** — this is the
central fact the four candidate methods below are evaluated against.

## Rank and percentile

`src/scoring/ranking.py::add_rank_and_percentile()`: rank 1 = highest NPI = most
vulnerable (ties broken by `method="min"`, so tied provinces share the better rank
rather than being arbitrarily ordered); percentile 0–100, 100 = most vulnerable.
Both are null, never fabricated, for any province with a null score (not currently
applicable — `expenditure_per_capita` has zero missing values across all 38
provinces, per `docs/phase2_indicator_audit.md` — but implemented defensively in
case a future methodology change reintroduces a gap).

## Candidate tiering methods — evaluated against the real distribution above

### 1. Quartile (equal-count, 4 groups)

Real result: Low 10 / Medium 9 / High 9 / Critical 10 — breakpoints at 0.274 / 0.302
/ 0.372.

- **Advantages:** simplest to explain ("the bottom fourth, the next fourth, ...");
  every tier has a similar, predictable size, which is convenient for capacity
  planning (e.g. "we can fund the Critical quartile this year").
- **Disadvantages:** **forces 4 provinces into "Critical" and 4 (well, by
  construction, equal counts) into "Low" regardless of whether the data actually
  supports a 4-way split.** Given the real skew, this method draws a breakpoint at
  0.302 — right in the middle of the dense cluster most provinces sit in — meaning
  two provinces separated by a tiny, possibly statistically meaningless difference
  can land in different tiers purely because of where the equal-count line falls.

### 2. Quintile (equal-count, 5 groups)

Real result: Very Low 8 / Low 7 / Medium 8 / High 7 / Very High 8 — breakpoints at
0.254 / 0.291 / 0.329 / 0.391.

- **Advantages:** same equal-count convenience as quartiles, finer granularity.
- **Disadvantages:** the same core problem as quartiles, worse — four breakpoints
  packed between 0.254 and 0.391 means most of these cut lines fall *inside* the
  same dense cluster, splitting near-identical provinces into different tiers even
  more often than quartiles do.

### 3. Natural breaks (Jenks)

Real result (4 classes): Low 4 / Medium 20 / High 9 / Critical 5 — breakpoints at
0.183 / 0.330 / 0.438.

- **Advantages:** **the only method of the four whose group sizes are determined by
  the data's actual structure rather than imposed on it.** The 20-province "Medium"
  cluster reflects the genuine dense cluster identified above; the 5-province
  "Critical" group is a real, separated high-end cluster, not an artificially
  equal-sized slice. This is the most defensible "evidence-based" tiering per this
  project's explicit requirement, because the breaks are *derived from* evidence
  (within-group variance minimization) rather than chosen independently of it.
- **Disadvantages:** breakpoints are **not stable across years** — refitting Jenks
  on next year's data could shift every cutoff, including which provinces sit right
  at a boundary. Harder to explain to a non-technical audience than "the top
  quarter": "the algorithm found a natural gap in the data" is a less intuitive
  sentence than "the top 25%." Group sizes are unpredictable in advance, which is
  inconvenient for fixed-capacity program planning.

### 4. Policy-threshold (fixed equal-interval cutoffs: 0.25 / 0.5 / 0.75)

Real result: Low 7 / Medium 26 / High 1 / Critical 4.

- **Advantages:** cutoffs are fixed, round numbers, stable across years and
  trivially explainable ("score above 0.75 is Critical") — and, unlike the other
  three methods, **the same threshold can be applied consistently to a future
  year's data without ever needing to recompute breakpoints.**
- **Disadvantages:** **performs the worst of the four against this specific
  dataset's actual shape.** Because the real scores cluster well below 0.5, this
  method dumps 26 of 38 provinces (68%) into a single "Medium" tier and only 1
  province into "High" — providing almost no discrimination among the large
  majority of the country. A fixed threshold chosen without reference to the
  data's distribution can silently fail this badly, and did, on real evidence
  here.

## Decision: Jenks (natural breaks) is the primary tiering method

Chosen specifically because **this project's tier requirement is "evidence-based,"
and Jenks is the only method of the four whose tier boundaries are derived from
the actual evidence (the score distribution's own structure) rather than imposed
independently of it.** The real comparison above shows this isn't a marginal
call: the fixed-threshold method's 26-province "Medium" bucket is a concrete
demonstration of what goes wrong when a tiering method ignores distribution shape,
and the equal-count methods' breakpoints landing inside the dense cluster show the
same underlying problem in a milder form.

**Quartile is retained as a secondary, familiar reference tier** in the final
output (`data/processed/npi_rankings.csv` carries all four tier columns, not just
the chosen one) — specifically because its "predictable group size" property that
counted against it as the *primary* method is genuinely useful for a reader who
wants a simple, year-over-year-comparable cut without engaging with Jenks's
data-dependent breakpoints. Quintile and policy-threshold are reported for
transparency and completeness but are not recommended as primary, for the reasons
in §2 and §4 above.

## Robustness diagnostics to run (executed for real in `docs/phase4_ranking_results.md`)

Per this phase's requirement, four stability checks, building directly on the
infrastructure already validated in Phase 3B/3C:

1. **Ranking stability** — Spearman rank correlation of the full ordering under
   weight perturbation (reusing `src/scoring/validation.py::weight_sensitivity_grid`,
   now run against the expenditure-only primary instead of the PCA benchmark).
2. **Top-5 stability** and **3. Top-10 stability** — overlap fraction at both cut
   sizes, since `docs/phase3_final_methodology_decision.md` already found PCA and
   expenditure-only can diverge more below the top-10 than within it.
3. **Tier stability** — `src/scoring/validation.py::tier_stability()`, applying the
   chosen Jenks tiering to both the baseline and each weight-perturbed/PCA-benchmark
   variant, and counting how many provinces cross a tier boundary. This is a
   distinct question from rank stability: a province can move several ranks without
   crossing a tier boundary, or move one rank and cross one.

## Caveats and uncertainty carried into the results document

- **Tier boundaries are themselves estimates, not fixed truths** — Jenks
  breakpoints depend on this exact 38-province, single-year snapshot.
- **Missing-data impact:** none for the primary methodology specifically —
  `expenditure_per_capita` has zero missing values, so no province's tier
  assignment in the primary ranking is affected by the missing-data policy in
  `docs/phase3_missing_data_decision.md`. That policy remains relevant only for the
  PCA benchmark and the Education Access dimension, both reported as secondary
  context, not the primary tier.
- **A province sitting close to a Jenks breakpoint should be treated as
  tier-ambiguous**, not confidently classified — the results document flags any
  province within a small margin of a boundary explicitly.
