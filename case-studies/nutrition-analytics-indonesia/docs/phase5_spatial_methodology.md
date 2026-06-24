# Phase 5 — Spatial Methodology

Defines how this phase tests whether the NPI's priority patterns are geographically
clustered, and whether that spatial structure strengthens or weakens confidence in
the ranking framework (`docs/phase4_ranking_results.md`). Methodology only — real
results and their interpretation are in `docs/phase5_spatial_results.md`.

## Data

`data/processed/npi_spatial.geojson` — the Phase 4 NPI ranking
(`data/processed/npi_rankings.csv`) joined to real, distinct geometry for all 38
current provinces (`docs/phase5_geometry_reconciliation.md`), validated for unique
province count, geometry validity, CRS consistency, and join completeness before
any spatial statistic is computed (`src/geospatial/spatial_join.py`).

## Spatial weights (neighbor definition)

Queen contiguity (shared-border neighbors) leaves 7 of 38 provinces — Bali, Kep.
Bangka Belitung, Kep. Riau, Maluku, Maluku Utara, Nusa Tenggara Barat, Nusa
Tenggara Timur — with **zero neighbors**, confirmed during testing: these are
island/archipelagic provinces with no land border to another province, a real
property of Indonesia's geography, not a data defect. Using Queen contiguity as
the primary weights matrix would silently exclude 18% of provinces from every
local statistic.

**K-nearest-neighbors (KNN, k=6) is used as the primary weights matrix instead** —
every province is guaranteed at least one neighbor regardless of physical
adjacency. Queen contiguity, and KNN at k=4 and k=8, are computed and reported as
explicit robustness comparisons (`docs/phase5_spatial_results.md`), not silently
dropped in favor of whichever gives the cleanest result.

## Global spatial autocorrelation: Moran's I

`esda.moran.Moran`, computed on the primary KNN(k=6) weights matrix. **Inference
is permutation-based (999 random reassignments of the NPI score to provinces,
seeded for reproducibility), not the normal approximation** — n=38 is too small to
reliably assume the normal-approximation p-value's assumptions hold, and a
permutation-based p-value (`p_sim`) makes no such assumption. Both are still
reported (`docs/phase5_spatial_results.md`), with `p_sim` treated as authoritative.

## Local spatial autocorrelation: LISA (Local Moran's I)

`esda.moran.Moran_Local`, same KNN(k=6) weights matrix, 999 conditional
permutations. **`alternative="two-sided"` is set explicitly** rather than relying
on this esda version's current default (`"directed"`, which esda's own
deprecation warning says is changing in a future release) — pinning this choice
means a future library upgrade can't silently change which provinces this project
reports as significant. Provinces with `p_sim >= 0.05` are labeled "Not
significant" rather than forced into a High-High/Low-Low/High-Low/Low-High
quadrant the data doesn't actually support at that confidence level.

## Regional analysis

Provinces are grouped into Western / Central / Eastern Indonesia using
**Indonesia's official, legally-defined time zones** (WIB/WITA/WIT) as the
regional boundary (`src/geospatial/regions.py`) — chosen specifically to avoid
inventing a subjective regional boundary; the time zones are a real,
government-defined 3-way partition of the country that maps directly onto
"Western/Central/Eastern" with no judgment call required from this project.

Regional comparison reports mean, median, variance, and tier distribution per
region, plus **two convergent significance tests** — one-way ANOVA (parametric)
and Kruskal-Wallis (rank-based, robust to the NPI distribution's confirmed right
skew, `docs/phase4_ranking_design.md`) — reporting both rather than selecting
whichever gives the more favorable p-value.

## Spatial robustness checks

Three distinct sensitivity questions, each isolating one methodological choice
while holding the others fixed:

1. **Neighbor definition**: Moran's I recomputed at KNN k=4, k=6 (primary), k=8,
   and Queen contiguity (with its 7 islands excluded).
2. **Province reconciliation choice**: Moran's I and LISA recomputed using the
   *original* GADM-crosswalk approach from `docs/province_reconciliation.md`
   (duplicate parent-polygon geometry for the 4 new Papua provinces) instead of
   this phase's real distinct-geometry source, to test whether the geometry
   source itself — not just the neighbor definition — materially changes the
   spatial findings.
3. **Weight matrix row-standardization**: both weights matrices use row-standardized
   ("r") transformation throughout, the standard choice for Moran's I so that
   each province's neighbor influence sums to 1 regardless of how many neighbors
   it has — not varied in this phase, since it's a near-universal convention
   rather than a live methodological choice worth comparing against alternatives.

## What this phase does not do

Per explicit scope: no dashboard, no policy recommendations, no change to the NPI
or ranking methodology itself (Phases 2–4 stand as finalized inputs to this
phase, not revisited here).
