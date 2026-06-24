# Phase 3 — Missing Data Decision

Resolves the methodological decision flagged as a Phase 3 prerequisite in
`docs/phase2_technical_design.md`: how to handle `population` and
`participation_rate` being null for the 4 provinces created by Indonesia's 2022
Papua split (Papua Selatan, Papua Tengah, Papua Pegunungan, Papua Barat Daya), per
`docs/missing_data_report.md`. This decision must be made before `npi.py` can run, so
it precedes the Part B dry run in this same document set.

## Why this can't be resolved the same way for both indicators

The two missing indicators play different roles in the framework
(`docs/phase2_framework_design.md`):

- `participation_rate` is one of the NPI's two **weighted input dimensions**
  (Education Access). Missing it removes one of two numbers that get summed into
  the score.
- `population` is **not a weighted input** — it's the Reach Modifier, used
  multiplicatively after the NPI score exists (`population × stunting_rate`,
  `population × NPI percentile`), never summed into it.

So this decision has two parts, evaluated together below but resolved separately at
the end.

## Options evaluated

### 1. Exclude affected provinces

Drop the 4 provinces from the index entirely; report them separately as
"insufficient data."

- **Statistical implications:** clean — no missing-value handling needed downstream,
  no risk of an artificial score distortion.
- **Policy implications:** **actively counterproductive for this project's stated
  mission.** Papua Pegunungan has the highest `stunting_rate` in the entire dataset
  (40.0%, "Sangat Tinggi" — the only province in that top category;
  `docs/phase2_indicator_audit.md` §6). Excluding it from a *nutrition priority*
  index because one non-outcome input indicator is missing would remove the single
  most urgent province from consideration by exactly the tool meant to surface it.
- **Reproducibility implications:** simplest to reproduce, but the output is
  incomplete in a way that doesn't shrink over time (these provinces are new, not
  temporarily missing — BPS has no historical series for them to eventually fill in
  retroactively for past years, though future years should resolve this).
- **Risk of bias:** systematically biased *against new administrative units* —
  any future province split would recreate this exact problem and silently drop the
  newest, often least-developed, provinces from the analysis. Rejected.

### 2. Renormalize available indicators

Recompute each affected province's score using only the dimensions it has data for,
rescaling weights so they still sum to 1.

- **Statistical implications:** the 4 provinces' scores become a function of fewer
  inputs than the other 34 provinces' scores — not perfectly comparable on a strict
  apples-to-apples basis, but every number used is real and actually measured for
  that province.
- **Policy implications:** keeps every province in the index, including Papua
  Pegunungan. A transparency flag (see Recommendation) lets a policymaker see which
  provinces' scores rest on less complete data, rather than hiding the difference.
- **Reproducibility implications:** fully reproducible — the renormalization rule is
  a deterministic function of which inputs are present, no external judgment call
  needed per province.
- **Risk of bias:** a province's relative score shifts somewhat based on which
  dimensions happen to be available for it (e.g. relying 100% on Socioeconomic
  Vulnerability when Education Access is missing rather than 50/50) — a real but
  bounded and documented bias, not a fabricated value.

### 3. Parent-province inheritance

Assign the new province its parent's value (Papua → Papua Selatan/Tengah/Pegunungan;
Papua Barat → Papua Barat Daya, per the crosswalk in
`src/reference/province_gadm_crosswalk.csv`).

- **Statistical implications — specifically broken for `population`:** the
  `population` figures in this dataset are from **2020**, two years *before* the
  split existed. BPS's 2020 "Papua" figure (3,393.1 thousand) and "Papua Barat"
  figure (986.0 thousand) are **pre-split totals that already include the territory
  that is now the 4 new provinces.** Naively copying the parent's total to each
  child would not estimate the child's population — it would assign each child the
  *entire undivided parent total*, quadruple-counting (Papua's total would appear
  once for Papua itself and again for each of its 3 children). A *correct*
  inheritance would require apportioning the 2020 total by district-level
  population mapped to the new province boundaries — a real, knowable calculation,
  but one that needs a dataset this project does not currently have (district-level
  population crosswalked to the new province lines). Doing it without that data
  would mean inventing an apportionment, which is fabrication, not inheritance.
- **Policy implications:** for `participation_rate`, a "regional proxy" framing is
  more defensible (school participation rates are plausibly similar across a region
  before and after an administrative split) but it is still **not a real measured
  value for that specific province** — it's an assumption dressed as data, and a
  policymaker reading "Papua Selatan: 83.61%" would reasonably believe that number
  was measured in Papua Selatan, when it was not.
- **Reproducibility implications:** reproducible as a calculation, but encodes a
  substantive empirical assumption (the child resembles the parent) that isn't
  documented as data, which is a worse failure mode than a visible null — it looks
  more authoritative than it is.
- **Risk of bias:** highest of the four options. For `population` specifically, it
  is not just biased but **arithmetically wrong** given the pre/post-split timing
  mismatch. Rejected for `population`. For `participation_rate`, rejected on this
  project's standing real-data-only principle (`docs/known_limitations.md`,
  `docs/missing_data_report.md`'s existing "do not estimate by splitting the old
  combined figure" policy for this exact province group) — the project has already
  made this call once, for the same 4 provinces, in Phase 1.

### 4. Other defensible alternative considered: model-based imputation

(e.g. regression of `participation_rate` on correlated indicators for the 34
complete provinces, applied to predict the 4 missing ones.)

- Rejected outright, not weighed as seriously as 1-3: this is imputation by a more
  sophisticated name. These 4 provinces are newly-created entities with no
  comparable history to validate a model against, and any predicted value would be
  presented as if it were a measured one. Directly contradicts this project's
  absolute real-data-only rule (`CLAUDE.md`, `docs/known_limitations.md`).

## Recommendation

**Different treatment per indicator, matching its actual role — not one blanket
rule for both:**

1. **`participation_rate` (Education Access dimension): Option 2, renormalize.**
   For the 4 affected provinces, NPI = 100% Socioeconomic Vulnerability (the only
   available dimension) instead of the standard 50/50 split. This is the only option
   that keeps every province — including Papua Pegunungan, the dataset's highest
   stunting-rate province — in the index, without inventing a measured value that
   doesn't exist.
2. **`population` (Reach Modifier, not a weighted input): leave null, no
   renormalization needed.** Because `population` is never summed into the NPI score
   (it multiplies into a separate companion metric), there is no weight to
   renormalize — the Reach Modifier metrics are simply reported as unavailable for
   these 4 provinces, never estimated. This is consistent with Phase 1's existing,
   already-justified policy for this exact gap (`docs/missing_data_report.md`).
3. **Mandatory transparency requirement, regardless of the above:** every output
   table from `npi.py` onward must carry a `data_completeness` flag (e.g.
   `"full"` / `"partial: education_access unavailable"`) per province, so the
   distinction travels with the data through every later stage (validation,
   reporting, dashboard) instead of being a fact only visible in this document.

This recommendation is implemented in `src/features/missing_value_policy.py` and
exercised in the Part B dry run below.
