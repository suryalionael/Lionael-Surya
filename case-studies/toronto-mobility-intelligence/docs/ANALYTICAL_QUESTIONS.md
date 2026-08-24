# Analytical Questions

Toronto Mobility Intelligence — Phase 1 question bank, scoped against the schema in
[`DATA_MODEL.md`](DATA_MODEL.md). Every metric below states its formula, unit, grain, time
period, denominator, and limitations explicitly — no undefined terms like "dangerous
intersection" are used anywhere in this project. Where a metric formula appears in more than
one question, it is defined once (marked **[metric defined here]**) and referenced by name
afterward.

Questions are prioritized: sections A–C run on `fact_collisions` alone and are valid across the
full 2006–2026 span with no exposure-denominator caveats (Tier 1, per `DATA_MODEL.md` §1.5).
Sections D–E depend on the spatial match and/or the traffic-volume snapshot and carry the
caveats documented there (Tier 2). Section F is geography-only. Section G is meta — questions
about the data itself.

---

## Phase 3 implementation status

Phase 3 built a curated SQL layer (`sql/analytics/01_temporal/` … `07_quality/`, 14 files, 5 of
them persisted as `analytics.v_*` views) answering the highest-value questions from this bank,
prioritizing quality over exhaustively implementing every question listed here. Findings drawn
from the real output are in [`ANALYTICAL_FINDINGS.md`](ANALYTICAL_FINDINGS.md).

**Implemented (question → SQL file):** A1/A2 → `01_temporal/010`, B1 → `01_temporal/020`, B2 →
`01_temporal/030`, A2-extended → `02_severity/010`, C3 → `02_severity/020`, A3 →
`03_road_users/010` and `020`, C1/F1 → `04_neighbourhoods/010`, F2 → `04_neighbourhoods/020`
(implemented as a two 5-year-window comparison rather than a per-year LAG across all 158
neighbourhoods × 21 years — the per-year version would produce ~3,300 mostly-noisy single-year
deltas; see that file's header for the full reasoning), D1 → `05_intersections/010` and `020`
(the `020` file also covers a version of "persistent activity," not originally broken out as
its own lettered question), E1 → `06_exposure/010`, D3/G4 → `07_quality/010`, G1/G3 →
`07_quality/020`.

**Deliberately not implemented:** D2 (infrastructure-vs-collision association) was dropped, not
deferred by oversight — its own limitation note already flags a strong reverse-causation risk
(safety features are often installed *because* a location already had a collision history,
which would bias any naive comparison toward making safety features look associated with
*higher* risk). Building it would have produced a number that looks like a finding but isn't
one. F3 (neighbourhood KSI vs demographic/socioeconomic profile) remains not answerable, as
already noted in its own entry — Neighbourhood Profiles was never one of the four approved
datasets. E2 (bike-volume quartiles vs cyclist involvement) and E3 (zero-collision intersection
screening) were not built in Phase 3 to keep this phase to a curated 10–15 queries rather than
exhaustively covering the bank; both remain valid candidates for a future pass.

---

## A. Collision Patterns

### A1. What is the citywide trend in KSI collisions and fatalities per year?

- **Business/public-sector question:** Is Vision Zero's core outcome measure — killed or
  seriously injured people — trending up, down, or flat since the plan launched in 2016?
- **Required tables:** `fact_collisions`, `dim_date`
- **Required fields:** `collision_id`, `accdate` → `date_key`, `acclass`, `fatal_no`
- **Expected SQL technique:** `COUNT(DISTINCT collision_id)` grouped by `year`; window function
  `LAG()`/`AVG() OVER (ORDER BY year ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)` for a 3-year
  rolling trend to smooth year-to-year noise before eyeballing direction.
- **Metric — annual KSI collision count [metric defined here]:**
  - Formula: `COUNT(DISTINCT collision_id) WHERE acclass IN ('Fatal Injury','Non-Fatal Injury')`
    (exact source strings, confirmed during Phase 2 build; `acclass` is a true collision-level
    attribute — every person-row of a given `collision_id` carries the same value, confirmed
    with zero exceptions across all 20,691 rows)
  - Unit: collisions per calendar year
  - Grain: year
  - Time period: 2006–2026 (current year likely under-reported, see §1.5 of `DATA_MODEL.md`
    and Question G3)
  - Denominator: none — raw count
  - Limitations: KSI is severity-filtered by definition; this cannot say whether *total*
    collisions (including minor ones) rose or fell, only the killed-or-seriously-injured
    subset. City population/vehicle-registration growth is not controlled for. Note: a small
    residual share of collision_ids in this extract carry `acclass = 'Property Damage Only'`
    (not Fatal/Non-Fatal) — this formula's `IN` filter already excludes them, which is the
    intended behavior.

### A2. How does collision severity break down, and how has the mix shifted over time?

- **Business/public-sector question:** Among KSI collisions, is the fatal share growing
  relative to serious-injury?
- **Required tables:** `fact_collisions`
- **Required fields:** `collision_id`, `acclass`, `accdate`
- **Expected SQL technique:** conditional aggregation (`CASE WHEN acclass = 'Fatal Injury' THEN 1
  ELSE 0 END`), percent-of-total via `COUNT(*) FILTER (WHERE ...) / COUNT(*)::numeric`.
- **Metric — fatal share of KSI collisions:**
  - Formula: `COUNT(DISTINCT collision_id) FILTER (WHERE acclass = 'Fatal Injury') / COUNT(DISTINCT collision_id)::numeric`
  - Unit: proportion (0–1), typically reported as a percentage
  - Grain: year (or any chosen time bucket)
  - Time period: any sub-range of 2006–2026
  - Denominator: all KSI collisions in the same period
  - Limitations: small annual counts (fatal collisions are rare relative to serious-injury)
    make year-over-year percentage swings noisy; a multi-year rolling window is recommended
    over single-year comparisons.

### A3. Which road-user groups are most represented among KSI collisions, and how has that mix changed?

- **Business/public-sector question:** Are pedestrians, cyclists, or motorcyclists an
  increasing share of the people killed or seriously injured?
- **Required tables:** `fact_collisions`
- **Required fields:** `collision_id`, `per_no`, `pedestrian`, `cyclist`, `motorcyclist`,
  `road_user`, `injury`, `accdate`
- **Expected SQL technique:** conditional aggregation on the boolean flag columns; `GROUP BY
  road_user`; percent-of-total.
- **Metric — road-user involvement rate:**
  - Formula: `COUNT(DISTINCT collision_id) FILTER (WHERE pedestrian) / COUNT(DISTINCT collision_id)::numeric` (repeat per flag: cyclist, motorcyclist)
  - Unit: proportion of KSI collisions involving that road-user type
  - Grain: year
  - Time period: 2006–2026
  - Denominator: all KSI collisions in the period (a single collision can involve more than
    one road-user type, so the flags are not mutually exclusive and percentages will not sum
    to 100%)
  - Limitations: this measures *involvement*, not fault or cause.

---

## B. Temporal Patterns

### B1. What hour of day and day of week see the most KSI collisions?

- **Business/public-sector question:** When should enforcement/safety-campaign resources be
  timed?
- **Required tables:** `fact_collisions`, `dim_date`
- **Required fields:** `accdate` (hour extraction), `date_key` → `day_of_week`, `day_name`
- **Expected SQL technique:** `EXTRACT(HOUR FROM accdate)`; `GROUP BY hour, day_of_week`;
  window function `RANK() OVER (ORDER BY collision_count DESC)` to surface the top hour/day
  combinations.
- **Metric:** annual KSI collision count (defined in A1), bucketed by hour-of-day and
  day-of-week instead of year.
  - Limitations: hour is taken from the reported collision timestamp, which for a small number
    of records may be an estimate rather than a precise observed time (source data quality,
    not something this project can verify).

### B2. Is there a seasonal pattern (winter vs. summer) in collision frequency or severity mix?

- **Business/public-sector question:** Does winter road condition (ice/snow) correlate with
  more or more-severe collisions?
- **Required tables:** `fact_collisions`, `dim_date`
- **Required fields:** `date_key` → `season`, `acclass`, `rdsfcond`, `light`
- **Expected SQL technique:** `GROUP BY season`; conditional aggregation combining `season`
  with `rdsfcond` (road surface condition) to check whether the seasonal pattern is explained
  by road condition or persists independent of it.
- **Metric:** annual KSI collision count (A1) and fatal share (A2), bucketed by season.
  - Limitations: "association" language only — road-surface condition is self-reported by the
    investigating officer at the scene, not measured independently, and this cannot establish
    that winter conditions *caused* any given collision.

### B3. What is the month-over-month trend within the most recent 24 months, and does it show early signs of a shift?

- **Business/public-sector question:** Is the most recent data showing an emerging trend worth
  flagging before annual figures are finalized?
- **Required tables:** `fact_collisions`, `dim_date`
- **Required fields:** `date_key` → `year`, `month`
- **Expected SQL technique:** window function `AVG() OVER (ORDER BY year, month ROWS BETWEEN 5
  PRECEDING AND CURRENT ROW)` (6-month rolling average); `LAG()` for month-over-month percent
  change.
- **Metric:** annual KSI collision count (A1), computed monthly and rolled up with a 6-month
  moving average.
  - Limitations: the most recent 1–3 months are under-reported due to the verification lag
    described in `DATASET_RESEARCH.md` (fatalities ~1–2 weeks, serious injuries 2–3 months) —
    this question must explicitly exclude or flag the trailing 3 months to avoid reading a
    reporting-lag artifact as a real trend. See Question G3.

---

## C. Geographic Patterns

### C1. Which neighbourhoods have the highest KSI collision counts, and how does that compare on a per-capita or per-area basis?

- **Business/public-sector question:** Where in the city is the KSI burden concentrated?
- **Required tables:** `fact_collisions`, `dim_neighbourhood`
- **Required fields:** `neighbourhood_key`, `collision_id`, `dim_neighbourhood.area_name`,
  `dim_neighbourhood.geom` (for area in km² via `ST_Area(geography(geom))`)
- **Expected SQL technique:** `GROUP BY neighbourhood_key`; `RANK() OVER (ORDER BY
  collision_count DESC)`; percent-of-total (`collision_count / SUM(collision_count) OVER ()`).
- **Metric — neighbourhood KSI density:**
  - Formula: `COUNT(DISTINCT collision_id) / ST_Area(geography(geom)) * 1,000,000` (collisions
    per km²)
  - Unit: KSI collisions per km²
  - Grain: neighbourhood
  - Time period: any chosen range, e.g. trailing 5 years
  - Denominator: neighbourhood land area
  - Limitations: this is not per-capita or per-traveler — a large, sparsely-trafficked
    neighbourhood and a small, dense one are not directly comparable on this metric alone
    without population or traffic-volume context (Neighbourhood Profiles data, not currently
    in scope, would be needed for a true per-capita version).

### C2. Where are KSI collisions clustered geographically within the road network (points on a map), independent of neighbourhood boundaries?

- **Business/public-sector question:** Do collisions cluster at specific spots that a
  neighbourhood-level rollup would smooth over?
- **Required tables:** `fact_collisions`
- **Required fields:** `geom`, `collision_id`, `latitude`, `longitude`
- **Expected SQL technique:** raw point export for map visualization (Power BI / GIS layer);
  optionally `ST_ClusterDBSCAN(geom, eps, minpoints) OVER ()` in PostGIS for density-based
  clustering.
- **Metric:** none — this is a visualization/exploration question, not a scored metric.
  - Limitations: 1 of 7,587 collisions lacks coordinates and is excluded from any spatial view.

### C3. How does collision severity vary by road classification (arterial vs. local vs. collector)?

- **Business/public-sector question:** Are higher-speed/higher-volume road classes associated
  with more severe outcomes?
- **Required tables:** `fact_collisions`
- **Required fields:** `road_class`, `acclass`, `collision_id`
- **Expected SQL technique:** conditional aggregation; percent-of-total within each
  `road_class` group.
- **Metric:** fatal share (A2), grouped by `road_class` instead of year.
  - Limitations: `road_class` is a City-assigned category on the collision record, not
    independently verified against the Centreline dataset (not in scope for Phase 1) — a small
    number of misclassifications are possible.

---

## D. Intersection Risk

> All questions in this section depend on `bridge_collision_intersection` and therefore only
> cover the ~44.7% of KSI collisions expected to match a signalized intersection within the
> validated 20 m radius (`DATA_MODEL.md` §2.4). They describe signalized-intersection risk
> specifically, not citywide intersection risk.

### D1. Which signalized intersections have the highest KSI collision counts?

- **Business/public-sector question:** Which specific signals warrant an engineering review?
- **Required tables:** `fact_collisions`, `bridge_collision_intersection`, `dim_intersection`
- **Required fields:** `bridge_collision_intersection.collision_id`, `.intersection_key`,
  `.match_status`, `dim_intersection.px`, `.main_street`, `.side1_street`
- **Expected SQL technique:** `INNER JOIN ... WHERE match_status = 'matched'`; `GROUP BY
  intersection_key`; `RANK() OVER (ORDER BY collision_count DESC)`.
- **Metric — matched KSI collision count:**
  - Formula: `COUNT(DISTINCT bridge.collision_id) WHERE match_status = 'matched'`, joined to
    `dim_intersection`
  - Unit: matched KSI collisions
  - Grain: intersection (`px`)
  - Time period: any chosen range
  - Denominator: none — raw count
  - Limitations: **this ranks intersections by raw count, not by rate** — a busy intersection
    will naturally rank higher even if it is proportionally safer per vehicle passing through
    it. Do not describe a high-ranking intersection here as "the most dangerous" without also
    reporting the Tier-2 rate metric (E1) alongside it, and even then with its stated
    limitations. This question intentionally does not use the word "dangerous."

### D2. Does infrastructure (pedestrian countdown timers, audible signals, transit/fire/rail preemption) show any association with collision counts at matched intersections?

- **Business/public-sector question:** Do intersections with certain safety features show a
  different collision pattern than those without?
- **Required tables:** `bridge_collision_intersection`, `dim_intersection`
- **Required fields:** `dim_intersection.audible_ped_signal`, `.led_blankout_sign`,
  matched collision counts (D1)
- **Expected SQL technique:** conditional aggregation grouped by the boolean infrastructure
  flags.
- **Metric:** matched KSI collision count (D1), grouped by infrastructure flag.
  - Limitations: **association only, explicitly not causal.** Infrastructure is not randomly
    assigned — safety features are often installed *because* a location already had a
    collision history, which would bias any naive comparison toward making safety features
    look associated with *higher* risk (reverse causation). This question can only be answered
    descriptively, with this caveat stated alongside any result, never as "feature X reduces
    collisions."

### D3. How does the mix of matched vs. unmatched collisions vary by `traffictl` category, and does it validate the spatial match itself?

- **Business/public-sector question:** (Internal data-quality question, not a public-facing
  finding) — does the spatial join actually behave the way §2.3 of `DATA_MODEL.md` predicts?
- **Required tables:** `fact_collisions`, `bridge_collision_intersection`
- **Required fields:** `fact_collisions.traffictl`, `bridge_collision_intersection.match_status`
- **Expected SQL technique:** `GROUP BY traffictl, match_status`; percent-of-total within each
  `traffictl` group — expect `traffictl = 'Traffic Signal'` to show a `matched` rate close to
  100% and `traffictl = 'No Control'`/`'Stop Sign'` to show mostly `unmatched_outside_radius`.
- **Metric:** match rate — `COUNT(*) FILTER (WHERE match_status='matched') /
  COUNT(*)::numeric`, grouped by `traffictl`.
  - Limitations: this is a validation check on the join quality, not a mobility finding — kept
    in the analytical question bank because it should run as part of any Phase 2 build to
    confirm the spatial match continues to behave as expected as new KSI data lands.

---

## E. Traffic Exposure

> Every question here inherits the Tier-2 caveats from `DATA_MODEL.md` §1.5/§4.2: the
> denominator is a **single most-recent volume snapshot**, not a time-matched annual figure.
> These are cross-sectional (point-in-time) comparisons between intersections, never a
> collision-rate *trend* over time.

### E1. Among matched intersections, which have a disproportionately high collision count relative to their most recently observed traffic volume?

- **Business/public-sector question:** Controlling for how busy an intersection currently is,
  which locations still stand out?
- **Required tables:** `bridge_collision_intersection`, `dim_intersection`,
  `fact_traffic_volume`
- **Required fields:** matched collision count (D1), `fact_traffic_volume.total_vehicle`,
  `.total_bike`, `.total_pedestrian`, `.count_date`
- **Expected SQL technique:** CTE to get each intersection's `MAX(count_date)` row from
  `fact_traffic_volume`; join to matched-collision counts; window function `PERCENT_RANK() OVER
  (ORDER BY collisions_per_10k_movements)` to express results as a percentile rather than a
  raw, hard-to-interpret ratio.
- **Metric — collisions per 10,000 observed movements [metric defined here]:**
  - Formula: `matched_collision_count / (total_vehicle + total_bike + total_pedestrian) *
    10,000`, using each intersection's single most recent `fact_traffic_volume` row
  - Unit: matched KSI collisions per 10,000 vehicle/bike/pedestrian movements observed on the
    count day
  - Grain: intersection (`px`)
  - Time period: collisions from a chosen multi-year window (e.g. trailing 5 years) ÷ a
    **single-day** volume snapshot (whatever day the most recent TMC count happened to be
    taken)
  - Denominator: total observed movements (vehicle + bike + pedestrian) on that one count day
  - Limitations (must be stated with every use of this metric): (1) numerator spans years,
    denominator is one day — this is a proxy for typical exposure, not a matched-period rate;
    (2) `count_recency_years` varies by intersection (§1.5) — a location last counted in 2010
    and one last counted in 2026 are not equally trustworthy denominators, and results should
    be filtered or faceted by recency rather than presented as one uniform ranking; (3) this
    metric only covers the ~44.7% of collisions that matched an intersection (D1) — it says
    nothing about midblock or unsignalized-intersection risk.

### E2. Do intersections with high bicycle volume show a different collision/severity pattern than low-bicycle-volume intersections?

- **Business/public-sector question:** Does cycling infrastructure investment correlate with
  different collision patterns?
- **Required tables:** `fact_collisions`, `bridge_collision_intersection`, `dim_intersection`,
  `fact_traffic_volume`
- **Required fields:** `fact_collisions.cyclist`, matched collision counts, `total_bike`
- **Expected SQL technique:** bucket intersections into bike-volume quartiles with `NTILE(4)
  OVER (ORDER BY total_bike)`; conditional aggregation of cyclist-involved collisions per
  quartile.
- **Metric:** road-user involvement rate (A3, `cyclist` flag), computed within bike-volume
  quartiles instead of citywide.
  - Limitations: same single-day-snapshot caveat as E1, plus: higher bike volume at an
    intersection could reflect *either* more cycling infrastructure/safety measures *or* simply
    a busier cycling corridor with no safety intervention — this dataset alone cannot
    distinguish the two without the Cycling Network dataset (deferred to Phase 2 per
    `DECISION_LOG.md`).

### E3. What share of TMC-counted intersections have never recorded a matched KSI collision, and is that meaningful or just a function of stale/no counts?

- **Business/public-sector question:** (Data-quality-adjacent) — before reporting "safe"
  intersections, confirm this isn't just an artifact of coverage gaps.
- **Required tables:** `dim_intersection`, `bridge_collision_intersection`,
  `fact_traffic_volume`
- **Required fields:** `LEFT JOIN` from `dim_intersection` to matched collisions;
  `count_recency_years`
- **Expected SQL technique:** `LEFT JOIN` + `WHERE bridge.collision_id IS NULL`; cross-tabulate
  against `count_recency_years` bucket.
  - Limitations: an intersection with zero matched collisions might genuinely be safe, or might
    simply have had all its nearby collisions fall just outside the 20 m radius, or might be a
    low-volume location where a KSI event is statistically rare regardless of underlying risk.
    This question exists specifically to prevent the project from mis-reporting "zero
    collisions" as "safe" without checking these alternatives first.

---

## F. Neighbourhood Analysis

### F1. How does the road-user mix (pedestrian/cyclist/motorcyclist/driver) of KSI collisions differ by neighbourhood?

- **Business/public-sector question:** Do some neighbourhoods have a pedestrian-safety problem
  specifically, versus a general collision problem?
- **Required tables:** `fact_collisions`, `dim_neighbourhood`
- **Required fields:** `neighbourhood_key`, `pedestrian`, `cyclist`, `motorcyclist`,
  `collision_id`
- **Expected SQL technique:** conditional aggregation grouped by `neighbourhood_key`;
  percent-of-total within each neighbourhood.
- **Metric:** road-user involvement rate (A3), grouped by neighbourhood instead of citywide.
  - Limitations: same as A3 (involvement, not fault); small neighbourhoods with few total KSI
    collisions will show noisy percentages — a minimum collision-count threshold should be
    applied before ranking neighbourhoods on this metric.

### F2. Which neighbourhoods have shown the largest year-over-year change in KSI collisions (improving or worsening)?

- **Business/public-sector question:** Where should Vision Zero investment be reprioritized —
  where is it working, and where is it not?
- **Required tables:** `fact_collisions`, `dim_neighbourhood`, `dim_date`
- **Required fields:** `neighbourhood_key`, `date_key` → `year`, `collision_id`
- **Expected SQL technique:** window function `LAG() OVER (PARTITION BY neighbourhood_key ORDER
  BY year)` for year-over-year comparison; a multi-year rolling average (as in B3) to smooth
  small-neighbourhood noise before computing a trend.
- **Metric — year-over-year change:**
  - Formula: `(this_year_count - last_year_count) / NULLIF(last_year_count, 0)::numeric`
  - Unit: proportion change (percentage)
  - Grain: neighbourhood × year
  - Time period: any two consecutive years, or a multi-year rolling comparison
  - Denominator: prior-year collision count for the same neighbourhood
  - Limitations: percentage change on small counts is highly volatile (a neighbourhood with 2
    KSI collisions one year and 4 the next shows "+100%" from a small, possibly non-meaningful
    swing) — this should always be reported alongside the raw counts, never as a percentage
    alone, and a minimum base-count threshold (e.g. ≥10 collisions in the base year) should
    gate which neighbourhoods are included in a "most improved/worsened" ranking.

### F3. How does neighbourhood-level KSI density (C1) relate to the neighbourhoods' available Neighbourhood Profile characteristics?

- **Status: not answerable in Phase 1.** Neighbourhood Profiles (demographic/socioeconomic
  data) was identified in Phase 0 research but is **not** one of the four datasets approved for
  this project. This question is recorded here as a documented Phase 2 candidate, not answered
  now, to be explicit that it was considered rather than silently omitted.

---

## G. Data Quality

### G1. What percentage of KSI collision records have missing or null values in key fields, and is that rate stable over time?

- **Business/public-sector question:** (Internal) — how much of the analysis rests on complete
  data vs. inference?
- **Required tables:** `fact_collisions`
- **Required fields:** all nullable columns listed in `DATA_MODEL.md` §3.6, especially
  `latitude`/`longitude`, `neighbourhood_key`, `road_class`, `injury`
- **Expected SQL technique:** `COUNT(*) FILTER (WHERE column IS NULL) /
  COUNT(*)::numeric`, per column, per year — a standard data-quality check, to live in
  `sql/quality/`.
  - Limitations: none — this is itself the limitations-measurement question.

### G2. Are there duplicate collision records (same `collision_id` + `veh_no` + `per_no` appearing more than once)?

- **Business/public-sector question:** (Internal) — validate the assumed natural key before it
  is used as a join/grain guarantee anywhere else in the model.
- **Required tables:** `fact_collisions` (staging layer, pre-dedup)
- **Required fields:** `collision_id`, `veh_no`, `per_no`
- **Expected SQL technique:** `GROUP BY collision_id, veh_no, per_no HAVING COUNT(*) > 1`; or
  `ROW_NUMBER() OVER (PARTITION BY collision_id, veh_no, per_no ORDER BY _id)` to identify and
  drop true duplicates during the staging→clean transform.

### G3. What is the effective reporting lag in the most recent months of KSI data, and where should a "data as of" cutoff be drawn for trend reporting?

- **Business/public-sector question:** (Internal, feeds directly into B3 and A1) — prevent the
  project from reporting a false recent decline that is actually just unprocessed cases.
- **Required tables:** `fact_collisions`
- **Required fields:** `accdate`, and (if available in the source, to be confirmed at
  ingestion) any "date reported"/"date verified" field distinct from `accdate`
- **Expected SQL technique:** compare monthly collision counts as captured in successive raw
  data pulls over time (requires re-pulling the source at intervals — a Phase 2 operational
  concern) — for Phase 1, the simpler proxy is to plot monthly counts for the trailing 6 months
  and visually/statistically confirm the expected under-count pattern before deciding a cutoff
  (e.g., exclude the trailing 3 months from any "current trend" claim, per `DATASET_RESEARCH.md`'s
  documented 1–2 week / 2–3 month verification lag).

### G4. Do any collision or intersection coordinates fall outside Toronto's expected geographic bounding box?

- **Business/public-sector question:** (Internal) — catch obvious geocoding errors before they
  distort spatial analysis or the nearest-neighbor match.
- **Required tables:** `fact_collisions`, `dim_intersection`
- **Required fields:** `latitude`, `longitude` / `geom`
- **Expected SQL technique:** `WHERE NOT ST_Within(geom, toronto_bounding_box)` or a simple
  lat/long range check (Toronto ≈ 43.58–43.85 N, −79.64 – −79.12 W); flag rather than silently
  drop, since a small number of legitimate edge-of-city collisions may sit near the boundary.
