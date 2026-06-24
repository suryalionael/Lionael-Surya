# Phase 2 — Sensitivity Analysis Design

Defines the methodology Phase 3 must implement to answer three questions before the
NPI is treated as reliable enough to inform real prioritization decisions. No
sensitivity analysis is run here — this is the design only, per Phase 2 scope.

## Question 1 — How sensitive is the ranking to weights?

**Method: weight-perturbation analysis.**

1. Compute the NPI under the recommended hybrid weighting
   (`docs/phase2_weighting_options.md`) as the baseline ranking.
2. Recompute under each alternative considered in that document (pure equal
   weighting, pure PCA-based weighting) and under a grid of perturbations to the
   top-level dimension split (e.g. Socioeconomic Vulnerability:Education Access at
   70:30, 60:40, 50:50, 40:60, 30:70, rather than only the recommended 50:50).
3. For each variant, compute:
   - **Spearman rank correlation** against the baseline ranking (overall stability).
   - **Top-10 membership overlap** — how many provinces stay in the top 10 priority
     list across variants (what a policymaker actually acts on is usually a cutoff
     list, not an exact rank number).
   - **Largest single-province rank shift** — identifies which province's
     prioritization is least robust to the weighting choice, which matters more
     for that specific province's stakeholders than an aggregate stability number.
4. **Reporting threshold (to be set in Phase 3, not invented here without real
   numbers):** define in advance what counts as "stable" (e.g. Spearman r > 0.9
   and top-10 overlap > 8/10 across all variants) versus "weight-sensitive" —
   deciding this threshold after seeing the results would be a form of the same
   circularity problem flagged in the framework design.

## Question 2 — Which indicators drive the results?

**Method: leave-one-indicator-out (LOIO) analysis.**

1. Recompute the NPI once per indicator, omitting that indicator and renormalizing
   the remaining weights within its dimension.
2. Measure the same Spearman/top-10-overlap metrics as above, comparing each
   LOIO variant to the full-indicator baseline.
3. The indicator whose removal causes the largest ranking shift is the de facto
   "most influential" — report this explicitly rather than relying on raw weights
   alone, since within the Socioeconomic Vulnerability dimension the *effective*
   influence of `poverty_rate`, `ipm`, and `expenditure_per_capita` depends on the
   PCA loadings (§ weighting doc), not a simple 1/3 each.
4. Cross-check against the correlation matrix already computed in the indicator
   audit (§7) as a prior expectation: indicators with the strongest correlation to
   `stunting_rate` (`ipm`, `expenditure_per_capita`, `poverty_rate`, in that order)
   are expected a priori to also be the most influential in LOIO testing. If LOIO
   testing disagrees with this expectation, that disagreement itself is a finding
   worth investigating before trusting the index (it would suggest the PCA
   combination step is behaving unexpectedly).

## Question 3 — What assumptions create instability?

Four specific assumptions made in Phase 1/2's design are identified here as
candidates to stress-test, rather than treated as settled:

1. **"Most recent year per indicator" (Phase 1 merge design).** Indicators span
   2018 (`population`) to 2025 (`poverty_rate`, `expenditure_per_capita`) — up to a
   7-year gap. Test: recompute the NPI restricted to each indicator's *earliest*
   available year instead of latest, and compare rankings. A province whose rank
   changes materially between the "latest available" and "earliest available"
   versions is one where temporal misalignment, not real current risk, may be
   driving its position.
2. **Missing-value handling for the 4 new Papua provinces.** `population` and
   `participation_rate` are null for Papua Selatan, Papua Tengah, Papua Pegunungan,
   and Papua Barat Daya (`docs/missing_data_report.md`). Phase 3 must decide and
   test at least two policies: (a) renormalize that province's dimension weights
   over only its available indicators, vs. (b) exclude provinces with incomplete
   indicator coverage from the ranked list entirely (reporting them separately as
   "insufficient data"). Compare how much the 4 affected provinces' relative
   standing differs between these two policies — this is a real, known data gap
   (not a hypothetical), so this test is not optional.
3. **PCA basis stability.** The PCA loadings (§ weighting doc) are fit on this
   project's current 38-province, single-snapshot dataset. Test: re-fit PCA after
   removing each province one at a time (a leave-one-out stability check on the
   *loadings themselves*, distinct from Question 1's perturbation of the
   *top-level* weights) to confirm no single province disproportionately determines
   what "Socioeconomic Vulnerability" even means in this dataset.
4. **Tier-boundary fragility.** Once provinces are grouped into priority tiers
   (e.g. top quartile = "high priority"), check how many provinces sit within a
   small margin of a tier boundary under the baseline weighting. Provinces near a
   boundary should be flagged as "borderline" in any reporting, since a policymaker
   treating tier membership as a hard yes/no cutoff needs to know which provinces'
   classification is fragile.

## Outcome-correlation validation (face validity, not circular)

Because the framework design (`docs/phase2_framework_design.md`) deliberately keeps
`stunting_rate` out of the NPI's weighted inputs, it can be used here as an honest,
non-circular validation check:

1. Compute Spearman correlation between the final NPI ranking and the real
   `stunting_rate` ranking. A reasonably strong positive correlation is evidence the
   index is capturing real risk, not an artifact of the weighting choices; a weak
   or negative correlation would be a serious warning sign requiring the framework
   itself to be revisited before any policy use.
2. Compute the residual for each province (actual `stunting_rate` rank minus
   NPI-predicted rank). Provinces with large positive residuals (worse outcomes than
   their risk factors predict) and large negative residuals (better outcomes than
   predicted) are themselves a policy-relevant output — the former may indicate
   program-delivery or local-implementation problems worth investigating beyond
   what national-level indicators capture; the latter may indicate effective local
   practices worth studying and replicating.

## Reporting format (for Phase 3)

All of the above should be reported as a single `docs/phase3_sensitivity_report.md`
(or equivalent), generated by code, not hand-written — consistent with this
project's existing practice of generating `docs/data_inventory.md` and
`docs/missing_data_report.md` from real pipeline runs rather than writing them by
hand. It should include, at minimum: the weight-perturbation table, the LOIO
ranking-shift table, the four assumption stress-tests above, and the outcome-residual
table — each with the real numbers from real computation, not placeholders.
