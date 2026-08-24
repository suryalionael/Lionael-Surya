# Power BI Specification

Toronto Mobility Intelligence — Phase 4. This is a design specification, not an implementation
— no `.pbix` file exists yet. It defines exactly what the dashboard will contain, where every
number comes from, and where the project's established limitations must stay visible, so that
review can happen before any building starts.

For the narrative this dashboard tells, see [`DASHBOARD_STORY.md`](DASHBOARD_STORY.md). For
where each SQL view's numbers come from and their full methodology, see
[`DATA_MODEL.md`](DATA_MODEL.md) and [`ANALYTICAL_FINDINGS.md`](ANALYTICAL_FINDINGS.md).

---

## 1. Data architecture

```
Power BI (.pbix)
   ↓  PostgreSQL connector, Import mode, DirectQuery not used (see S6)
PostgreSQL "analytics" schema views  (analytics.v_*, plus bridge_collision_intersection
                                       and dim_date imported directly)
   ↓  sql/analytics/0*_*/*.sql (Phase 3-4)
PostgreSQL "analytics" schema tables (fact_collisions, fact_traffic_volume, dim_*,
                                       bridge_collision_intersection)
   ↓  sql/warehouse/*.sql (Phase 2)
PostgreSQL "clean" schema
   ↓  sql/transformations/*.sql (Phase 2)
PostgreSQL "staging" schema
   ↓  etl/download + etl/ingestion (Phase 2)
Toronto Open Data (CKAN API) -- the 4 approved source datasets
```

**Power BI connects to PostgreSQL views and tables only — never to `data/raw/*.csv` or the
`staging`/`clean` schemas.** This is the single most important architectural rule in this
document: every number the dashboard shows must already exist, fully computed, in a named
`analytics.*` object with a documented formula. If a required metric doesn't exist yet, the fix
is a new SQL view (§5), never a DAX measure that re-derives business logic Power BI shouldn't
own — the project's most fragile logic (the collision-level-flag vs. person-level-field
distinction, the 20m spatial match, the cross-sectional exposure formula) all live in SQL
specifically so no report author can get them wrong in DAX.

### 1.1 Required objects to import

| Object | Kind | Grain | Used by |
|---|---|---|---|
| `analytics.v_annual_ksi` | view | year | Page 1, Page 4 |
| `analytics.v_road_user_involvement` | view | year | Page 1, Page 3 |
| `analytics.v_neighbourhood_ksi` | view | neighbourhood | Page 2 |
| `analytics.v_intersection_risk` | view | intersection (px) | Page 1, Page 2 |
| `analytics.v_intersection_exposure` | view | intersection (px) | Page 2 |
| `analytics.v_collision_hour_weekday` | view | (day_of_week, hour_of_day) | Page 3 |
| `analytics.v_collision_monthly_pattern` | view | month | Page 3 |
| `analytics.v_collision_seasonal_pattern` | view | season | Page 3 (tooltip/drill) |
| `analytics.bridge_collision_intersection` | table | collision | Page 1 KPI, Page 4 |
| `analytics.dim_date` | table | date | marked as Power BI's official **Date table** |

Ten objects total — no raw fact tables (`fact_collisions`, `fact_traffic_volume`) are imported
directly. Every number the dashboard needs is already aggregated to a stable, documented grain
in one of the eight views above; importing the raw facts as well would just invite a report
author to rebuild logic that already exists correctly in SQL.

### 1.2 Power BI relationship model

```
dim_date (marked Date table, 1)
    │ year  (dim_date.year has no direct 1-to-many key into the views below --
    │        see the Year slicer note in S4)
    │
v_annual_ksi (year) ──1:1 (by year)── v_road_user_involvement (year)

v_intersection_risk (px) ──1:1 (by px)── v_intersection_exposure (px)
    -- both are one-row-per-intersection; relate directly on px, no separate
    -- dim_intersection import needed since both views already carry
    -- main_street/side1_street for display

v_neighbourhood_ksi            -- standalone, no relationship needed (one page, one grain)
v_collision_hour_weekday       -- standalone
v_collision_monthly_pattern    -- standalone
v_collision_seasonal_pattern   -- standalone
bridge_collision_intersection  -- standalone (used only for the one Page 1 KPI + Page 4)
```

Relate `v_annual_ksi` ↔ `v_road_user_involvement` on `year` (both are one-row-per-year, so this
is a 1:1 relationship, not the usual 1:many star-schema pattern) and `v_intersection_risk` ↔
`v_intersection_exposure` on `px` (also 1:1). Every other view stands alone — forcing an
artificial relationship between, say, `v_neighbourhood_ksi` and `v_collision_hour_weekday`
would imply a cross-filtering interaction that doesn't correspond to anything real in the data
(they don't share a grain), so none is created.

### 1.3 Why no DirectQuery

Import mode is specified, not DirectQuery. The full dataset behind these 8 views is small (the
largest, `v_intersection_risk`, is ~1,556 rows) — Import mode gives instant slicer/cross-filter
response with no live-query latency to the database, and the project's refresh cadence (Toronto
Open Data updates on its own daily-to-ad-hoc schedule per dataset, not real-time — see
`DATASET_RESEARCH.md`) makes a live connection unnecessary. A scheduled refresh (§6.3) is the
right mechanism, not DirectQuery.

---

## 2. Page 1 — Toronto Mobility Overview

**Purpose:** Answer "what is happening?" for a reader who has 30 seconds — the citywide
headline numbers and the one or two trends that matter most, with an honest note about what
fraction of the picture this covers spatially.

**Audience:** A public-sector manager, councillor's office staffer, or another analyst getting
oriented before drilling into Page 2 or 3. Assume no prior familiarity with this project's
methodology.

**Key questions answered:** How many people are being killed or seriously injured, is it
getting better or worse, who is most affected, and how much of that picture can this data even
see spatially?

### 2.1 KPI cards (5, top row)

| # | KPI | Formula | Source |
|---|---|---|---|
| 1 | Total KSI Collisions | `SUM(v_annual_ksi.ksi_collision_count)` across all years | `v_annual_ksi` |
| 2 | Fatal Collisions | `SUM(v_annual_ksi.fatal_collision_count)` | `v_annual_ksi` |
| 3 | Fatal Share | `Fatal Collisions / Total KSI Collisions` (recompute the ratio from the two sums above, not an average of `fatal_share_pct` — averaging pre-computed yearly percentages would weight small and large years equally, which is wrong) | `v_annual_ksi` |
| 4 | Pedestrian + Cyclist Involvement | `(SUM(ped_collision_count) + SUM(cyclist_collision_count)) / SUM(ksi_collision_count)`, all from `v_road_user_involvement` — note this is an upper-bound-ish approximation since a collision involving both a pedestrian and a cyclist would be counted once in the numerator's sum of two columns but the two columns aren't mutually exclusive; label this KPI "Pedestrian OR Cyclist Involvement" precisely, not "pedestrian + cyclist" | `v_road_user_involvement` |
| 5 | Spatially Matched | `COUNT(*) FILTER (match_status='matched') / COUNT(*)` from `bridge_collision_intersection` | `bridge_collision_intersection` |

KPI 5 is the one every reviewer must see on the landing page — it is the project's central
honesty check, not a technical footnote (§7.4).

### 2.2 Visual 1 — Annual KSI & Fatal Trend (combo line chart)

- **Analytical question:** Is the citywide KSI count trending up, down, or flat, and how does
  the fatal count move with it?
- **Data source/view:** `analytics.v_annual_ksi`
- **X-axis:** `year` (2006–2026)
- **Y-axis:** `ksi_collision_count` (line 1) and `fatal_collision_count` (line 2, same axis —
  both are collision counts, no dual-axis needed since fatal is a subset of KSI and the scale
  difference is informative, not distorting)
- **Dimensions:** none beyond year (no legend/series split)
- **Filters:** none page-level; this chart is the reason the Year slicer exists (§4)
- **Aggregation:** none — `v_annual_ksi` is already at year grain, values plotted as-is
- **Why this visual is appropriate:** a two-line trend is the simplest, most legible way to show
  two related counts moving together (or apart) over 21 years — exactly what a line chart is for.
- **Potential misleading interpretation:** the final point (2026) is a partial year — a
  connected line implies continuity a partial year doesn't have. **Mitigation:** the 2026 point
  must be visually distinguished (dashed line segment or a distinct marker), driven by
  `v_annual_ksi.is_current_year_partial`, with a visible annotation ("2026: partial year").
  Without this, a reader will misread the 2026 dip as a real decline.

### 2.3 Visual 2 — Road-User Involvement Trend (multi-line chart)

- **Analytical question:** How has pedestrian, cyclist, and motorcyclist involvement in KSI
  collisions changed over time?
- **Data source/view:** `analytics.v_road_user_involvement`
- **X-axis:** `year`
- **Y-axis:** collision count
- **Dimensions:** series = `ped_collision_count`, `cyclist_collision_count`,
  `motorcyclist_collision_count` (three lines, one per road-user type)
- **Filters:** none page-level
- **Aggregation:** none — already year grain
- **Why this visual is appropriate:** three comparable time series on one chart is the standard,
  legible way to compare trend shape across categories without forcing a reader to flip between
  charts.
- **Potential misleading interpretation:** these are **collision counts** (collisions involving
  that road-user type), not person counts — the chart must be titled and labeled using
  "collisions involving a [pedestrian/cyclist/motorcyclist]," never "[pedestrians/cyclists]
  injured," per the confirmed collision-level-flag distinction (`DECISION_LOG.md`, Phase 3). A
  tooltip note should state this explicitly, since it is the single easiest mistake a report
  viewer could make with this data.

### 2.4 Visual 3 — Citywide Neighbourhood Overview (map, de-emphasized)

- **Analytical question:** At a glance, where in the city is the KSI burden concentrated?
- **Data source/view:** `analytics.v_neighbourhood_ksi`
- **X-axis / Y-axis:** N/A — Shape Map visual (see §5.1 for the boundary-file requirement)
- **Dimensions:** color saturation = `ksi_collision_count`; match key = `area_name`
- **Filters:** none page-level
- **Aggregation:** none — already neighbourhood grain
- **Why this visual is appropriate:** a compact, low-detail map orients the reader
  geographically before Page 2's deeper dive — deliberately the *raw count* version only, kept
  small and unlabeled with rankings, since Page 1's job is orientation, not analysis.
- **Potential misleading interpretation:** this is the exact metric flagged in
  `ANALYTICAL_FINDINGS.md` as misleading on its own (raw count rewards large land area, e.g.
  West Humber-Clairville) — **this is precisely why this map must stay small and
  low-emphasis on Page 1**, with a one-line caption ("Raw counts — see Page 2 for
  land-area-normalized density") and no ranking table attached here. The normalized version
  and full discussion live on Page 2, not here.

**Page 1 explicitly excludes:** road-class breakdowns, intersection-level detail, exposure
metrics, and hour/day/season patterns — all of which have a home on Page 2 or 3. Page 1 is
capped at 5 KPIs + 3 visuals by design.

---

## 3. Page 2 — Where

**Purpose:** Answer "where is it happening?" — and specifically, teach the reader that "where
the most collisions are" and "where collisions are concentrated relative to size" are two
different questions with two different answers, using this project's own data as the
illustration.

**Audience:** Same as Page 1, now drilling into geography — plausibly a transportation planner
comparing specific neighbourhoods or corridors.

**Key questions answered:** Which neighbourhoods and intersections show the most KSI activity,
does that hold up once normalized, and where does volume-relative risk look different from raw
counts?

### 3.1 Visual 1 — Neighbourhood Choropleth Map (with raw-count/density toggle)

- **Analytical question:** Which neighbourhoods have the most KSI collisions, and does that
  ranking change once normalized by land area?
- **Data source/view:** `analytics.v_neighbourhood_ksi`
- **X-axis / Y-axis:** N/A — Shape Map, matched by `area_name`
- **Dimensions:** color = a **field parameter** toggling between `ksi_collision_count` and
  `ksi_density_per_km2` (Power BI field parameters let a slicer swap which measure drives the
  color scale without duplicating the visual)
- **Filters:** none page-level beyond the Neighbourhood slicer (§4)
- **Aggregation:** none
- **Why this visual is appropriate:** a choropleth is the standard way to show a rate/count
  distributed across defined polygons; the toggle turns the map itself into the demonstration of
  the raw-vs-normalized distinction, rather than requiring two separate maps competing for space.
- **Potential misleading interpretation:** without the toggle clearly labeled and defaulting to
  a neutral state (not defaulting to raw count, which is the more dramatic-looking but more
  misleading view), a reader could take a screenshot of the raw-count view and treat it as "the
  danger map." The toggle's current state must be visible as an on-visual label, not just a
  slicer position that could be missed.

### 3.2 Visual 2 — Raw Count vs. Density Ranking Table

- **Analytical question:** Concretely, which neighbourhoods change rank the most between raw
  count and density — i.e., where would "most collisions" and "most concentrated" give a
  reader a different answer?
- **Data source/view:** `analytics.v_neighbourhood_ksi`
- **X-axis / Y-axis:** N/A — table
- **Dimensions/columns:** `area_name`, `ksi_collision_count`, `rank_by_raw_count`,
  `ksi_density_per_km2`, `rank_by_density`, `area_km2`
- **Filters:** default sorted by `rank_by_raw_count`; a "largest rank swing" sort option
  (computed as `ABS(rank_by_raw_count - rank_by_density)` in a DAX measure — this is a display
  sort, not new business logic, so it's an acceptable Power BI-side calculation) surfaces cases
  like West Humber-Clairville (#1 raw → #120 density) directly
- **Aggregation:** none — row-level table
- **Why this visual is appropriate:** the specific numeric contrast (`ANALYTICAL_FINDINGS.md`'s
  West Humber-Clairville example) is best communicated in a table where both rankings sit
  side-by-side in the same row — a map or bar chart would require the reader to mentally compare
  two separate visuals.
- **Potential misleading interpretation:** `area_km2` must stay visible in this table (not
  hidden), since density-per-km² can otherwise look like an unexplained, arbitrary number — the
  area column is what lets a reader verify the metric makes sense.

### 3.3 Visual 3 — Intersection Hotspot Map (bubble map)

- **Analytical question:** Which specific intersections show the highest observed KSI activity?
- **Data source/view:** `analytics.v_intersection_risk`
- **X-axis / Y-axis:** N/A — Map/ArcGIS visual, `latitude`/`longitude`
- **Dimensions:** bubble size = `matched_ksi_collision_count`; bubble color = `fatal_collision_count`
  (a sequential color scale, not traffic-light red/green — see §6)
- **Filters:** none page-level beyond Neighbourhood (spatial filter via the map's own pan/zoom,
  not the slicer, since intersections aren't tagged with a neighbourhood name in this view)
- **Aggregation:** none — 1,556 points, well within Power BI map performance limits; **raw
  individual collision points are never plotted** (per the brief's explicit caution) — this map
  plots the already-aggregated intersection grain established in Phase 3, not the underlying
  ~7,586 collisions
- **Why this visual is appropriate:** a bubble map at the intersection grain is the natural way
  to show point-level geographic concentration without the performance or legibility problems of
  plotting every raw collision.
- **Potential misleading interpretation:** per `ANALYTICAL_FINDINGS.md`'s intersection-ranking
  finding, this only covers the ~44.7% of KSI collisions that spatially matched — an intersection
  with heavy midblock activity just outside the 20m radius will look artificially quiet here.
  **The page must carry a visible caption**: "Shows collisions matched to a signalized
  intersection within 20m (~44.7% of citywide KSI collisions) — see Page 4 for methodology."
  Tooltip on hover must never use the word "dangerous" — "highest observed count" only, per the
  project's metric-discipline rule.

### 3.4 Visual 4 — Pedestrian/Cyclist Concentration by Neighbourhood (bar chart)

- **Analytical question:** Which neighbourhoods have the highest concentration of
  pedestrian/cyclist-involved KSI collisions?
- **Data source/view:** `analytics.v_neighbourhood_ksi`
- **X-axis:** `area_name` (top 15 by combined pedestrian + cyclist count, sorted descending)
- **Y-axis:** collision count
- **Dimensions:** series = `pedestrian_collision_count`, `cyclist_collision_count` (stacked or
  clustered bars)
- **Filters:** Top-N filter (15), overridable by the Neighbourhood slicer
- **Aggregation:** none — already neighbourhood grain
- **Why this visual is appropriate:** a ranked bar chart is the clearest way to compare a
  bounded category (top 15 neighbourhoods) across two series.
- **Potential misleading interpretation:** same collision-level-flag caveat as Page 1 Visual
  2 — these are collisions *involving* a pedestrian/cyclist, not counts of people. Also: this is
  a raw-count ranking (no density normalization applied here, unlike Visual 1), so the same
  land-area caveat applies and should be a visible footnote, not restated at full length again.

### 3.5 Visual 5 — Relative Exposure Ranked Table

- **Analytical question:** Among matched intersections, which show a disproportionate recent
  collision count relative to their most recently observed traffic volume?
- **Data source/view:** `analytics.v_intersection_exposure`
- **X-axis / Y-axis:** N/A — table, default sorted by `collisions_per_10k_movements` descending
- **Dimensions/columns:** `main_street`, `side1_street`, `matched_ksi_collisions_2021_2025`,
  `traffic_count_date`, `count_recency_years`, `total_movements`, `collisions_per_10k_movements`
- **Filters:** **default-filtered to `recency_reliable = TRUE`** (count within the last 10
  years) — this is a required default, not optional, since including stale-count rows
  unfiltered would let a 20-year-old traffic count masquerade as current exposure; a visible
  toggle can let an analyst opt into seeing the full unfiltered set, off by default
- **Aggregation:** none — row-level table
- **Why this visual is appropriate:** a ranked table (not a chart) is correct here specifically
  because this metric needs its caveats to stay legible next to every number — a bar chart
  strips out the `traffic_count_date`/`count_recency_years` context that makes this metric
  honest.
- **Potential misleading interpretation:** this is the project's highest-risk-of-misreading
  metric. **This table must carry a permanent, non-dismissible caption**: "Cross-sectional
  snapshot, NOT a historical trend — numerator spans 2021–2025, denominator is a single day's
  count. Never describe this as 'the 2023 rate' or any year-specific rate." (§7.3 restates why.)

---

## 4. Page 3 — When & Who

**Purpose:** Answer "when is it happening?" and "who is involved?" together, since Vision
Zero's focus on vulnerable road users is itself a "who" question best read alongside "when."

**Audience:** Same as prior pages; also useful for anyone planning enforcement or
safety-campaign timing.

**Key questions answered:** What hour/day/month/season sees the most KSI activity, and how does
pedestrian/cyclist/motorcyclist involvement and severity break down?

### 4.1 KPI cards (3, top row)

| # | KPI | Formula | Source |
|---|---|---|---|
| 1 | Peak Hour × Day | the `(day_name, hour_of_day)` pair with `MAX(ksi_collision_count)` | `v_collision_hour_weekday` |
| 2 | Highest-Fatal-Share Season | the `season` with `MAX(fatal_share_pct)` | `v_collision_seasonal_pattern` |
| 3 | VRU Share Range | `MIN(vru_share_pct)`–`MAX(vru_share_pct)` across all years (a range, e.g. "49%–64%," not a single number, since `ANALYTICAL_FINDINGS.md` specifically found no sustained trend — a single average would misrepresent that as a stable figure) | computed from `v_road_user_involvement` (`(ped_collision_count + cyclist_collision_count)/ksi_collision_count` per year, min/max across years) |

### 4.2 Visual 1 — Hour × Weekday Heatmap

- **Analytical question:** What hour of day and day of week see the most KSI collisions?
- **Data source/view:** `analytics.v_collision_hour_weekday`
- **X-axis:** `hour_of_day` (0–23)
- **Y-axis:** `day_name` (ordered Monday–Sunday via `day_of_week`, not alphabetically)
- **Dimensions:** color intensity = `ksi_collision_count`
- **Filters:** none
- **Aggregation:** none — the view is already the full 168-cell grid, purpose-built for this
  exact visual (§5.2)
- **Why this visual is appropriate:** a matrix/heatmap is the standard, correct visual for two
  categorical dimensions crossed with one measure — a bar chart could only show one dimension at
  a time.
- **Potential misleading interpretation:** color-intensity heatmaps can visually imply a smooth
  gradient/trend across hours that doesn't exist — adjacent hours are independent counts, not
  points on a continuous curve. A sequential (not diverging) color scale avoids implying a
  "good/bad" binary that doesn't apply here.

### 4.3 Visual 2 — Monthly Pattern (bar chart, with seasonal grouping)

- **Analytical question:** Which calendar months see more or fewer KSI collisions, and how does
  that align with the broader seasonal pattern?
- **Data source/view:** `analytics.v_collision_monthly_pattern` (primary); `v_collision_seasonal_pattern`
  available as a drill-up/tooltip reference, not a separate chart
- **X-axis:** `month_name` (ordered January–December)
- **Y-axis:** `ksi_collision_count`
- **Dimensions:** color = `fatal_share_pct` (a second encoding on the same bars, e.g. bar
  outline or a secondary small-multiple, so severity and volume are both visible without a
  second full chart)
- **Filters:** none
- **Aggregation:** none
- **Why this visual is appropriate:** a single ranked bar chart covers both the "which month"
  question and, via color, the severity question, without needing four charts (month count,
  month severity, season count, season severity).
- **Potential misleading interpretation:** `month_year_coverage` (11 months have 21 years of
  data, September–December have only 20, since 2026 is a partial year through early August) is
  not itself plotted — if a future refresh makes this asymmetry larger, the chart could quietly
  bias toward the higher-coverage months. A tooltip field showing `month_year_coverage` is
  required so this stays checkable.

### 4.4 Visual 3 — Road-User Severity Trend (stacked bar / combo)

- **Analytical question:** How does the fatal share within each road-user type's KSI
  involvement change over time?
- **Data source/view:** `analytics.v_road_user_involvement` (using the Phase 4-added
  `ped_fatal_collision_count`, `cyclist_fatal_collision_count`, `motorcyclist_fatal_collision_count`)
- **X-axis:** `year`
- **Y-axis:** collision count
- **Dimensions:** series = the three road-user types; a DAX measure computes
  `{type}_fatal_collision_count / {type}_collision_count` for the tooltip's severity percentage
  (a ratio of two imported columns — display-layer arithmetic, not new business logic)
- **Filters:** Year slicer applies natively (this view has a year column)
- **Aggregation:** none
- **Why this visual is appropriate:** ties Page 1's involvement trend to severity without
  needing a fourth chart — reuses the same view already imported for Page 1.
- **Potential misleading interpretation:** annual fatal counts per road-user type are small
  (single digits to low tens some years) — year-over-year swings in the severity ratio will be
  visually noisy; the chart should default to showing counts (which read more stably) with the
  percentage available on hover, not as the primary encoding.

### 4.5 Visual 4 — Severity Mix by Road-User Type (bar chart, all-time)

- **Analytical question:** Across the full 2006–2026 history, how does fatal share compare
  between pedestrian-involved, cyclist-involved, motorcyclist-involved, and vehicle-occupant-only
  collisions?
- **Data source/view:** `analytics.v_road_user_involvement`, summed across all years in a DAX
  measure (`SUM(ped_fatal_collision_count)/SUM(ped_collision_count)`, etc. — this reproduces
  `sql/analytics/02_severity/010_severity_by_road_user_type.sql`'s citywide totals from the
  already-imported view rather than requiring a separate view import; see §5.3 for why this one
  query was not also promoted to a view)
- **X-axis:** road-user category (Pedestrian / Cyclist / Motorcyclist / Vehicle-occupants-only)
- **Y-axis:** `fatal_share_pct`
- **Dimensions:** none beyond category
- **Filters:** none (deliberately all-time — Phase 3's finding on this was citywide, not
  year-sliced)
- **Aggregation:** `SUM()` across years per category, computed in DAX
- **Why this visual is appropriate:** a single bar chart directly shows the
  `ANALYTICAL_FINDINGS.md` finding (pedestrian 17.54%, motorcyclist 13.67%, vehicle-only 12.00%,
  cyclist 5.86%) in the clearest possible form.
- **Potential misleading interpretation:** these categories are not mutually exclusive (a
  collision can involve both a pedestrian and a cyclist) — bars must not be described as parts
  of a whole (no 100%-stacked framing, no pie chart), and a footnote should say so explicitly.

---

## 5. Gap analysis: SQL changes made to support this design

Per the instruction to identify gaps and propose (and where small, implement) the smallest SQL
change rather than pushing logic into Power BI, six additive changes were made in Phase 4 — full
detail and rationale in each file's own header comment and in `DECISION_LOG.md`:

1. **`v_neighbourhood_ksi`** — added `pedestrian_collision_count`, `cyclist_collision_count`
   (Page 2 Visual 4).
2. **`v_intersection_risk`** — added `latitude`, `longitude` (Page 1 Visual 3 map key, Page 2
   Visual 3 map).
3. **`v_road_user_involvement`** — added `ped_fatal_collision_count`,
   `cyclist_fatal_collision_count`, `motorcyclist_fatal_collision_count` (Page 3 Visual 3).
4. **`v_collision_hour_weekday`** (new) — the full 168-cell grid version of Phase 3's top-20
   curated query, required because a heatmap needs the complete grid (Page 3 Visual 1).
5. **`v_collision_seasonal_pattern`** (new) — view version of Phase 3's seasonal query (Page 3
   Visual 2 tooltip/drill).
6. **`v_collision_monthly_pattern`** (new) — genuinely new grain, not built in Phase 3 (month
   wasn't broken out from season); required because Page 3 explicitly asks for "month" distinct
   from "season" (Page 3 Visual 2).

All six are additive (new columns appended at the end of existing views, or entirely new views)
— no existing Phase 3 column was renamed, removed, or reordered, and the original curated
Phase 3 query files (`020_weekday_hour_pattern.sql`, `030_seasonal_pattern.sql`,
`010_severity_by_road_user_type.sql`) are untouched.

**One gap identified and deliberately NOT closed with a new view:** `02_severity/010_severity_by_road_user_type.sql`
(the all-time severity-by-road-user-type breakdown) was not promoted to a persisted view,
because `v_road_user_involvement`'s Phase 4 extension already carries everything needed to
reproduce it via a `SUM()` DAX measure (§4.5) — adding a seventh view for numbers already
reachable from an imported view would be redundant.

---

## 6. Filters

### 6.1 Global filters

| Filter | Type | Applies to |
|---|---|---|
| **Year** | Range slicer, 2006–2026 | `v_annual_ksi`, `v_road_user_involvement` (Page 1, Page 3 Visual 3) only — see the explicit limitation below |
| **Neighbourhood** | Searchable dropdown slicer | `v_neighbourhood_ksi` (Page 2), and the map's pan/zoom on Page 2 Visual 3/Visual 1 |

**Important interaction limitation, stated on the dashboard, not just in this document:** the
Year slicer does **not** filter `v_neighbourhood_ksi`, `v_intersection_risk`,
`v_intersection_exposure`, `v_collision_hour_weekday`, `v_collision_seasonal_pattern`, or
`v_collision_monthly_pattern` — none of those views carry a `year` column, by design (per each
view's own header comment, several were deliberately built as all-time or fixed-window
aggregates specifically to avoid noisy small-count per-year splits at fine grains like
per-intersection or per-hour). A reader moving the Year slicer and expecting Page 2/3 to update
would be misled; the slicer's visual placement should make clear (e.g. a "Page 1 filter" label,
or simply not appearing on Page 2/3 at all) that it is scoped, not global. Building
year-sliceable versions of the geographic/fine-grain views is a legitimate future enhancement,
not done here to avoid re-fragmenting statistically thin per-year-per-intersection or
per-year-per-hour counts (see `DECISION_LOG.md` for the explicit call on this).

### 6.2 Page-scoped filters

- **Page 3:** a Weekday/Weekend toggle, computed from `v_collision_hour_weekday.day_of_week`
  (`day_of_week IN (0,6)` = weekend), affecting Visual 1 only.
- **Page 2:** the Top-N control on Visual 4 (default 15, adjustable 5–30).

### 6.3 Filters deliberately not built

- **Severity (Fatal/Non-Fatal) as a global slicer** — every view already reports
  `fatal_collision_count`/`fatal_share_pct` as columns, not as a row-level category to filter
  by; the aggregated grain of these views means a "show only fatal" slicer has nothing to filter
  against without re-fetching row-level `fact_collisions` data, which would defeat the purpose
  of importing pre-aggregated views. Fatal-specific analysis is already visible via the
  dedicated severity columns/visuals on each page.
- **Road-user type as a global slicer** — same reasoning: `v_annual_ksi` has no
  pedestrian/cyclist column to filter by (that's what `v_road_user_involvement` is for), and the
  views that do carry per-type columns (`v_road_user_involvement`, `v_neighbourhood_ksi`) show
  all three types side-by-side by design, which is more informative for comparison than
  isolating one at a time. No analytical value would be added by this filter, per the brief's
  own instruction not to build filters without one.

---

## 7. Color & accessibility system

- **Neutral (structural/navigation):** a single desaturated blue-grey, used for axis lines, KPI
  card backgrounds, and any "informational" count that isn't itself a severity signal (e.g. the
  Total KSI Collisions KPI).
- **Warning (elevated, not fatal):** a single amber/orange, used consistently for anything
  flagged for review — the Page 4 monitoring flags (§8), `unmatched_outside_radius` in any
  match-status breakdown, `REVIEW` flags from the quality-monitoring queries.
- **Severe/fatal:** a single deep red, reserved **only** for fatal-specific measures
  (`fatal_collision_count`, `fatal_share_pct`) — never reused for "high count" in a
  non-severity context, so red always means "fatal" specifically, not "big number."
- Sequential color scales (single-hue, increasing saturation) are used for all choropleth/bubble
  maps and the heatmap — never a red-green diverging scale, both because red-green is not
  colorblind-safe and because none of this project's metrics have a natural "good/bad" midpoint
  to diverge around (a collision count doesn't have a meaningful "zero is bad, high is good"
  axis the way, say, profit does).
- No visual encodes a distinction using color alone: the Page 1 partial-year marker uses both a
  dashed line style AND a text annotation; match-status uses both color AND a text label/legend,
  never color alone.
- Minimum contrast ratio 4.5:1 for all text on background, per WCAG AA — applies to KPI card
  numerals against their background and any on-visual labels.

---

## 8. Methodology & Limitations (Page 4, supplementary)

Not one of the 3 primary pages, but a required companion page — the brief's 7 limitations are
substantial enough that cramming them into tooltips on the analytical pages would either bury
them or clutter those pages. Page 4 is a low-visual, text-and-diagram page:

1. **KSI is severity-filtered** — this project cannot describe "all collisions," only the
   killed-or-seriously-injured subset. (Source: `DATASET_RESEARCH.md`.)
2. **TMC exposure is cross-sectional** — the architecture diagram from §1 repeated here, with
   the explicit statement that traffic-volume counts are not temporally aligned with collision
   history (`DATA_MODEL.md` §1).
3. **Traffic-normalized metrics are not historical trends** — restates Page 2 Visual 5's caption
   at full length, since this is the project's single highest-risk-of-misinterpretation number.
4. **Spatial matching covers ~44.7% of geocoded collisions** — the same figure as Page 1 KPI 5,
   explained: which collisions match (signalized-intersection-adjacent) and which structurally
   cannot (midblock, unsignalized) — restating the `accloc`/`traffictl` cross-validation from
   `DATA_MODEL.md` §2.3 briefly.
5. **Raw neighbourhood collision count ≠ risk** — restates the West Humber-Clairville example
   from Page 2, with the actual numbers (#1 raw, #120 density) as a permanent reference so a
   reader can look this specific fact up without hunting through Page 2's interactive table.
6. **Infrastructure relationships are not causal** — this project does not include an
   infrastructure-vs-collision-count visual for exactly this reason (`ANALYTICAL_QUESTIONS.md`
   D2 was deliberately not built — `DECISION_LOG.md` Phase 3 entry) — stated here so a reader
   who might otherwise expect that analysis understands why it's absent, not missing by oversight.
7. **Recent `road_class` missingness may reflect verification lag, not a data problem** — the
   2024–2026 completeness drop found in `07_quality/020_temporal_and_category_drift.sql`,
   with the explicit "not yet confirmed, re-check after re-ingestion" status from
   `ANALYTICAL_FINDINGS.md`.

Also on this page: the architecture diagram from §1 (full pipeline, staging through Power BI),
`staging.ingestion_log`'s most recent `city_last_refreshed`/`downloaded_at` values as a small
"data as of" table (so a viewer can see exactly how current the underlying data is), and a link
back to this document and `ANALYTICAL_FINDINGS.md` for anyone who wants the full detail.

---

## 9. Implementation plan (for Phase 5, not done now)

### 9.1 Connection setup

1. Power BI Desktop → Get Data → PostgreSQL database.
2. Server: `localhost` (or the deployment host), port from `.env`'s `POSTGRES_PORT` (5433 in
   local dev). Database: `toronto_mobility`.
3. Import mode (not DirectQuery — §1.3). Select the 10 objects listed in §1.1 only.
4. Mark `dim_date` as the official Date table (Model view → right-click `dim_date` → "Mark as
   date table," using `date_key`).
5. Build the two 1:1 relationships from §1.2 (`year` and `px`) manually — Power BI's
   auto-detect may propose incorrect relationships (e.g. guessing a relationship on `px` between
   `v_intersection_risk` and an unrelated column) and should be reviewed, not accepted blindly.

### 9.2 Boundary file for the neighbourhood Shape Map

Power BI's Shape Map visual needs a TopoJSON boundary file, matched by `area_name` — this is a
one-time asset, not something Power BI generates. Recommended: convert the neighbourhood
GeoJSON already downloaded at `data/raw/neighbourhoods/*.csv` (specifically its `geometry`
column, or re-fetch the GeoJSON resource directly from the same CKAN package —
`docs/DATASET_RESEARCH.md` has the source URL) via mapshaper.org or a similar GeoJSON→TopoJSON
converter, matching on `AREA_NAME`. This conversion happens outside Power BI and outside this
project's SQL layer — it is a Phase 5 setup step, not built now.

### 9.3 Refresh considerations

- Recommended cadence: weekly, not real-time — matches the practical cadence at which
  `make ingest` would realistically be re-run (Toronto Open Data's own refresh cadence per
  dataset varies from daily to ad-hoc — `DATASET_RESEARCH.md`), and avoids refreshing a
  dashboard more often than the underlying pipeline actually produces new numbers.
- Before any scheduled refresh is wired up, the full pipeline
  (`make ingest && make transform && make warehouse && make views && make validate`) must
  complete with 0 FAIL rows in the validation suite — a refresh should not run silently against
  data that failed validation. This is a Phase 5 orchestration concern (e.g. a wrapper script
  gating the Power BI refresh trigger on the validation suite's exit code), not built now.
- `staging.ingestion_log` already records `city_last_refreshed` and `downloaded_at` per dataset
  per load (Phase 2) — Page 4's "data as of" table (§8) reads directly from this table, so no
  new tracking mechanism is needed.

### 9.4 Performance considerations

- All 10 imported objects are small (largest is `v_intersection_risk` at ~1,556 rows;
  `v_collision_hour_weekday` is fixed at 168 rows) — Import mode with these volumes gives
  sub-second slicer response with no partitioning or aggregation-table strategy needed.
- The neighbourhood Shape Map (158 polygons) and intersection bubble map (~1,556 points) are
  both well within Power BI's map visual limits (typically comfortable well past 5,000 points
  for a bubble map, and Shape Map is bounded by the TopoJSON file's own complexity, not row
  count) — no additional spatial aggregation is needed beyond what Phase 3/4 already built.
- No individual raw collision point layer is included anywhere in this design, per the brief's
  explicit performance caution (§3.3) — if a future phase wants a raw-point drill-through, that
  would need a new, deliberately-scoped view (e.g. filtered to a single selected intersection or
  neighbourhood) rather than an unfiltered ~7,586-point layer.
