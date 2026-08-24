# Data Model

Toronto Mobility Intelligence — Phase 1 analytical schema design.

This document is the result of an empirical investigation (not assumption) into the temporal
grain of the traffic-volume dataset and the real coordinate distributions of collisions vs.
signals. All figures below were computed by directly querying the City of Toronto CKAN
datastore API (`datastore_search`) for full datasets — 20,691 KSI person-rows, 30,831 TMC
count-events, 2,550 traffic signals — not sampled or estimated.

---

## Part 1 — Temporal Compatibility Investigation (required before any rate metric)

### 1.1 What is the actual grain of the Traffic Volumes (TMC) dataset?

The dataset ships two relevant resources:

| Resource | Rows | What it is |
|---|---|---|
| `tmc_most_recent_summary_data` | 6,378 | **One row per location's single most recent count** |
| `tmc_summary_data` (full history) | 30,831 | **One row per count *event*** — every count ever taken |

Querying the full history resource and grouping by `(px, count_date)` confirms the grain
directly: for the 24,067 rows that carry a non-null `px` (signal/intersection-keyed location),
only 9 pairs of 12,000+ distinct `(px, count_date)` combinations repeat — i.e., **grain is
`intersection × count_date`, essentially unique** (the 9 duplicates are same-day resurveys, a
minor known data-quality wrinkle, not a modeling problem). Directional volumes (N/E/S/W
approach) are already pivoted into columns on that one row — there is no separate
`intersection × direction × count_date` grain to worry about.

The remaining 6,764 rows (30,831 − 24,067) have `px = NULL` — these are **midblock/segment
counts** identified only by `centreline_id`, not by an intersection `px`. They are a legitimate
part of the TMC dataset but cannot join to `dim_intersection` (which is keyed by `px`) and are
**excluded from Phase 1's `fact_traffic_volume`** — see §3.4.

**Grain, stated precisely: `fact_traffic_volume` grain = one row per (`px`, `count_date`)
count event, for locations where `px` is populated.**

### 1.2 Does the dataset contain historical observations, or only the most recent count?

Both — the full-history resource (`tmc_summary_data`) contains every count ever taken, back to
1984:

| Year band | Count events |
|---|---|
| 1984–1989 | 2,720 |
| 1990–1999 | 4,792 |
| 2000–2009 | 7,846 |
| 2010–2019 | 6,927 |
| 2020–2026 | 8,528 |
| **Total** | **30,831** |

Coverage is real and spans the full period, but it is **not evenly distributed** — there is a
visible spike in 2022 (2,185 counts, likely a post-pandemic recount push) and a generally
thinner middle period (2008–2015 average ~650/year vs. 2020s average ~1,200/year).

### 1.3 What is the actual re-count cadence per intersection?

2,661 distinct intersections have at least one count, averaging **11.6 counts per intersection
over 42 years** — but the distribution is far from uniform:

- 134 intersections have exactly **1** count in the entire 1984–2026 history (never recounted).
- The most-counted intersection has **52** counts.
- 94% of intersections (2,511 of 2,661) have counts spanning **more than one calendar year**,
  so directional before/after comparisons are possible for most locations — but the counts
  arrive irregularly (e.g., 1986 → 1995 → 2003 → 2016 → 2022), not on any fixed annual or
  multi-year schedule. There is no intersection with a complete year-by-year series across
  2006–2026.

### 1.4 Can we compute a true historical collision rate (collisions in year Y ÷ volume in year Y) for multiple years?

**No — this is not statistically defensible, and Phase 1 will not build it.**

Reasoning, directly from the numbers above: with an average recount gap of ~3.6 years and a
long tail of intersections recounted only once in 42 years, the overwhelming majority of
`(intersection, year)` combinations inside the KSI window (2006–2026) simply have **no volume
observation in that exact year**. A year-by-year rate metric would require one of two invalid
moves:

1. Leave the denominator null for almost every intersection-year (the metric would be undefined
   for most of the data), or
2. Carry forward a stale count from a different year as a stand-in for "this year's" volume —
   which silently manufactures false precision. A trend line built this way could show, e.g., an
   apparent rise in collision rate at an intersection purely because the volume denominator was
   frozen at a count from 8 years earlier, while the real traffic volume may have changed
   substantially since — the metric would be measuring the age of the count, not the safety of
   the intersection.

Per the explicit instruction not to force this calculation when the denominator is temporally
incompatible: **it will not be built.**

### 1.5 What is the most statistically defensible metric we *can* calculate?

Three tiers, in order of how much the data actually supports each:

**Tier 1 — Fully valid across the entire 2006–2026 span, no volume data needed.**
Collision counts, KSI severity mix, road-user involvement (pedestrian/cyclist/motorcyclist),
and all temporal patterns (hour/weekday/month/season/year) computed directly from
`fact_collisions`. This is the backbone of the analysis and does not depend on the sparse TMC
data at all — see `ANALYTICAL_QUESTIONS.md` sections A–C.

**Tier 2 — A cross-sectional (point-in-time) relative risk score, explicitly not a
time-series rate.** For each intersection, use its single most-recent volume count
(`tmc_most_recent_summary_data`) as a **current exposure proxy**, and compute:

```
collisions_per_10k_movements =
    (matched KSI collisions at this intersection, trailing N years)
    / (total_vehicle + total_bike + total_pedestrian from the most recent count)
    * 10,000
```

This is valid **only** as a same-day relative ranking of intersections against each other
("which of today's busy intersections has a disproportionate collision history"), never as a
trend over time. It must carry a `count_recency_years` field (years between the count date and
today), because the most-recent count for a given location can itself be decades stale — the
recency distribution of "most recent" counts, pulled live from the API, shows this is a real
risk, not a hypothetical one:

| `latest_count_date` year | Locations whose *most recent* count is from that year |
|---|---|
| 1984–1999 | 89 locations (their newest count is 25–42 years old) |
| 2000–2009 | 861 locations |
| 2010–2019 | 1,264 locations |
| 2020–2026 | 4,120 locations |

Roughly **950 locations (15% of the 6,378) have not been recounted since before 2010** — using
their old count as "current" exposure without flagging it would be misleading. The metric
design (§4.2) restricts the default score to locations recounted within a defined recency
window and surfaces `count_recency_years` for every row so this can be filtered or
down-weighted rather than hidden.

**Tier 3 — Descriptive before/after narrative, not a citywide metric.** For the 2,511
intersections with counts in more than one era, a small number of high-interest
locations can be manually profiled (volume in an earlier era vs. a later era, alongside the
collision counts recorded in the years around each count date) as a narrative case study — not
a systematic, all-intersections metric, since coverage and timing are too irregular to
generalize.

**Decision: Phase 1's core deliverable is Tier 1 (pure collision analysis). Tier 2 is included
as a clearly-labeled secondary enrichment. Tier 3 is documented as a Phase 2 idea, not built
now.**

---

## Part 2 — Spatial Matching Investigation (required before designing the bridge table)

Per the instruction not to pick an arbitrary radius, the actual coordinate distributions were
computed before choosing a threshold.

### 2.1 Method

- Pulled all 2,550 Traffic Signal point locations (lat/long from the `Traffic Signal` GeoJSON
  datastore layer).
- Pulled all distinct KSI collisions with coordinates: **7,586 of 7,587 distinct `collision_id`
  values have usable lat/long** (only 1 missing — coordinate coverage is essentially complete).
- Computed the great-circle (haversine) distance from every collision to its single nearest
  signal — a 7,586 × 2,550 distance matrix, ~19.3M pairwise distances.

### 2.2 Result: the distribution is bimodal, with a sharp elbow around 10–15 m

| Distance band | Collisions in band | % of all collisions | Cumulative % |
|---|---|---|---|
| 0–5 m | 1,696 | 22.4% | 22.4% |
| 5–10 m | 1,452 | 19.1% | 41.5% |
| 10–15 m | 165 | 2.2% | 43.7% |
| 15–20 m | 79 | 1.0% | 44.7% |
| 20–50 m | 358 | 4.7% | 50.6% |
| 50–150 m | 1,477 | 19.5% | 78.3% |
| 150–500 m | 1,487 | 19.6% | 92.7% |
| 500–2,339 m | 160 | 2.4% | 100.0% |

There is a dense cluster of collisions essentially **coincident** with a signal (0–10 m = 41.5%
of all collisions), a sharp drop at 10–15 m, and then a long, smooth, gradually thickening tail
out past 500 m with **no second cluster or natural elbow** — i.e., there is no statistical
basis for a "near but not quite at" secondary tier. Beyond ~20 m the data behaves like general
background distance-to-nearest-signal across the city, not like a second population of
genuinely-matched collisions.

### 2.3 Cross-validation against KSI's own location fields

This shape was cross-checked against KSI's own recorded attributes (not derived from
coordinates at all), and the two independent signals agree closely:

| KSI field | Value | Distinct collisions | % |
|---|---|---|---|
| `accloc` | `At Intersection` | 3,156 | 41.6% |
| `traffictl` | `Traffic Signal` | 3,097 | 40.8% |

Both land within a point of the 41.5% found within 10 m purely from coordinates. This is strong
independent confirmation that the near-zero cluster in the distance histogram *is* real
signalized-intersection collisions (the police-report location fields agree), and that the long
tail (`traffictl = 'No Control'` at 47.6%, `Stop Sign` at 8.0%) genuinely represents
midblock and unsignalized-intersection collisions that have **no valid match** — not a data
quality gap to be closed by loosening the radius.

### 2.4 Chosen threshold: 20 meters

**20 m** is chosen as the match radius because it sits right at the end of the empirical
elbow (captures 44.7% cumulative — the 0–20 m dense cluster — while adding almost nothing past
15 m), it is large enough to absorb ordinary GPS/geocoding jitter (a few meters) without being
large enough to reach into the flat background tail, and it is corroborated by the independent
`traffictl`/`accloc` fields landing at the same ~41–42% mark. A looser radius (e.g. the 30–50 m
figure floated in Phase 0 before this investigation) would have started pulling in the flat
background tail — in a dense downtown grid where intersections can sit under 100 m apart, a
50 m radius risks attributing a collision to the *wrong* nearby intersection rather than
correctly leaving it unmatched.

**Expected outcome at 20 m: ~44.7% of KSI collisions (≈3,390 of 7,586) will match a signal;
the remaining ~55.3% are expected to be genuinely unmatched** (midblock, stop-sign-controlled,
or otherwise non-signalized locations) — this is a real finding about Toronto's collision
geography, not a modeling shortfall, and `bridge_collision_intersection` is designed
specifically to preserve and label that majority rather than force a false match.

### 2.5 `px` join validity check (TMC ↔ Traffic Signals)

One more empirical check before finalizing `dim_intersection`: TMC's `px` field is `int4`
(e.g. `2081`), while the Signals dataset's `PX` field is zero-padded **text** (e.g. `"0003"`).
After normalizing both to integers:

- 2,658 distinct `px` values appear in `tmc_most_recent_summary_data`.
- 2,550 distinct `PX` values appear in Traffic Signals.
- **2,450 overlap (92.2% of TMC's px values resolve to a real signal).** The 208 TMC-only
  values are most likely unsignalized intersections or beacons/crossovers still counted by TMC;
  the 100 Signals-only values are signals that have not yet had a TMC count taken. Both are
  legitimate partial coverage, not an error — `dim_intersection` uses a `LEFT JOIN`-friendly
  nullable relationship rather than assuming full overlap.

---

## Part 3 — Schema Design

### 3.1 Layered architecture

```
staging   →  1:1 load of each source file/API resource, minimal typing, no dedup
   ↓
clean     →  typed columns, standardized categories, geometry columns built,
             px normalized to a consistent integer type across sources
   ↓
analytics →  star schema: dim_date, dim_intersection, dim_neighbourhood,
             fact_collisions, fact_traffic_volume, bridge_collision_intersection
```

Three PostgreSQL schemas: `staging`, `clean`, `analytics`. PostGIS is enabled once, at the
database level (`CREATE EXTENSION IF NOT EXISTS postgis;`), and geometry columns exist starting
at the `clean` layer (staging keeps raw lat/long as plain numeric columns, matching the source
files exactly).

### 3.2 `analytics.dim_date`

Generated in SQL (not sourced externally), spanning the min/max of `accdate` in
`fact_collisions` (2006-01-01 → present).

| Column | Type | Notes |
|---|---|---|
| `date_key` | `date` **PK** | e.g. `2019-06-14` |
| `year` | `smallint` | |
| `month` | `smallint` | 1–12 |
| `month_name` | `text` | "June" |
| `quarter` | `smallint` | 1–4 |
| `day_of_month` | `smallint` | |
| `day_of_week` | `smallint` | 0=Sunday … 6=Saturday |
| `day_name` | `text` | "Friday" |
| `is_weekend` | `boolean` | |
| `season` | `text` | Winter/Spring/Summer/Fall, meteorological |

Not nullable — every column is derivable from `date_key`.

### 3.3 `analytics.dim_intersection`

Sourced from Traffic Signals Tabular. Grain: one row per signal `PX`.

| Column | Type | Notes |
|---|---|---|
| `intersection_key` | `serial` **PK** | surrogate |
| `px` | `integer` **UNIQUE, NOT NULL** | normalized from source `PX` text, leading zeros stripped |
| `main_street` | `text` | |
| `side1_street` | `text` | nullable — some records only have one cross street |
| `side2_street` | `text` | nullable |
| `signal_system` | `text` | e.g. "TransSuite" |
| `control_mode` | `text` | |
| `audible_ped_signal` | `boolean` | cast from source 1/0/null |
| `led_blankout_sign` | `boolean` | |
| `transit_preempt` | `boolean` | |
| `fire_preempt` | `boolean` | |
| `rail_preempt` | `boolean` | |
| `activation_date` | `date` | nullable — some historical signals lack this |
| `geom` | `geometry(Point, 4326)` **NOT NULL** | from source GeoJSON |

Index: `GIST (geom)`, unique btree on `px`.

### 3.4 `analytics.fact_traffic_volume`

Sourced from TMC `tmc_summary_data` (full history), **restricted to rows with non-null `px`**
(§1.1) — the 6,764 midblock rows (`px IS NULL`) are excluded from Phase 1 by design; they
belong conceptually with the deferred Midblock Volumes dataset (Phase 0 decision) and would
need `centreline_id`-based modeling of their own. Grain: one row per (`px`, `count_date`).

| Column | Type | Notes |
|---|---|---|
| `traffic_volume_key` | `serial` **PK** | surrogate |
| `px` | `integer` **NOT NULL** | natural key component |
| `count_date` | `date` **NOT NULL** | natural key component |
| `intersection_key` | `integer` **FK → dim_intersection, NULLABLE** | null for the ~7.8% of px values with no matching signal (§2.5) |
| `location_name` | `text` | as recorded by TMC, kept for audit/debug even though `intersection_key` is the real join |
| `count_duration` | `text` | source code, e.g. "8R"/"14"/"8S" — meaning not fully documented by the City; kept as-is, flagged as a data-quality follow-up |
| `total_vehicle`, `total_bike`, `total_pedestrian` | `integer` | |
| `total_heavy_pct` | `numeric(5,4)` | |
| `am_peak_start`, `pm_peak_start` | `timestamp` | nullable |
| `am_peak_vehicle`, `am_peak_bike`, `pm_peak_vehicle`, `pm_peak_bike` | `integer` | nullable |
| `n_appr_vehicle`, `e_appr_vehicle`, `s_appr_vehicle`, `w_appr_vehicle` | `integer` | per-approach vehicle volumes |
| `n_appr_bike`, `e_appr_bike`, `s_appr_bike`, `w_appr_bike` | `integer` | per-approach bike volumes |
| `geom` | `geometry(Point, 4326)` | |

Constraints: `UNIQUE (px, count_date)` — enforces the confirmed grain and will surface the 9
known duplicate rows (§1.1) at load time for manual review rather than silently double-counting.
Index: `GIST (geom)`, btree on `count_date`, btree on `intersection_key`.

### 3.5 `analytics.dim_neighbourhood`

| Column | Type | Notes |
|---|---|---|
| `neighbourhood_key` | `serial` **PK** | surrogate |
| `area_id` | `integer` **UNIQUE, NOT NULL** | source neighbourhood code |
| `area_name` | `text` **NOT NULL** | joins to KSI's free-text `neighbourhood` field on `lower(trim(...))` — validated during Phase 2 build: 100% of the 20,540 collision-person rows with a non-blank source neighbourhood value resolved to a real `area_name` (the remaining 151 rows have a genuinely blank source value, not a naming mismatch) |
| `geom` | `geometry(MultiPolygon, 4326)` **NOT NULL** | |

Index: `GIST (geom)`, unique btree on `area_id`.

### 3.6 `analytics.fact_collisions`

Sourced from KSI. **Grain: one row per person-involved-in-a-collision**, matching the source
exactly — `(collision_id, veh_no, per_no)` is the natural composite key. This grain is kept
(not collapsed to one-row-per-collision) because road-user role (`pedestrian`, `cyclist`,
`motorcyclist`, `injury` severity per person) is only meaningful at the person level; a
collision-level view is provided as a SQL view on top of this table (see
`ANALYTICAL_QUESTIONS.md`), not as a separate physical table, to avoid maintaining two sources
of truth.

| Column | Type | Notes |
|---|---|---|
| `collision_person_key` | `serial` **PK** | surrogate |
| `collision_id` | `text` **NOT NULL** | natural collision identifier, repeats across rows |
| `veh_no`, `per_no` | `integer` | nullable — complete the natural key with `collision_id` |
| `accdate` | `timestamp` **NOT NULL** | |
| `date_key` | `date` **FK → dim_date, NOT NULL** | `accdate::date` |
| `stname1`, `stname2`, `stname3` | `text` | nullable, source street names |
| `acclass` | `text` | `Fatal Injury` / `Non-Fatal Injury` / `Property Damage Only` — severity (exact source values, confirmed during Phase 2 build; earlier drafts of this doc used shorthand `Fatal`/`Property Damage`, which do not match the real data) |
| `accloc`, `traffictl` | `text` | nullable |
| `impactype`, `visible`, `light`, `rdsfcond`, `road_class` | `text` | nullable |
| `vehtype`, `invage`, `injury` | `text`/`integer` | nullable, person/vehicle-specific |
| `drivact`, `drivcond`, `pedact`, `pedcond`, `manoeuvre`, `cyclistype`, `road_user` | `text` | nullable |
| `fatal_no` | `integer` | nullable |
| `aggressive`, `distracted`, `cyclist`, `motorcyclist`, `other_micromobility`, `older_adult`, `pedestrian`, `red_light`, `school_child`, `heavy_truck` | `boolean` | cast from source `true`/`false` text. **Confirmed collision-level, not person-level** (Phase 3 build): identical across every person-row of a given `collision_id`, including the driver/passengers of that same event. `COUNT(DISTINCT collision_id) WHERE <flag>` correctly counts "collisions involving <x>"; `COUNT(*) WHERE <flag>` does **not** count "<x> people" — use `road_user = '<x>'` for that. See `docs/ANALYTICAL_FINDINGS.md` §03. |
| `wardname` | `text` | nullable |
| `division` | `text` | police division, nullable |
| `neighbourhood_key` | `integer` **FK → dim_neighbourhood, NULLABLE** | resolved from source `neighbourhood` text (validated 100% match rate, §3.5) |
| `latitude`, `longitude` | `double precision` | nullable (1 of 7,587 collisions lacks coordinates) |
| `geom` | `geometry(Point, 4326)` | nullable, built from lat/long where present |

Indexes: btree on `collision_id`, btree on `date_key`, btree on `neighbourhood_key`,
`GIST (geom)`.

### 3.7 `analytics.bridge_collision_intersection`

The spatial match result, kept as a **separate bridge table** rather than a column bolted onto
`fact_collisions` — per the design requirement, and because the match is collision-grain
(one location per collision event) while `fact_collisions` is person-grain, so a 1:1 column
would be redundantly repeated across every person-row of the same collision.

| Column | Type | Notes |
|---|---|---|
| `collision_id` | `text` **PK** | one row per distinct collision (7,587 rows total) |
| `collision_lat`, `collision_lon` | `double precision` | denormalized copy, for audit without joining back |
| `intersection_key` | `integer` **FK → dim_intersection, NULLABLE** | null when unmatched |
| `matched_px` | `integer` | nullable, denormalized for readability |
| `match_distance_m` | `numeric(8,2)` | nullable, null when unmatched |
| `match_status` | `text` **NOT NULL**, `CHECK IN ('matched','unmatched_no_candidate','unmatched_outside_radius')` | |
| `match_radius_m_used` | `numeric(6,2)` **NOT NULL** | the threshold applied at match time (20.00 for the Phase 1 batch) — kept so a future re-run with a different radius doesn't silently reinterpret old matches |
| `matched_at` | `timestamp` **NOT NULL DEFAULT now()** | batch audit timestamp |

Expected distribution at load time (§2.4): ~44.7% `matched`, ~55.3% `unmatched_outside_radius`,
`unmatched_no_candidate` expected to be effectively 0 rows in practice (a nearest signal always
exists somewhere in the city) but retained in the status domain for robustness — e.g. if a
future collision record has null coordinates, it lands here instead of silently being dropped.

Index: btree on `match_status`, btree on `intersection_key`.

---

## Part 4 — How the pieces connect

```
dim_date ──────────────< fact_collisions >────── dim_neighbourhood
                              |  (collision_id, shared 1:many
                              |   with the bridge below)
                              v
                    bridge_collision_intersection
                              |
                              v
                       dim_intersection >──────── fact_traffic_volume
                                                    (px, count_date)
```

- `fact_collisions.date_key → dim_date.date_key` (many-to-one)
- `fact_collisions.neighbourhood_key → dim_neighbourhood.neighbourhood_key` (many-to-one,
  nullable)
- `bridge_collision_intersection.collision_id` relates to the *set* of
  `fact_collisions.collision_id` rows sharing that id (one bridge row per collision event,
  many person-rows per collision in the fact — this is a 1-to-many relationship read from the
  bridge outward, not a simple FK-to-PK pair, since `fact_collisions` has no single-row PK at
  the collision grain)
- `bridge_collision_intersection.intersection_key → dim_intersection.intersection_key`
  (many-to-one, nullable)
- `fact_traffic_volume.intersection_key → dim_intersection.intersection_key` (many-to-one,
  nullable)

See [`ERD.md`](ERD.md) for a diagram version of this.

### 4.1 What Tier 1 analysis needs (no bridge/volume tables required)

`fact_collisions ⋈ dim_date ⋈ dim_neighbourhood` — fully populated, fully valid across
2006–2026, no exposure-denominator caveats.

### 4.2 What Tier 2 analysis needs (the cross-sectional relative risk score)

```
fact_collisions
  ⋈ bridge_collision_intersection ON collision_id  (keep only match_status = 'matched')
  ⋈ dim_intersection ON intersection_key
  ⋈ fact_traffic_volume ON intersection_key, filtered to each intersection's MAX(count_date)
```
with `count_recency_years = date_part('year', age(current_date, count_date))` computed and
exposed on every row so low-recency (stale-count) intersections can be filtered out or
down-weighted by the analyst rather than silently trusted — this metric definition, with its
formula, unit, grain, and limitations spelled out explicitly, is repeated in
`ANALYTICAL_QUESTIONS.md` §E.

---

## Part 5 — Analytical Layer (Phase 3)

The `analytics` Postgres schema described above (`fact_collisions`, `fact_traffic_volume`,
`dim_*`, `bridge_collision_intersection`) is built by `sql/warehouse/*.sql` (the file directory
was renamed from `sql/analytics/` to `sql/warehouse/` in Phase 3 to free up the `sql/analytics/`
*directory* name for the curated query/view layer below — the Postgres schema itself is still
called `analytics` and is unaffected by the file rename).

`sql/analytics/01_temporal/` … `07_quality/` hold 14 curated queries answering the questions in
`ANALYTICAL_QUESTIONS.md` (implementation status tracked there). Five of the fourteen are
persisted as views in the same `analytics` schema (`v_annual_ksi`, `v_road_user_involvement`,
`v_neighbourhood_ksi`, `v_intersection_risk`, `v_intersection_exposure`) — read-only, built
`FROM`/`JOIN` the fact/dim tables, adding no new stored data. Findings drawn from their output,
with evidence/interpretation/limitations, are in `ANALYTICAL_FINDINGS.md`.
