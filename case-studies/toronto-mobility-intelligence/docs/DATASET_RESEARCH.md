# Dataset Research

Toronto Mobility Intelligence — Phase 0 research into City of Toronto Open Data.

All datasets below were pulled from the City of Toronto Open Data Portal (CKAN instance):
`https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/`. The public-facing catalogue
pages are at `https://open.toronto.ca/dataset/<slug>/`, but those pages are React-rendered and
carry no static metadata, so all figures here (row counts, fields, refresh dates) were pulled
directly from the CKAN `package_show` / `datastore_search` API, not scraped from the HTML.
Row counts and "Last Refreshed" dates reflect the live API response as of **2026-08-22**.

Datasets are grouped by verdict: **Recommended** (used in the project) and **Investigated, not
recommended** (evaluated and rejected, with reasons).

---

## Recommended datasets

### 1. Motor Vehicle Collisions Involving Killed or Seriously Injured Persons (KSI)

- **Official source URL:** https://open.toronto.ca/dataset/motor-vehicle-collisions-involving-killed-or-seriously-injured-persons/
- **CKAN package id:** `motor-vehicle-collisions-involving-killed-or-seriously-injured-persons`
- **Active datastore resource id:** `9c9a9b60-95c1-4541-ad44-15c4a643aff9`
- **Description:** Every person involved in a collision on Toronto's road network where at least
  one person was killed or seriously injured, since 2006. Sourced from Toronto Police Service
  collision reports, published by Transportation Services as the core measurement dataset for
  the Vision Zero Road Safety Plan.
- **File/API format:** CSV (datastore-backed, queryable via CKAN `datastore_search`/SQL API),
  plus static CSV/SHP/GPKG/GeoJSON exports in EPSG:4326 and EPSG:2952.
- **Approximate row count:** 20,691 records (datastore `total`, live count).
- **Historical date range:** 2006-01-01 to present.
- **Update frequency:** Refresh rate listed as **Daily**; last refreshed 2026-08-21. Note: KSI
  records lag real-world occurrence — fatalities take ~1–2 weeks to verify, serious injuries
  2–3 months, so the most recent 1–3 months of data should be treated as provisional/incomplete.
- **Important columns:** `collision_id`, `accdate` (timestamp), `stname1`/`stname2`/`stname3`
  (streets), `acclass` (Fatal / Non-Fatal Injury / Property Damage), `impactype`, `visible`
  (weather), `light`, `rdsfcond` (road surface condition), `road_class`, `veh_no`, `vehtype`,
  `per_no`, `invage`, `injury`, `drivact`, `drivcond`, `pedact`, `pedcond`, `manoeuvre`,
  `cyclistype`, `road_user`, `fatal_no`, and boolean-style flag columns `aggressive`,
  `distracted`, `cyclist`, `motorcyclist`, `pedestrian`, `red_light`, `school_child`,
  `heavy_truck`, `older_adult`.
- **Geographic fields:** `longitude`, `latitude`, `geometry` (WKT/GeoJSON point), `wardname`,
  `division` (police division), `neighbourhood` (name, matches the 158-area Neighbourhoods
  dataset).
- **Temporal fields:** `accdate` (full timestamp — supports hour/weekday/month/season/year
  analysis directly).
- **Potential primary key:** None at file grain — the file is **person-involved-per-collision**
  grain (one `collision_id` repeats once per person/vehicle role in the event), so the natural
  key is composite: `(collision_id, veh_no, per_no)`. A collision-level grain requires
  `DISTINCT collision_id` aggregation.
- **Potential join keys:** `neighbourhood` → Neighbourhoods dataset; `wardname` → Ward
  boundaries; `latitude`/`longitude` → nearest-intersection spatial join to Traffic Signals /
  Traffic Volumes; `stname1`/`stname2` → fuzzy text join to intersection-based datasets (no
  clean numeric key exists between KSI and the signals/volumes datasets — this is documented
  as a data-quality risk below).
- **Data quality concerns:** (1) grain ambiguity — must decide collision-level vs.
  person-level analysis per query; (2) no shared numeric location key with other Transportation
  Services datasets (`px` intersection IDs are absent from KSI — only free-text street names
  and lat/long); (3) recent months under-reported due to verification lag; (4) some
  categorical fields (`vehtype`, `manoeuvre`, `drivact`) have inconsistent free-text-like
  category values across years as police reporting forms evolved; (5) KSI is a **severity-
  filtered** dataset — it excludes minor/no-injury collisions, so it cannot answer "total
  collision volume," only "how often are people killed or seriously hurt."
- **License/reuse:** Open Government Licence – Toronto (portal-wide licence; not set at the
  package level in the API, confirmed via the catalogue's licence footer).
- **Why it is useful:** This is the single richest, best-documented, longest-running,
  daily-refreshed dataset for the project's core question (collision frequency, severity,
  timing, location). It has real lat/long, real timestamps, real severity classification, and
  road-user breakdowns (pedestrian/cyclist/motorcyclist/driver) — directly supports analytical
  questions 1–5 and 8–9 in the brief.
- **Verdict: Recommended — primary fact table (`fact_collisions`).**

---

### 2. Traffic Volumes – Multimodal Intersection Turning Movement Counts (TMC)

- **Official source URL:** https://open.toronto.ca/dataset/traffic-volumes-at-intersections-for-all-modes/
- **CKAN package id:** `traffic-volumes-at-intersections-for-all-modes`
- **Key resources:**
  - `tmc_most_recent_summary_data` — resource id `6afa3b1f-f6a5-4235-8bd6-7568411c19f4`
    (**6,378 records**, most recent count per intersection)
  - `tmc_summary_data` — resource id `1364bffa-29a3-4c39-af8a-925d8ca7bf1f` (all summarized
    counts, every intersection/date pair)
  - `tmc_raw_data_1980_1989` … `tmc_raw_data_2020_2029` — five decade-partitioned raw
    15-minute-interval files (large; not needed for Phase 1)
- **Description:** Ad-hoc Turning Movement Counts collected by Transportation Services at
  signalized and unsignalized intersections since 1984 — vehicle, truck, bus, bicycle, and
  pedestrian volumes by approach and turning movement.
- **File/API format:** CSV, XML, JSON; datastore-backed and queryable via API.
- **Approximate row count:** 6,378 (most-recent-per-intersection summary — the table used in
  this project). The full `tmc_summary_data` history and raw decade files are far larger and
  out of scope for Phase 1.
- **Historical date range:** 1984 to present (raw data); the summary table used here is one
  row per intersection reflecting its most recent count date.
- **Update frequency:** Last refreshed 2026-08-21 (rolling/ad-hoc — counts are collected
  intersection-by-intersection, not on a fixed citywide cadence).
- **Important columns:** `location_name`, `centreline_id`, `centreline_type`, `px`
  (intersection ID), `latest_count_date`, `count_duration`, `total_vehicle`, `total_bike`,
  `total_pedestrian`, `total_heavy_pct`, AM/PM peak volumes, and per-approach (N/E/S/W) vehicle
  and bike volumes.
- **Geographic fields:** `latitude`, `longitude`, `centreline_id`, `px`.
- **Temporal fields:** `latest_count_date`, `am_peak_start`, `pm_peak_start` (the historical
  `tmc_summary_data`/raw tables carry a date per count, enabling true time-series volume
  analysis in a later phase).
- **Potential primary key:** `px` (intersection ID) in the most-recent-summary table (one row
  per intersection); composite `(px, latest_count_date)` in the full history table.
- **Potential join keys:** `px` and `centreline_id` → Traffic Signals Tabular (`px` appears
  there too, per City of Toronto's shared intersection numbering); `centreline_id` → Toronto
  Centreline dataset (not ingested in Phase 1) for street-segment geometry.
- **Data quality concerns:** (1) counts are ad-hoc, not a continuous census — coverage is
  uneven across intersections and years, so citywide "total traffic" trends cannot be inferred,
  only intersection-level snapshots; (2) `px` is City-internal and not present in the KSI
  dataset, so collisions cannot be joined to exact traffic volume without a spatial
  (lat/long-proximity) join, which introduces matching-radius judgment calls; (3) turning
  movement counts pre-2000s use older collection methodology and sparser bicycle/pedestrian
  detail.
- **License/reuse:** Open Government Licence – Toronto.
- **Why it is useful:** Provides the "exposure" side of a safety analysis — collision counts
  alone can't say whether an intersection is dangerous or just busy. Volume data lets the
  project compute collision *rates* (collisions per 10,000 vehicle/bike/pedestrian movements),
  which is a materially stronger analytical result than raw counts.
- **Verdict: Recommended — secondary fact table (`fact_traffic_volume`), most-recent-summary
  grain for Phase 1; full time-series history flagged as a Phase 2 stretch goal.**

---

### 3. Traffic Signals Tabular

- **Official source URL:** https://open.toronto.ca/dataset/traffic-signals-tabular/
- **CKAN package id:** `traffic-signals-tabular`
- **Description:** Every traffic signal, pedestrian crossover, and traffic beacon location in
  Toronto, with operational metadata (control system type, accessibility/audible tone,
  pedestrian countdown timer, transit/fire/rail priority, activation date).
- **File/API format:** CSV, XLSX, SHP, GeoJSON, GPKG; three live datastore layers (`Traffic
  Signal`, `Pedestrian Crossover`, `Traffic Beacon`).
- **Approximate row count:** Not yet pulled precisely (city has ~2,300+ signals per the related
  Signal Timing dataset description); to be confirmed at ingestion time.
- **Historical date range:** Point-in-time current inventory (activation dates go back
  decades, but the table reflects the *current* signal network, not a historical log).
- **Update frequency:** Last refreshed 2026-08-22 (kept current).
- **Important columns:** signal type/control system, audible tone flag, pedestrian countdown
  flag, transit/fire/rail priority flags, activation date.
- **Geographic fields:** latitude/longitude, `px` (intersection ID — same ID space as the TMC
  dataset).
- **Temporal fields:** activation date only (not a time series).
- **Potential primary key:** `px`.
- **Potential join keys:** `px` → Traffic Volumes TMC dataset (confirmed shared ID scheme).
- **Data quality concerns:** current-state snapshot only — cannot reconstruct what the signal
  network looked like in, say, 2010, so it should not be used to explain collision trends over
  time, only to describe present-day intersection infrastructure.
- **License/reuse:** Open Government Licence – Toronto.
- **Why it is useful:** Supplies the missing `px` ↔ location bridge needed to connect the TMC
  volume dataset to real intersection identities/geometry, and adds infrastructure context
  (e.g., "does this high-collision intersection have a pedestrian countdown timer?").
- **Verdict: Recommended — dimension table (`dim_intersection`), used for ID resolution and
  infrastructure attributes, not as a fact/time-series source.**

---

### 4. Neighbourhoods

- **Official source URL:** https://open.toronto.ca/dataset/neighbourhoods/
- **CKAN package id:** `neighbourhoods`
- **Description:** Official boundaries for Toronto's 158 social-planning neighbourhoods, used
  citywide as the standard geographic unit for reporting.
- **File/API format:** CSV, SHP, GeoJSON, GPKG (EPSG:4326 and EPSG:2952).
- **Approximate row count:** 158 (one per neighbourhood — confirmed stable, boundaries change
  "very infrequently").
- **Historical date range:** Current boundary set (post-2021 update to 158 areas, previously
  140); a "historical 140" GeoJSON resource is also published for backward compatibility.
- **Update frequency:** Last refreshed 2026-02-20.
- **Important columns:** neighbourhood name, neighbourhood ID (`AREA_SHORT_CODE` /
  `AREA_NAME`, exact field names to confirm at ingestion), geometry.
- **Geographic fields:** polygon geometry, name.
- **Temporal fields:** none (static reference dimension).
- **Potential primary key:** neighbourhood ID/code.
- **Potential join keys:** neighbourhood name → KSI `neighbourhood` field (exact-text match
  expected but must be validated — City datasets have occasionally used slightly different
  neighbourhood-name spellings/casing across releases).
- **Data quality concerns:** name-matching to KSI's free-text `neighbourhood` column needs a
  validation pass (case, punctuation, renamed areas) before being trusted as a join key.
- **License/reuse:** Open Government Licence – Toronto.
- **Why it is useful:** Turns KSI's `neighbourhood` text field into a real dimension with
  stable IDs and polygon geometry, enabling neighbourhood-level rollups and (later) choropleth
  mapping in Power BI.
- **Verdict: Recommended — dimension table (`dim_neighbourhood`).**

---

## Investigated, not recommended

### 5. Traffic Volumes – Midblock Vehicle Speed, Volume and Classification Counts

- **URL:** https://open.toronto.ca/dataset/traffic-volumes-at-intersections-for-all-modes/ (sibling: midblock package)
- Speed/volume/vehicle-classification counts at road **segments** (not intersections) since
  1993, refreshed daily. Genuinely strong dataset (>30,000 historical counts).
- **Reason not recommended for Phase 1:** different grain (road segment vs. intersection) and
  a different ID space (`centreline_id`-only, no `px`) than the TMC/Signals pair already
  chosen. Adding it now would mean maintaining two parallel volume models before the core
  intersection-based model is proven out. **Flagged as a strong Phase 2 addition**, not
  excluded on quality grounds — only on scope grounds.

### 6. Road Restrictions

- **URL:** https://open.toronto.ca/dataset/road-restrictions/
- Described as a "live feed" of current closures/RESCU incidents, but the API's
  `last_refreshed` timestamp is **2022-08-04** — over three years stale despite the "live"
  framing.
- **Reason not recommended:** it is operationally a point-in-time snapshot with no historical
  archive, so it cannot support the project's time-series analytical questions, and its
  currency cannot be trusted for present-day use either. Not usable as a fact or dimension
  table without a separate scraping/archiving process, which is out of scope.

### 7. Cycling Network

- **URL:** https://open.toronto.ca/dataset/cycling-network/
- Current-state line geometry of Toronto's bike lanes/cycle tracks/trails, well maintained
  (refreshed 2026-08-10).
- **Reason not recommended for Phase 1:** it's an infrastructure snapshot with no reliable
  historical versioning in the API response (can't tell what existed in 2015 vs. 2026), so it
  can describe *today's* network but not explain collision trends *over time*. Also requires
  a line-to-point spatial join (nearest-cycling-infrastructure-to-collision) which is a
  meaningful scope increase. **Flagged as a Phase 2 spatial-overlay candidate** for a
  cyclist-safety deep dive, not core to the initial model.

### 8. Red Light Cameras / Red Light Camera Annual Charges

- **URL:** https://open.toronto.ca/dataset/red-light-cameras/
- Point locations of red-light camera intersections plus annual ticket-count summaries
  (2007–present).
- **Reason not recommended for Phase 1:** small, current-state location list with only
  annual-grain ticket totals (no daily/monthly detail), and no confirmed shared join key to
  KSI beyond an approximate location match. Adds enforcement context but not enough analytical
  depth to justify inclusion before the core model is built. Worth revisiting for the
  "recommendations" narrative in a later phase.

### 9. Automated Speed Enforcement (ASE) Locations / ASE Charges

- **URL:** https://open.toronto.ca/dataset/automated-speed-enforcement-locations/
- Monthly ASE ticket counts since July 2020 from ~150 mobile units in school Community Safety
  Zones.
- **Reason not recommended:** Ontario's provincial government banned automated speed cameras
  in November 2025 per the dataset's own notes — the program is winding down, so this dataset
  represents a closed, short (2020–2025), narrowly-scoped historical window rather than an
  ongoing signal. Not central enough to the mobility story to include now.

### 10. Travel Times – Bluetooth

- **URL:** https://open.toronto.ca/dataset/travel-times-bluetooth/ (and related King St.
  Pilot travel-time resources)
- Corridor travel-time data from Bluetooth/WiFi sensors.
- **Reason not recommended:** last refreshed **2019-07-23** — the general citywide Bluetooth
  program is stale/discontinued in the open data portal; only the narrow King Street Transit
  Pilot corridor still gets occasional updates (last 2026-02-20), and that's a single-street,
  single-project dataset, too narrow to generalize into a citywide mobility model.

### 11. Parking Tickets

- **URL:** https://open.toronto.ca/dataset/parking-tickets/
- ~2.8 million tickets/year since 2008, actively maintained (refreshed 2026-05-13).
- **Reason not recommended:** genuinely large and well-maintained, but it measures parking
  enforcement, not mobility/collision risk, and has no natural join key to the collision or
  traffic-volume datasets beyond coarse location. Including it would pull the project's scope
  toward a parking-enforcement story instead of the stated Vision-Zero/mobility-safety focus.
  Considered and set aside rather than overlooked.

### 12. Traffic Signal Vehicle and Pedestrian Volumes / Wellbeing Toronto – Transportation

- Both explicitly marked **Retired** in the CKAN metadata (last refreshed 2018-03-31 and
  2014-12-31 respectively) and superseded by the active TMC and KSI datasets used above.
  Excluded as stale duplicates of data already covered by recommended sources.

### 13. Traffic Cameras / Special-event datasets (e.g., Church St. Pedestrianization Pilot)

- Traffic Cameras is a live-updated location-only list (no analytical/time dimension). No
  general citywide "special events / road closures for events" dataset was found on the
  portal — the closest match, the Church Street Pedestrianization Pilot public-life study, is
  a one-off consultant study for a single street, not a generalizable events dataset. Neither
  is recommended; the "events" data category from the research brief does not have a strong
  City of Toronto open-data match at this time.

---

## Recommended Dataset Architecture

**Use four datasets for the Phase 1 build:**

1. **Motor Vehicle Collisions (KSI)** — `fact_collisions` (person-involved-in-collision grain)
2. **Traffic Volumes – Multimodal TMC**, most-recent-summary resource — `fact_traffic_volume`
   (intersection grain)
3. **Traffic Signals Tabular** — `dim_intersection` (bridges `px` between the two fact
   sources, adds signal infrastructure attributes)
4. **Neighbourhoods** — `dim_neighbourhood` (adds stable geography + polygons on top of KSI's
   free-text neighbourhood names)

Plus one derived dimension built in SQL, not sourced externally:

5. **`dim_date`** — generated calendar table (date, year, month, month name, quarter, weekday,
   weekday name, is_weekend, season), driven off the min/max of `accdate` in `fact_collisions`.

### Why this combination and not more

- **KSI is the spine.** It is the only dataset with the full package the project needs in one
  place: real timestamps, real lat/long, severity, and road-user breakdowns, at a daily refresh
  cadence, going back to 2006. Every analytical question in the brief (1–9) can be answered
  from KSI alone if nothing else were added.
- **TMC + Signals together solve one specific, real gap**: KSI has no traffic-volume context,
  so "which intersection is dangerous" and "which intersection is just busy" are
  indistinguishable without it. TMC supplies volumes; Signals supplies the `px` key that makes
  TMC's intersection identity concrete and connects it to real-world infrastructure
  attributes. Neither is useful without the other for this purpose — TMC's `px` is meaningless
  without Signals' location/name context, and Signals alone has no volume or safety data.
- **Neighbourhoods** is a low-cost, low-risk addition — 158 static rows — that upgrades KSI's
  free-text neighbourhood field into a real, joinable, mappable dimension, which materially
  improves the Power BI stretch goal (choropleth by neighbourhood) for very little modeling
  cost.
- **Everything else was excluded on a specific, stated reason** (stale/retired, wrong grain
  for Phase 1, no reliable join key, or off-topic vs. the stated mobility-safety focus) — not
  because it was uninteresting. Midblock volumes, Cycling Network, and Red Light Cameras are
  explicitly flagged as strong **Phase 2** candidates once the core star schema is proven, so
  the door is intentionally left open rather than closed.

### Known join-key risk that needs an explicit decision in Phase 1 design

KSI does **not** carry the City's `px` intersection ID — it only has free-text street names
and lat/long. Connecting a given collision to a specific `px` (and therefore to TMC volume /
Signals infrastructure data) requires either:
  - a **nearest-neighbor spatial join** on lat/long within some radius (e.g., 30–50 meters), or
  - a **fuzzy text match** on `stname1`/`stname2` against the Signals dataset's intersection
    naming.

This is a real, non-trivial data-modeling decision (not a simple `JOIN ON key = key`) and is
exactly the kind of design choice the workflow calls for pausing on before Phase 1 begins — see
`docs/DECISION_LOG.md`.
