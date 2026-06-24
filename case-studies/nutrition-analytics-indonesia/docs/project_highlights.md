# Project Highlights

Concrete, real numbers — not adjectives — for portfolio summaries, cover
letters, and interview talking points.

## Scale & scope

- **38 provinces**, **7 real datasets**, **3 government sources** (BPS,
  Kemenkes/TP2S, BIG), **0 synthetic data points** anywhere in the pipeline.
- **6 project phases**, each with a written methodology document produced
  *before* results, and a results document produced *after* — over 20
  `docs/phase*.md` files tracing every decision to evidence.
- **67 automated tests**, 0 real-network calls in the test suite (all test
  logic against fixtures), CI on every push.

## Statistical findings worth quoting

- **Global spatial autocorrelation: Moran's I = 0.622, p = 0.001** (999-permutation
  test) — child-nutrition vulnerability is geographically clustered, not
  randomly distributed.
- **Local clustering: 6 provinces form one significant high-vulnerability
  spatial cluster** (LISA, p < 0.05) — all in the Papua region, independently
  confirmed by 3 separate diagnostics across 2 project phases.
- **Regional disparity: Eastern Indonesia's mean priority score is 2.5× Western
  Indonesia's**, confirmed by both ANOVA (p = 2.8×10⁻⁸) and Kruskal-Wallis
  (p = 8.1×10⁻⁵) — not just eyeballed off a map.
- **Outcome validation: Spearman r = 0.74** between the priority index and real
  child stunting prevalence (0.67 on the more conservative, full-data-coverage
  subset) — reported both ways, not just the more flattering number.
- **Methodology robustness: rank order stable at Spearman r > 0.99** across a
  ±20% weighting perturbation — the ranking doesn't depend on a fragile,
  arbitrary weight choice.

## Real engineering problems solved (not toy exercises)

- **An undocumented pagination bug**: a government API's variable-discovery
  endpoint silently caps results at 10 per page; diagnosed and fixed by reading
  the actual API response structure, not assuming the documentation was complete.
- **A stale-vs-current data conflict**: a government metadata endpoint returned
  Indonesia's pre-2022 34-province scheme while the real statistical data used
  the current 38-province scheme — caught by cross-checking two endpoints
  against each other, not trusting either one blindly.
- **No scriptable source existed for one required dataset** (child stunting
  prevalence) — investigated 6 alternative sources, documented why each failed,
  and built a manual-import path with the same validation rigor as every
  automated one.
- **A geometry source mismatch that would have silently corrupted spatial
  statistics**: the obvious choice (GADM) was missing 4 provinces; the
  documented workaround (duplicate parent polygons) was rejected after testing
  showed it would distort neighbor-based spatial statistics specifically —
  a better, scriptable source was found and substituted instead.
- **A counter-intuitive finding surfaced and reported, not hidden**: tier
  *labels* (Low/Medium/High/Critical) can reclassify up to 76% of provinces
  under small methodology changes even when underlying rank order is stable to
  >0.99 correlation — discovered through deliberate stress-testing, not assumed
  to be stable.

## Self-correction, visible in the project history

The project's own initial methodology (a PCA composite, chosen for sound
statistical reasons) was empirically out-performed by a simpler alternative
during validation — and the simpler one was promoted to primary, with the more
sophisticated one retained as a documented benchmark rather than deleted or
the result buried. See `docs/phase3_final_methodology_decision.md`.
