# Phase 2 — Framework Design: Nutrition Priority Index (NPI)

Designs the dimensional structure of the NPI using the findings from
`docs/phase2_indicator_audit.md`. No scores are calculated here — this is the
structural design only.

## The central design problem

The audit surfaced two structural issues that any naive 4-dimension framework
(Nutrition Risk / Economic Vulnerability / Human Development / Population Exposure,
applied literally) would inherit silently:

1. **Multicollinearity / double-counting.** `ipm`, `expenditure_per_capita`, and
   `poverty_rate` are not independent — `ipm` ↔ `expenditure_per_capita` r = 0.88,
   `ipm` ↔ `poverty_rate` r = -0.79. Treating "Economic Vulnerability" and "Human
   Development" as two separate, equally-weighted dimensions when they are built from
   overlapping signal would implicitly give the economic dimension roughly 2-3x its
   intended weight.
2. **Circularity.** `stunting_rate` is this project's outcome variable — what an
   intervention is meant to reduce — not a risk *factor*. Folding it into a "Nutrition
   Risk" input dimension alongside the others makes the index partly a restatement of
   the very thing it's supposed to help prioritize against, which weakens its value
   for explaining *why* a province is high-priority and makes later validation
   (checking the index against real stunting outcomes) circular.

Three candidate frameworks were evaluated against these two problems.

## Candidate frameworks

### Candidate 1 — Literal 4-dimension framework (as initially proposed)

Nutrition Risk (stunting_rate) + Economic Vulnerability (poverty_rate) + Human
Development (ipm) + Population Exposure (population), each as an equally-structured
additive dimension.

- **Pros:** simplest to explain in one sentence; matches the brief literally.
- **Cons:** inherits both structural issues above unmitigated. Population as an
  *additive* dimension also conflates *scale* with *severity* — a large, low-rate
  province could outscore a small, high-rate one for the wrong reason, which is a
  known pitfall in vulnerability indices and would be the first thing a careful
  policymaker or reviewer would flag.
- **Verdict: rejected as-is.** Kept as the explicit baseline to compare against.

### Candidate 2 — Minimalist 2-axis framework (Outcome vs. Capacity)

Collapse everything into two axes: "Current Burden" (stunting_rate) and "Structural
Capacity" (a single composite of everything else).

- **Pros:** maximally simple, avoids double-counting by construction.
- **Cons:** too coarse for policy use — collapsing poverty, development, and
  education into one undifferentiated "Capacity" number tells a policymaker *that*
  a province has low capacity but not *which lever* (income support? school feeding?
  general development?) is most actionable. Fails the "explainable to policymakers"
  bar in a different way: it's simple to compute but not useful to act on.
- **Verdict: rejected** — under-differentiated.

### Candidate 3 (Recommended) — Outcome-separated, collinearity-aware framework

Structurally separate the framework into an **Outcome Layer** (reported, not scored
as an input) and an **Input/Driver Layer** (what the index is actually built from),
plus a **Reach Modifier** (population, kept out of the additive score, used as a
companion lens):

**Outcome Layer (reported alongside the index, not part of its weighted sum):**
- `stunting_rate` / `stunting_category` — used for (a) face-validity checking the
  index against real outcomes (does high-NPI correlate with high actual stunting?
  see `docs/phase2_sensitivity_design.md`), and (b) flagging "outlier" provinces
  where actual stunting is much worse or better than the input-driven index would
  predict — itself a useful policy signal ("structural risk looks moderate here, but
  outcomes are bad — investigate local implementation/program-delivery factors").

**Input/Driver Layer (3 dimensions, what the NPI score is built from):**
1. **Socioeconomic Vulnerability** — `poverty_rate`, `ipm`, `expenditure_per_capita`
   treated as *one* dimension, not three, specifically because of their measured
   collinearity. How they're combined into a single dimension score (pick one
   representative indicator vs. a PCA-derived composite) is the subject of
   `docs/phase2_weighting_options.md`, not this document.
2. **Education Access** — `participation_rate` alone. Kept as its own dimension
   despite weak statistical correlation with stunting (r = -0.16) for an *operational*
   reason, not a statistical one: school-based nutrition programs (e.g. Makan Bergizi
   Gratis) are delivered through the education system, so a province's school
   participation rate is policy-relevant to *delivery feasibility* even where it isn't
   strongly predictive of *current* stunting outcomes. This distinction (statistical
   relevance vs. operational relevance) should be stated explicitly wherever this
   dimension is presented, so it isn't mistaken for a strong risk driver.
3. *(Population Exposure is deliberately not a third input dimension — see below.)*

**Reach Modifier (companion metric, not part of the additive score):**
- `population` is used to compute a separate **"estimated children potentially
  affected"** metric (population × stunting_rate, or population × NPI percentile)
  reported alongside the rate-based NPI, not summed into it. This preserves the NPI
  as a pure *rate/severity* ranking (so a small high-risk province isn't diluted by
  a population term) while still surfacing the scale dimension for policymakers who
  need to think about absolute reach, not just rate, when allocating a fixed program
  budget. This mirrors a standard practice in burden-of-disease and resource-allocation
  analysis: rank by rate for *where is it worst*, weight by population for *where do
  resources reach the most people* — and report both rather than collapsing them into
  one number.

### Why Candidate 3 is recommended

- Directly resolves both structural issues found in the audit, rather than leaving
  them as a known limitation.
- Still produces an actionable, explainable structure: a policymaker reading the
  output sees "this province ranks high on Socioeconomic Vulnerability and low on
  Education Access — and separately, here's its actual stunting rate and how many
  children that represents" — which is more useful than one blended number.
- Keeps the index honest for future validation: because the outcome variable isn't
  baked into the score, Phase 2's sensitivity-analysis work (`docs/
  phase2_sensitivity_design.md`) can meaningfully ask "does this index correlate with
  real outcomes?" without the answer being trivially "yes, partially, because it's
  partly the same number."

## Resulting structure (for Phase 3 implementation, not yet built)

```
NPI input dimensions (additive, weighted — weighting method: see phase2_weighting_options.md)
  1. Socioeconomic Vulnerability  <- poverty_rate, ipm, expenditure_per_capita (collinearity-aware combination)
  2. Education Access             <- participation_rate

Outcome layer (reported, not weighted into NPI)
  - stunting_rate, stunting_category

Reach modifier (companion metric, not weighted into NPI)
  - population x stunting_rate  ("estimated children affected")
  - population x NPI percentile ("estimated children in high-priority provinces")
```

This is a 2-input-dimension framework, not 4 — a deliberate reduction from the
originally suggested 4, justified above. If a future review decides the operational
case for `participation_rate` is too weak to retain as a full dimension, the fallback
is to demote it to a third reported-but-unweighted contextual indicator, leaving a
single-dimension (Socioeconomic Vulnerability) NPI — noted here as an explicit
fallback option, not adopted now.
