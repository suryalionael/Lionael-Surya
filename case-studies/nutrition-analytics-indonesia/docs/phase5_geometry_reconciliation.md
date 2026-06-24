# Phase 5 — Province Geometry Reconciliation

Resolves the GADM 34-vs-38 province mismatch documented in
`docs/province_reconciliation.md` §3, specifically for the spatial analysis this
phase requires. That document's original plan (a crosswalk mapping each of the 4
new Papua provinces to its old GADM parent polygon) is **not used here** — a better
real source was found during this phase, and using it instead avoids a problem the
crosswalk approach would have caused for spatial statistics specifically.

## Why the original GADM crosswalk approach was rejected for spatial analysis

The crosswalk (`src/reference/province_gadm_crosswalk.csv`) maps Papua Selatan,
Papua Tengah, and Papua Pegunungan all to the same GADM "Papua" polygon, and Papua
Barat Daya to the same GADM "Papua Barat" polygon. That is a reasonable choice for
*reporting* a value on a map (better to show a coarse approximation than nothing),
but it is **actively wrong for spatial statistics**: Moran's I and LISA depend on a
well-defined neighbor structure, and assigning 4 provinces onto only 2 distinct
polygons means those "neighbors" would be geometrically identical or overlapping —
violating the basic premise that each observation occupies a distinct location.
Using it here would have silently distorted both the global and local
autocorrelation results for exactly the cluster of provinces (`docs/phase4_ranking_
results.md` already flagged the Papua group as the entire "Critical" tier) most
relevant to this project's findings.

## What was found instead: a real, scriptable source with distinct 38-province geometry

`https://github.com/dmxsan/indonesia-admin-boundaries` republishes Indonesia's
administrative boundaries "derived from the latest shapefiles provided by Badan
Informasi Geospasial (BIG)" — the same authoritative national agency
`docs/known_limitations.md` §3 already identified as the most authoritative source,
previously rejected as a default only because *direct* access requires a free human
registration that can't be scripted. This GitHub mirror provides the same
underlying BIG-sourced data as 38 separate, genuinely distinct per-province GeoJSON
files — including real, distinct geometry for all 4 of the newest Papua provinces,
confirmed present and correctly named during Phase 5 testing.

**Provenance chain, stated explicitly for auditability:** BIG (original surveying
authority) → dmxsan/indonesia-admin-boundaries (public GitHub mirror, scriptable,
unauthenticated) → `src/ingestion/fetch_geo_boundaries.py --source big_mirror`
(this project's ingestion, confirmed reachable and downloadable without auth) →
`src/geospatial/boundaries.py` (standardization + simplification, below).

## Implementation

- `src/ingestion/fetch_geo_boundaries.py --source big_mirror`: downloads all 38
  per-province files (hardcoded filename list, not crawled at fetch time, so an
  upstream listing change can't silently alter what this project considers "the 38
  provinces" — see the module docstring), combines into one raw GeoJSON, and
  records a manifest entry exactly like every other dataset in this project.
- `src/geospatial/boundaries.py::load_boundaries()`: loads the raw file (~497MB,
  some single-province files exceed 50MB due to multi-island detail — set
  `OGR_GEOJSON_MAX_OBJ_SIZE=0` to bypass GDAL's default complexity guard),
  **simplifies geometry to 0.001° (~111m at the equator), topology-preserving**,
  and standardizes province names through the existing reference layer
  (`src/reference/lookup.py`) — every one of the 38 names matched the canonical
  list with zero unrecognized names, confirmed during testing.

## No provinces silently dropped — confirmed, not assumed

| Check | Result |
|---|---|
| Provinces in raw fetch | 38 |
| Provinces after standardization | 38 (zero unrecognized names) |
| Invalid geometries before simplification | 0 |
| Invalid geometries after simplification | 0 |
| Total geometry size (WKB bytes), before → after simplification | 258,020,389 → 5,637,901 (~46x reduction) |

## Assumptions documented explicitly

1. **The raw file is never modified** — simplification happens only on the
   in-memory copy `load_boundaries()` returns, consistent with this project's
   standing rule that raw fetched files are immutable provenance records
   (`docs/known_limitations.md`).
2. **0.001° simplification tolerance** was chosen by testing 0.001/0.005/0.01 and
   picking the loosest-still-fully-valid option that preserved the most shape
   detail (0.001 produced zero invalid geometries and the largest size reduction
   relative to shape fidelity of the three tested) — not an arbitrary default.
   Documented here so a future re-run with a different tolerance is a visible,
   deliberate choice, not silent drift.
3. **CRS is taken from the source file as-is (EPSG:4326 / CRS84)** and never
   reprojected for the Moran's I / LISA computations in this phase — `libpysal`
   contiguity weights operate on the polygons' topology, not a chosen projection's
   distances, so an unprojected CRS does not bias the contiguity-based results in
   `docs/phase5_spatial_methodology.md`. A future area- or distance-based spatial
   statistic (not used in this phase) would need an explicit projected CRS instead.
4. **The Phase 0 GADM crosswalk is retained, not deleted** — it remains documented
   in `docs/province_reconciliation.md` as the right fallback for any future context
   where only GADM-sourced geometry is available and a coarser approximation is
   acceptable. This document supersedes it specifically for Phase 5's spatial
   statistics, where geometric distinctness is required, not optional.
