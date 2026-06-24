# Executive Summary

## Data-Driven Prioritization of Child Nutrition Interventions in Indonesia

### The problem

Indonesia has limited resources for child-nutrition interventions (e.g. the
*Makan Bergizi Gratis* national school-feeding program) and 38 provinces with
very different needs. Policymakers need a transparent, evidence-based way to
decide where to direct resources first — not a black box, and not a number
pulled from intuition.

### What this project does

Builds a **Nutrition Priority Index (NPI)** ranking all 38 provinces, using only
real, publicly verifiable government data (BPS, Kemenkes/TP2S, BIG) — no
synthetic, simulated, or mocked values anywhere in the pipeline — and validates
every methodological choice against real evidence before publishing a result.

### Key findings

1. **The index is empirically grounded, not asserted.** Before publishing any
   ranking, the methodology was validated against real stunting outcomes
   (Spearman r = 0.74), tested for sensitivity to weighting choices (rank order
   stable to >0.99 correlation across a ±20% perturbation), and compared
   head-to-head against an alternative (PCA composite) — the simpler method won
   on 4 of 5 decision criteria and was promoted to primary.
2. **Priority is not randomly distributed — it is geographically clustered.**
   Global Moran's I = 0.622 (p = 0.001); all 6 Papua-region provinces form one
   statistically significant high-vulnerability spatial cluster. Eastern
   Indonesia's mean priority score is 2.5× Western Indonesia's, confirmed by two
   independent statistical tests (p < 0.0001 each).
3. **Honesty about limitations is built into the deliverable, not an
   afterthought.** Every dataset's real gaps (e.g. 4 provinces missing 2 of 6
   indicators because BPS hasn't republished those series since a 2022
   province split) are documented and handled by explicit policy
   (renormalization, never imputation) — and the headline correlation figure is
   reported alongside the more conservative figure that excludes the
   affected provinces.

### What's delivered

A full, reproducible analytics pipeline (ingestion → cleaning → scoring →
ranking → spatial analysis → dashboard), 67 passing automated tests, and an
interactive Streamlit dashboard — plus over 20 phase-by-phase documents tracing
every decision back to real evidence.

### Bottom line

This is a decision-support tool, not a black box: every number in the final
ranking can be traced back through a validated, tested, documented pipeline to
a real government dataset.
