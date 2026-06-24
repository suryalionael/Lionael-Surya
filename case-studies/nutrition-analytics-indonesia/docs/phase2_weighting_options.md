# Phase 2 — Weighting Methodology

Evaluates how to weight (a) the indicators within the Socioeconomic Vulnerability
dimension (`poverty_rate`, `ipm`, `expenditure_per_capita` — known to be collinear,
see `docs/phase2_indicator_audit.md` §7) and (b) the dimensions of the NPI overall
(`docs/phase2_framework_design.md`). No weights are calculated or applied here — this
is a methodology comparison and recommendation only.

## 1. Equal Weighting

Every indicator (or every dimension) gets the same weight (e.g. 1/n).

- **Advantages:** maximally transparent — anyone can recompute it by hand; no
  parameters to justify or defend; immune to accusations of the analyst "thumbing the
  scale."
- **Disadvantages:** blind to collinearity — applied naively across `poverty_rate`,
  `ipm`, and `expenditure_per_capita` (r up to 0.88 between pairs), it would
  effectively triple-count one underlying economic signal relative to
  `participation_rate`'s single, less-correlated signal.
- **Interpretability:** highest of all four options — "every factor counts the same."
- **Policy usefulness:** good as a *default/baseline* a policymaker can sanity-check
  against, poor as the *sole* method given the collinearity problem identified in this
  dataset specifically.
- **Implementation complexity:** trivial (no fitting, no parameters).

## 2. Expert Weighting

Weights set by domain expert judgment (e.g. a nutrition/health policy panel decides
poverty matters more than education access for this purpose).

- **Advantages:** can encode real domain knowledge that pure statistics can't —
  e.g. operational knowledge that school-feeding delivery infrastructure (`
  participation_rate`) matters for *implementation feasibility* even where it's
  statistically weak (audit finding: r = -0.16 with `stunting_rate`).
- **Disadvantages:** not reproducible from the data alone; subject to the particular
  panel's priors; this project currently has no convened expert panel, so "expert
  weights" right now would really just be the analyst's own judgment relabeled —
  a credibility risk worth naming plainly rather than disguising.
- **Interpretability:** high, *if* the rationale for each weight is documented
  (otherwise it looks arbitrary).
- **Policy usefulness:** potentially the highest *if* genuine domain experts are
  involved, since policymakers trust judgment-backed weights they can interrogate
  ("why does poverty count for 40%?") more than a black-box statistical output.
- **Implementation complexity:** low computationally, but operationally expensive —
  requires actually convening and documenting expert input, which is out of scope for
  this solo portfolio project.

## 3. PCA-Based Weighting

Derive weights from the data's own variance structure (first principal component, or
component loadings, of the correlated indicator set).

- **Advantages:** directly solves the collinearity problem this dataset has —
  PCA is specifically designed to collapse correlated indicators into an
  orthogonal composite without double-counting shared variance. Well suited to
  exactly the `poverty_rate`/`ipm`/`expenditure_per_capita` trio.
- **Disadvantages:** weights become a function of *this dataset's* covariance
  structure, not a stable, externally-justifiable policy choice — they would shift if
  next year's data shifts the correlations, which is awkward for a policy tool meant
  to be stable year over year. Harder to explain to a non-technical audience
  ("the program computed a component that explains 73% of the variance" is not an
  intuitive sentence for a policymaker). Only meaningful applied to genuinely
  correlated indicator sets — applying PCA across all 4 candidate indicators
  including the weakly-correlated `participation_rate` would dilute its benefit and
  add unnecessary opacity.
- **Interpretability:** lowest of the four for a non-technical audience, though
  component loadings can be reported as a transparency aid.
- **Policy usefulness:** good as an *internal validity/robustness check* ("does the
  expert-weighted version diverge much from a purely statistical one?"), weaker as
  the *primary, public-facing* methodology for exactly the audience this project
  targets (recruiters, policymakers, non-technical stakeholders).
- **Implementation complexity:** moderate — `sklearn.decomposition.PCA` is simple to
  run, but choosing how many components to retain and how to map loadings back to an
  interpretable weight requires care and documentation.

## 4. Hybrid Approach

Use the right tool for each part of the structure identified in
`docs/phase2_framework_design.md`, rather than one method for everything:

- **Within** the Socioeconomic Vulnerability dimension (3 correlated indicators):
  use PCA (or, as a simpler and more transparent variant, pick one representative
  indicator and document why) specifically *because* the collinearity problem is real
  and PCA is the correct statistical tool for it.
- **Across** the two top-level dimensions (Socioeconomic Vulnerability vs. Education
  Access): use **equal weighting**, because — unlike the indicators within
  Socioeconomic Vulnerability — these two dimensions are *not* strongly collinear
  with each other (`poverty_rate`/`ipm`/`expenditure_per_capita` vs.
  `participation_rate` correlations range from -0.44 to 0.15, i.e. weak-to-moderate,
  not the 0.7-0.9 range seen within the vulnerability trio), so there is no
  statistical case to prefer PCA here, and equal weighting keeps the top-level,
  policy-facing structure maximally transparent.

- **Advantages:** matches the weighting method to the actual statistical structure
  of each part of the framework, rather than forcing one method to do two different
  jobs. Keeps the part that needs to be statistically rigorous (collinear indicators)
  rigorous, and the part that needs to be transparent (top-level policy dimensions)
  transparent.
- **Disadvantages:** more moving parts to document and explain than a single uniform
  method; requires the audience to accept that different parts of the index are
  built differently, which needs clear communication (mitigated by the documentation
  this Phase 2 design work produces).
- **Interpretability:** high at the top level (equal weighting of 2 clearly-named
  dimensions), moderate at the sub-indicator level (PCA loadings need a sentence of
  explanation, but only for one dimension, not the whole index).
- **Policy usefulness:** best fit for this project's stated audience — a policymaker
  can understand "Vulnerability and Education Access count equally" without needing
  to understand PCA, while a data analyst reviewing the methodology can verify the
  PCA step is justified by the actual measured collinearity (§ above), not asserted.
- **Implementation complexity:** moderate — combines a small PCA step with simple
  arithmetic; more code than pure equal weighting, less organizational overhead than
  genuine expert weighting.

## Comparison summary

| Approach | Interpretability | Policy usefulness | Implementation complexity | Handles this dataset's collinearity? |
|---|---|---|---|---|
| Equal weighting | Highest | Good baseline | Trivial | No |
| Expert weighting | High (if documented) | Highest, if real experts involved | Low compute / high process cost | Only if experts account for it |
| PCA-based | Lowest for non-technical audiences | Best as a robustness check | Moderate | Yes, directly |
| **Hybrid (recommended)** | High at policy level, moderate at sub-indicator level | High — matches the audience | Moderate | Yes, where it matters |

## Recommendation

**Hybrid approach**, structured exactly as described above: PCA (or a clearly
documented single-representative-indicator substitute) to collapse the Socioeconomic
Vulnerability trio, equal weighting across the two top-level dimensions. This is the
only option that directly addresses the specific, measured collinearity problem in
this dataset (§7 of the indicator audit) without sacrificing the top-level
transparency this project's audience requires. Pure equal weighting would
misrepresent the data's actual structure; pure PCA would be needlessly opaque at the
top level where no collinearity problem exists; expert weighting would require a
panel this solo project doesn't have. Phase 3 should implement the PCA step with its
output (component loadings, % variance explained) documented in
`docs/phase2_technical_design.md`-style detail at build time, and should compute and
report the equal-weighting result alongside a pure-PCA-only result as a sensitivity
check (see `docs/phase2_sensitivity_design.md`), not as the primary output.
