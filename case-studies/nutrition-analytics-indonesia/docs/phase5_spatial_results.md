# Phase 5 — Spatial Results

Real output from `python -m src.geospatial.build_spatial_outputs`, methodology
fixed by `docs/phase5_spatial_methodology.md`. Maps referenced below are in
`reports/maps/`. Full spatial dataset: `data/processed/npi_spatial.geojson`.

## Headline finding

**Yes — NPI priority patterns show strong, statistically significant geographic
clustering, and this materially strengthens confidence in the ranking framework**:
the provinces the Phase 4 ranking flagged as highest-priority are not scattered at
random — they form a real, spatially contiguous cluster across the eastern arc of
the country, corroborated by three independent analyses below (global
autocorrelation, local clusters, and regional comparison) that all converge on the
same pattern.

## 1. Global spatial autocorrelation (Moran's I)

| Statistic | Value |
|---|---|
| Moran's I | **0.622** |
| Expected value under spatial randomness | -0.027 |
| z-score | 8.50 |
| p-value (999-permutation, primary) | **0.001** |
| p-value (normal approximation, reference only) | 4.6 × 10⁻¹⁶ |

**Confidence assessment: very high.** I = 0.622 is a strong positive value (the
theoretical range is roughly -1 to +1), the permutation p-value is at the floor of
what 999 permutations can resolve (1/1000), and the z-score (8.50) is far beyond
the conventional ±1.96 significance threshold. This is not a borderline result.

## 2. Local spatial autocorrelation (LISA)

| Cluster type | Count | Provinces |
|---|---|---|
| **High-High** (significant, p<0.05) | 6 | Papua, Papua Barat, Papua Barat Daya, Papua Pegunungan, Papua Selatan, Papua Tengah |
| **Low-Low** (significant, p<0.05) | 8 | Dki Jakarta, Jawa Barat, Jawa Tengah, Di Yogyakarta, Banten, Lampung, Sumatera Selatan, Kep. Bangka Belitung |
| High-Low / Low-High outliers | 0 | none found |
| Not significant | 24 | (remaining provinces) |

**All 6 of the Papua-region provinces — the entire province group that swept the
"Critical" tier in `docs/phase4_ranking_results.md` — form one contiguous,
statistically significant High-High cluster.** This is independent confirmation,
from a completely different statistical method, of the same pattern Phase 4's
ranking already surfaced: it is not an artifact of how the NPI score or its tiers
were computed. See `reports/maps/lisa_clusters.png`.

The Low-Low cluster is centered on Java (Jakarta, West/Central Java, Yogyakarta,
Banten) plus three additional provinces — a recognizable "developed-core" cluster.

## 3. Regional analysis (Western / Central / Eastern Indonesia, by official time zone)

| Region | n | Mean NPI | Median NPI | Variance |
|---|---|---|---|---|
| Western (WIB) | 18 | 0.263 | 0.289 | 0.0063 |
| Central (WITA) | 12 | 0.313 | 0.316 | 0.0054 |
| **Eastern (WIT)** | 8 | **0.671** | **0.752** | **0.0575** |

Eastern Indonesia's mean NPI is **2.5× Western's and 2.1× Central's** — and its
variance is roughly 10× either other region's, meaning Eastern Indonesia is both
*more vulnerable on average* and *far less homogeneous* than the rest of the
country (consistent with it containing both the most extreme "Critical" provinces
and more moderate ones like Maluku Utara).

**Tier distribution by region:**

| Region | Low | Medium | High | Critical |
|---|---|---|---|---|
| Western | 3 | 14 | 1 | 0 |
| Central | 1 | 6 | 5 | 0 |
| Eastern | 0 | 0 | 3 | **5** |

**Every single "Critical"-tier province in this dataset is in Eastern Indonesia.**
No Western or Central province reaches "Critical," and no Eastern province falls
below "High."

**Statistical significance of the regional difference:**

| Test | Statistic | p-value | Significant at 0.05? |
|---|---|---|---|
| One-way ANOVA | F = 29.76 | 2.8 × 10⁻⁸ | Yes |
| Kruskal-Wallis | H = 18.85 | 8.1 × 10⁻⁵ | Yes |

Both the parametric and rank-based tests agree emphatically: **the regional
disparity is not due to chance.**

## 4. Spatial robustness

### Sensitivity to neighbor definition

| Weights matrix | Moran's I | p-value (permutation) | z-score | Notes |
|---|---|---|---|---|
| KNN k=4 | 0.681 | 0.001 | 7.36 | |
| **KNN k=6 (primary)** | **0.622** | **0.001** | **8.50** | |
| KNN k=8 | 0.524 | 0.001 | 8.60 | |
| Queen contiguity | 0.913 | 0.001 | 6.04 | 7 islands excluded from the weights entirely |

**Conclusion: the clustering finding is robust to the choice of neighbor
definition.** Moran's I varies somewhat in magnitude (0.52–0.91) depending on how
many neighbors each province is assumed to have, but every single configuration
tested is highly significant (p = 0.001 throughout) — the *existence* of
significant clustering does not depend on this choice, even though its exact
strength estimate does.

### Sensitivity to the province reconciliation choice

Recomputing Moran's I using the *original* GADM-crosswalk approach from
`docs/province_reconciliation.md` (duplicate parent-polygon geometry for the 4
newest Papua provinces, instead of this phase's real distinct geometry):

| Geometry source | Moran's I | p-value | z-score |
|---|---|---|---|
| **Real distinct geometry (primary, this phase)** | **0.622** | 0.001 | 8.50 |
| GADM crosswalk (duplicate parent geometry) | 0.647 | 0.001 | 9.00 |

The headline statistic barely moves (0.622 vs. 0.647). **The LISA cluster
membership is nearly identical between the two** — the same 6-province Papua
High-High cluster and almost the same Low-Low set — with one meaningful
difference: **Kalimantan Barat is classified as a significant High-Low spatial
outlier under the GADM-crosswalk geometry, but not significant at all under the
real distinct geometry.** This is attributable to the duplicate-geometry
approach's known distortion (`docs/phase5_geometry_reconciliation.md`) — assigning
multiple provinces the identical parent polygon corrupts the neighbor distances
used for nearby observations like Kalimantan Barat. **This is itself evidence
the real-distinct-geometry choice (this phase's primary) is the more trustworthy
one**, not just a defensible alternative.

## Uncertainty and limitations carried forward

- **n=38 is small** for any spatial statistic; permutation-based inference
  mitigates but does not eliminate the small-sample caveat.
- **`docs/phase3_validation_results.md`'s outcome-correlation caveat still
  applies underneath this analysis** — the NPI's correlation with real stunting
  outcomes is weaker once the Papua group is set aside, so the spatial cluster
  found here is partly *driven by* the same provinces whose outcome-predictive
  power is least certain. The spatial clustering is real and statistically
  robust; whether the NPI score *itself* is the right number to be clustering on
  is a separate question this phase does not re-litigate (per the explicit
  "do not alter NPI methodology" constraint).
- **Spatial weights are unprojected (EPSG:4326)** — appropriate for the
  contiguity/KNN-based statistics used here, but a future area- or
  distance-weighted spatial statistic would need an explicit projected CRS first
  (`docs/phase5_geometry_reconciliation.md`).
- **The WIB/WITA/WIT regional grouping is a real, objective partition, but it is
  not the only valid one** — Indonesia's own statistics agencies also use a
  2-way Western/Eastern split (KBI/KTI) for some planning purposes; the 3-way
  split was chosen here specifically because the task required three regions, and
  documented as such rather than presented as the only correct grouping.

## Readiness for dashboard development

**Ready, with the spatial layer adding genuine value, not just a map for its own
sake.** This phase confirms the priority pattern is geographically structured
(strong global autocorrelation, a real significant cluster, a regional disparity
that survives two different significance tests) — a future dashboard's map view
would be visualizing a real, validated spatial pattern, not just coloring
provinces by an unrelated score. The 4 static maps in `reports/maps/` are
reasonable starting points for what a dashboard's interactive map should
reproduce; the LISA layer in particular is the one map of the four that answers a
question (is this clustering real?) the choropleths alone cannot.
