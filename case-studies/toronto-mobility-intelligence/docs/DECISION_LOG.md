# Decision Log

Chronological record of major decisions made on Toronto Mobility Intelligence. Routine
implementation choices are not logged here — only decisions that shape scope, architecture, or
analytical direction.

---

## 2026-08-22 — Phase 0: Dataset selection

**Decision:** Build the project on four City of Toronto Open Data sources:

- Motor Vehicle Collisions Involving Killed or Seriously Injured Persons (KSI) — primary fact
- Traffic Volumes – Multimodal Intersection Turning Movement Counts (TMC), most-recent-summary
  resource — secondary fact
- Traffic Signals Tabular — intersection dimension / `px` ID bridge
- Neighbourhoods — geography dimension

Full evaluation of 13 investigated datasets, including why each excluded dataset was rejected,
is in [`DATASET_RESEARCH.md`](DATASET_RESEARCH.md).

**Alternatives considered:**

- *All collisions (not just KSI)* — no citywide "all severities" collision dataset is
  published by the City; KSI (severity-filtered) is the only official collision-level source
  available. Accepted as a known scope limitation, not a choice among equals.
- *Midblock traffic volumes instead of / in addition to TMC* — segment-grain, no `px` key,
  would require a second parallel volume model before the intersection-based one is proven.
  Deferred to Phase 2.
- *Cycling Network as a core table* — current-state-only geometry (no historical versioning
  in the API), would need a line-to-point spatial join. Deferred to Phase 2 as a cyclist-safety
  overlay.
- *Road Restrictions* — API `last_refreshed` is 2022-08-04 despite being described as a "live
  feed"; rejected as unusable for a time-series project.
- *Parking Tickets, Travel Times (Bluetooth), Red Light/ASE cameras* — each considered and
  rejected for reasons specific to that dataset (off-topic, stale, or too narrow); documented
  individually in `DATASET_RESEARCH.md`.

**Rationale:** KSI is the only dataset with the complete package the analytical questions need
in one place (timestamp, lat/long, severity, road-user type) at a daily-refreshed, 20-year
cadence. TMC + Signals were added specifically to give collision counts a volume/exposure
baseline (rate, not just raw count) and to establish a real intersection identity (`px`) that
KSI itself lacks. Neighbourhoods was added because it is a near-zero-cost upgrade (158 static
rows) from a free-text field to a real joinable/mappable dimension.

**Status:** **Approved by user, 2026-08-22.** Phase 1 (data model design) proceeded on this
architecture.

---

## 2026-08-22 — Open question: KSI ↔ intersection join strategy

**Context:** KSI carries only free-text street names and lat/long — it has no `px`
(intersection ID) field, while TMC and Traffic Signals both use `px`. To compute
volume-normalized collision rates by intersection, collisions must be matched to a `px` some
way.

**Options identified (not yet decided):**

1. **Spatial nearest-neighbor join** — match each collision's lat/long to the nearest Traffic
   Signals `px` point within a fixed radius (e.g., 30–50m). Precise, but radius choice is a
   judgment call and some collisions (midblock, not at a signal) will legitimately have no
   match.
2. **Fuzzy text join** — match KSI's `stname1`/`stname2` pair against Signals' intersection
   naming. Avoids needing PostGIS/geometry functions early, but street-name text is messier
   (abbreviations, "St" vs "Street," ordering of the two street names) and will need a
   normalization pass.
3. **Do not force a join** — keep `fact_collisions` and `fact_traffic_volume` as siblings
   under `dim_neighbourhood` only (coarser grain), and treat true intersection-level
   volume-normalized rates as an optional, best-effort enrichment rather than a load-bearing
   part of the core model.

**Status:** Not decided. This is exactly the kind of architectural choice that should be
confirmed before Phase 1 schema design, since it affects whether PostGIS is needed, what the
grain of `fact_traffic_volume` joins look like, and how confidently "collision rate per
intersection" claims can be made in the final analysis.

**Decision (2026-08-22, user-approved):** Option 1 — spatial nearest-neighbor join. Each
collision's `(latitude, longitude)` will be matched to the nearest Traffic Signals `px` point
within a fixed search radius (exact radius, e.g. 30–50m, to be tuned during Phase 1 schema
design against real data — collisions with no `px` within radius are legitimately midblock and
should surface as unmatched, not be forced to a wrong intersection).

**Stack implication:** this requires the **PostGIS** extension on top of plain PostgreSQL
(`CREATE EXTENSION postgis;`) for `ST_DWithin`/`ST_Distance`/nearest-neighbor operators. This is
an addition to the technical stack beyond what was listed at project kickoff (PostgreSQL, SQL,
Python, pandas, Git) — flagged here explicitly since it's a direct consequence of this decision,
not scope creep. PostGIS is standard, well-supported, and required for correct results.

**Radius resolved (2026-08-22, Phase 1):** the "e.g. 30-50m" placeholder above was not used.
The actual distance distribution was computed by pulling all 7,586 geocoded KSI collisions and
all 2,550 Traffic Signal points and calculating every pairwise nearest-neighbor distance. The
result is bimodal with a sharp elbow at ~10-15m (a dense cluster of collisions sit within 0-10m
of a signal — essentially coincident — then the distribution drops sharply and becomes a flat,
featureless tail out past 500m with no second cluster). **20 meters** was chosen as the match
radius: it captures the dense near-zero cluster (44.7% cumulative) plus a small allowance for
GPS/geocoding jitter, without reaching into the flat background tail where a match would likely
be to the *wrong* nearby intersection. This was cross-validated against KSI's own
`accloc`/`traffictl` fields (independent of coordinates): `accloc = 'At Intersection'` is 41.6%
of collisions and `traffictl = 'Traffic Signal'` is 40.8% — both land within a point of the
41.5% found purely from the 0-10m coordinate cluster, confirming the spatial pattern reflects
something real rather than geocoding noise. Full analysis in `DATA_MODEL.md` §2.

**Expected consequence, stated up front:** ~44.7% of KSI collisions (≈3,390 of 7,586) are
expected to match an intersection under this radius; the remaining ~55.3% will be
`unmatched_outside_radius` by design — these are genuinely midblock or non-signalized-
intersection collisions (Traffic Signals only covers 2,550 signals citywide, not every
intersection), not a modeling failure to be fixed by loosening the radius.

---

## 2026-08-22 — Phase 1: Historical collision-rate metric rejected; cross-sectional metric adopted instead

**Context:** the brief required investigating whether TMC traffic-volume data can serve as a
valid exposure denominator for a year-by-year KSI collision rate before any such metric is
designed.

**Investigation:** pulled the full TMC count history (30,831 count events, 1984-2026, 2,661
distinct intersections). Findings: counts are ad hoc, not a continuous census — average ~11.6
counts per intersection across 42 years (~1 recount every 3.6 years), with 134 intersections
counted only once ever, and irregular gaps (e.g. 1986 → 1995 → 2003 → 2016 → 2022) rather than
any fixed schedule. Full detail in `DATA_MODEL.md` §1.

**Decision:** a true `collisions_in_year_Y / volume_in_year_Y` rate is **not built**. Given the
average 3.6-year recount gap, the overwhelming majority of intersection-year combinations in
the 2006-2026 KSI window have no same-year volume observation — computing the rate would mean
either leaving it undefined for most rows, or carrying forward a stale count as a stand-in,
which would manufacture false precision and could show an "increase in collision rate" that is
actually just an artifact of an old, unchanging denominator.

**Adopted instead:** a three-tier approach —
1. Pure collision-frequency/severity/temporal analysis directly from `fact_collisions`, fully
   valid across 2006-2026, no volume data involved — this is the project's primary analytical
   layer (`ANALYTICAL_QUESTIONS.md` sections A-C).
2. A clearly-labeled **cross-sectional** relative-risk score (`collisions_per_10k_movements`,
   `ANALYTICAL_QUESTIONS.md` §E1) using each intersection's single most-recent volume count as
   a "current exposure" snapshot — valid only for comparing intersections to each other as of
   now, never as a trend over time, and always reported alongside `count_recency_years` since
   ~15% of locations haven't been recounted since before 2010.
3. A documented (not built) Phase 2 idea: manual before/after case studies for the subset of
   intersections with multi-era count coverage.

**Rationale:** this directly follows the brief's instruction — "do not force a historical
collision-rate calculation if the denominator is temporally incompatible" — and keeps the
project's headline metrics resting on data that actually supports them.

---

## 2026-08-22/23 — Phase 2: pipeline implementation, findings against Phase 1's predictions

**Outcome: every empirical figure from Phase 1's research reproduced almost exactly once the
real pipeline ran against live source data.** Source row counts matched Phase 0/1 exactly
(KSI 20,691, TMC 30,831, Signals 2,550, Neighbourhoods 158 — no schema or volume drift since
research). The spatial match rate at the approved 20m radius came out to **44.71% matched
(3,392 of 7,587 distinct collisions)**, against Phase 1's predicted ~44.7% — confirms the
radius decision was sound and not overfit to a smaller/different sample. Full detail in
`docs/DATA_MODEL.md`.

**Resolved: the neighbourhood-name join, flagged in Phase 1 as unvalidated, is a clean
match.** 100% of the 20,540 collision-person rows with a non-blank source `neighbourhood`
value resolved to a real `dim_neighbourhood.area_name` on a case/whitespace-insensitive exact
match — the 151 "unmatched" rows all had a genuinely blank source value, not a spelling/format
mismatch. No fuzzy matching was needed.

**Correction: `acclass` values are `'Fatal Injury'` / `'Non-Fatal Injury'` /
`'Property Damage Only'`, not the shorthand `'Fatal'` / `'Property Damage'` used in earlier
drafts of `DATA_MODEL.md` and `ANALYTICAL_QUESTIONS.md`.** Caught by building the real
pipeline against real data rather than assuming from the dataset description; both docs were
corrected in place rather than left wrong.

**Decision: `fact_traffic_volume` is scoped to `px IS NOT NULL` rows only, exactly as
`DATA_MODEL.md` §3.4 specified.** Of 30,831 clean TMC rows, 24,067 carry a px; 9 of those are
duplicate `(px, count_date)` pairs (known from Phase 1 research) and are resolved
deterministically by keeping the lowest `clean.traffic_volume.id` — both the duplicates and
the 6,764 excluded midblock (`px IS NULL`) rows are logged to `clean.dq_flags` with a specific
reason code, not silently dropped. Final `fact_traffic_volume` row count: 24,058.

**Decision: line-ending normalization added to the download step.** The City's CKAN datastore
dump endpoint mixes CRLF (header row) and bare LF (data rows) within a single CSV file, which
PostgreSQL's `COPY ... CSV` rejects outright ("unquoted newline found in data"). Not a data
quality issue with the source content itself, just a transport quirk — `etl/download/download_datasets.py`
normalizes all line endings to LF before writing the file to disk, and this happens before the
sha256/manifest is computed, so the recorded checksum reflects exactly what gets loaded.

**Decision: defensive SQL cast functions (`clean.safe_int`, `safe_timestamp`, `safe_bool`,
`safe_toronto_point`, `safe_geom_from_geojson`, etc.) instead of relying on plain `::type`
casts in the staging→clean transforms.** A single malformed value under a plain cast aborts
the entire batch `INSERT`; these wrap the cast in `EXCEPTION WHEN OTHERS THEN RETURN NULL`, so
a bad value in one row degrades gracefully into a per-row reject-or-flag decision (handled
explicitly by each transform) instead of failing the whole load. In this run they made no
practical difference — the real source data had zero hard-reject cases across all four
datasets — but the mechanism is real and covered by `tests/test_cast_helpers.py`, not just
theoretical.

**Reproducibility verified directly, not assumed:** the full pipeline (`make reset && make up
&& make schema && make ingest && make transform && make analytics && make validate && make
test`) was run twice against a completely fresh database volume during this phase, and
produced byte-identical row counts, the same sha256 checksums on the downloaded source files,
and the same 44.71% spatial match rate both times.

---

## 2026-08-23 — Phase 3: `sql/analytics/` renamed to `sql/warehouse/`

**Decision:** the Phase 2 warehouse-build scripts (`010_dim_date.sql` … `060_bridge_collision_intersection.sql`)
moved from `sql/analytics/` to `sql/warehouse/`, freeing up `sql/analytics/` for the curated
query/view layer the Phase 3 brief explicitly requested at that path
(`sql/analytics/01_temporal/` … `07_quality/`). The Makefile's `analytics` target was renamed
`warehouse`; a new `views` target runs the curated layer. **The Postgres schema is still named
`analytics`** and is entirely unaffected — this was a repository file-layout decision, not a
database change.

**Alternatives considered:** keeping the flat build scripts where they were and nesting the new
`01_temporal/` etc. subdirectories alongside them inside the same `sql/analytics/` directory.
Rejected: mixing "scripts that mutate/rebuild tables" with "read-only queries that answer
analytical questions" in one directory would be confusing for a reviewer scanning the repo
tree, and the rename is a fully reversible, low-risk change.

---

## 2026-08-23 — Phase 3: confirmed `pedestrian`/`cyclist`/`motorcyclist` flags are collision-level, not person-level

**Finding:** while building `03_road_users/010_road_user_involvement_trend.sql`, direct
inspection showed `road_user='driver'` rows frequently carry `pedestrian = true` — proof the
flag describes the *collision event* ("this collision involved a pedestrian"), copied onto
every person-row of that event including drivers and passengers, not the specific person on
that row. Verified with zero exceptions: no `collision_id` in the dataset has inconsistent
values for these flags across its own person-rows.

**Decision:** every query in `sql/analytics/` that needs an actual person-level count (e.g.
"how many pedestrians were involved") uses `road_user = '<type>'`, never
`COUNT(*) FILTER (WHERE <flag>)`. Queries that need collision-level involvement (e.g. "how many
collisions involved a pedestrian") correctly use `COUNT(DISTINCT collision_id) WHERE <flag>`.
`docs/DATA_MODEL.md`'s `fact_collisions` column reference was corrected in place to document
this distinction directly on the affected columns, rather than leaving it as a Phase 3-only
footnote.

**Rationale:** this is exactly the "distinguish collision involving pedestrian from number of
pedestrians injured" requirement from the Phase 3 brief — getting the wrong one would have
overcounted pedestrian involvement by roughly 2.3x (8,445 flag-true person-rows vs. 3,650 actual
pedestrian person-records) in any query that made this mistake.

---

## 2026-08-23 — Phase 3: questions explicitly not built, and why

**Decision:** D2 (infrastructure features vs. collision counts) was dropped, not deferred by
oversight. Its own entry in `ANALYTICAL_QUESTIONS.md` already flags a strong reverse-causation
risk — safety infrastructure is often installed *because* a location already had a collision
history, which would bias a naive comparison toward making safety features look associated with
*higher* risk. Building it would have produced a number shaped like a finding that isn't one,
which the Phase 3 brief explicitly warned against ("if a metric is not defensible, do not
calculate it"). E2 (bike-volume quartiles vs. cyclist involvement) and E3 (zero-collision
intersection screening) were left unbuilt to keep this phase to a curated ~14 queries rather
than exhaustively covering the question bank — both remain valid Phase 4 candidates. F3
(neighbourhood KSI vs. demographic profile) stays unanswerable, as already noted at the dataset
level: Neighbourhood Profiles was never one of the four datasets approved for this project.

---

## 2026-08-23 — Phase 3: `road_class` completeness drop in 2024-2026 flagged, not investigated further

**Finding:** `07_quality/020_temporal_and_category_drift.sql` shows `road_class` NULL rate
jumping from under 3% (every year 2013-2023) to 28.38% (2024), 10.20% (2025), and 62.20% (2026,
partial year).

**Decision:** documented as a monitoring flag in `docs/ANALYTICAL_FINDINGS.md`, explicitly
**not** treated as a confirmed data-quality defect. It coincides closely with KSI's documented
verification lag (`docs/DATASET_RESEARCH.md`: fatalities 1-2 weeks, serious injuries 2-3
months to fully process) — the most recent records may simply be mid-pipeline at the City, not
mis-collected. Confirming this requires re-running `make ingest` at a later date and checking
whether the 2024/2025 NULL rate falls — logged as a concrete follow-up rather than acted on
now, since the project has no way to validate this against a single snapshot.

---

## 2026-08-23 — Phase 4: dashboard designed before building, per explicit instruction

**Decision:** `docs/POWER_BI_SPEC.md` and `docs/DASHBOARD_STORY.md` were written as design
specifications; no `.pbix` file was created. Six additive SQL changes (below) were made to
close specific gaps found while designing the 3-page dashboard, but no Power BI file, no
dashboard mockup, and no boundary-file conversion (§9.2 of the spec) were built — those are
explicitly Phase 5 work, pending review of this specification.

**Alternatives considered for "SQL-view proposals":** the brief's own wording ("propose the
smallest SQL change") left room to interpret this as documentation-only (write the proposed
view definitions in the spec, don't apply them) versus actually building and testing them.
**Decision: build and test them now.** Rationale: these are ordinary, low-risk, additive SQL
changes squarely inside the already-approved `analytics` schema and `sql/analytics/` layer (not
Power BI, not the warehouse) — the brief's own architecture principle ("if Power BI would
require substantial transformations that belong in SQL, create a new SQL view instead")
reads as an instruction to act, not just note the gap. Building them now, with tests, means
Phase 5 starts from proven-correct views instead of discovering the same six gaps mid-build.

**The six SQL changes**, all additive (new columns appended at the end of existing views, or
entirely new views — no existing Phase 3 column renamed, removed, or reordered; original
curated Phase 3 query files left untouched):

1. `v_neighbourhood_ksi` += `pedestrian_collision_count`, `cyclist_collision_count`
2. `v_intersection_risk` += `latitude`, `longitude`
3. `v_road_user_involvement` += `ped_fatal_collision_count`, `cyclist_fatal_collision_count`,
   `motorcyclist_fatal_collision_count`
4. `v_collision_hour_weekday` (new) — full 168-cell grid, for a heatmap visual
5. `v_collision_seasonal_pattern` (new) — view version of an existing Phase 3 query
6. `v_collision_monthly_pattern` (new) — a genuinely new grain (month), not built in Phase 3

**Bug caught during implementation:** the first attempt at changes 1–3 inserted new columns in
the *middle* of each view's column list (grouped next to the related existing columns, for
readability). PostgreSQL's `CREATE OR REPLACE VIEW` requires existing columns to keep their
exact ordinal position — this failed with `cannot change name of view column`. Fixed by moving
all new columns to the end of each SELECT list. Left as a visible lesson in each file's header
comment rather than silently corrected, since the same constraint will apply to any future view
extension in this project.

**Global filter design — a scope limitation surfaced, not hidden:** the Year slicer specified
in `POWER_BI_SPEC.md` §6.1 only filters `v_annual_ksi` and `v_road_user_involvement`, because no
other view carries a `year` column. This was a deliberate Phase 3 design choice (fine-grained
views like `v_intersection_risk` and `v_collision_hour_weekday` are all-time aggregates
specifically to avoid statistically thin per-year splits at fine grains), and Phase 4 chose to
document this as an explicit interaction limitation on the dashboard rather than silently build
year-sliceable versions of every view, which would reopen the small-sample-noise problem each of
those views was originally designed to avoid. Flagged in the spec as a legitimate future
enhancement if a reviewer specifically wants it, not built speculatively now.

**Two filters deliberately not built:** a global Severity slicer and a global Road-user-type
slicer, both because the aggregated views this dashboard consumes have no row-level category
column left to filter by — the brief's own instruction ("do not create filters that do not have
analytical value") was read literally here rather than adding slicers for the sake of a
complete-looking filter panel.

---

## 2026-08-23 — Phase 5: Power BI Desktop is unavailable on this machine; user chose PBIP + HTML prototype over GUI automation

**Context:** Phase 5 asked for an implemented 4-page Power BI dashboard. Power BI Desktop is
Windows-only. This machine is a Mac; the only Power BI Desktop install found is inside a
Parallels Desktop Windows 11 VM.

**Decision (user-approved via AskUserQuestion):** build (1) a real Power BI Project — TMDL
semantic model + PBIR report definition, the modern git-friendly text-based format Power BI
Desktop natively opens — and (2) a live interactive HTML prototype with real embedded data, for
design review without needing Power BI Desktop at all. Explicitly **not** chosen: driving Power
BI Desktop end-to-end via screen automation inside the VM (many rounds of brittle
screenshot/click cycles, plus the VM would need network access to the Postgres container on the
Mac host).

**What happened when the VM was tried anyway, as a verification-only step (not primary
construction):** `prlctl start "Windows 11"` failed — the Parallels Desktop license has
expired. This is not something fixable from this session; renewing it is on the user. The
practical consequence: the PBIP project's report layer (35 visuals across 4 pages) is
**structurally validated** (every visual's field binding, both relationships, and every
`model.tmdl` table reference cross-checked against the actual semantic model — 0 errors) but
was **never opened in a real Power BI Desktop**. This is stated plainly in `powerbi/README.md`'s
confidence table rather than implied to be fully verified.

---

## 2026-08-23 — Phase 5: three real gaps found by actually building the DAX/PBIR, not by re-reading the Phase 4 spec

Building the semantic model surfaced three places where the approved Phase 4 spec's plan didn't
actually work once implemented — each is a deviation from the letter of `docs/POWER_BI_SPEC.md`,
made because building the real thing is a stronger test than reviewing the plan for it, and each
is fixed with the smallest possible change rather than reworking the design:

1. **Page 3's "vehicle occupants only" severity category cannot be derived from
   `v_road_user_involvement`, contrary to `POWER_BI_SPEC.md` §4.5's plan.** That view has no
   such column, and it can't be computed from the existing per-type columns either, because
   pedestrian/cyclist/motorcyclist collisions overlap (a collision can involve more than one
   type), so `total − ped − cyclist − motorcyclist` would double-subtract the overlap. **Fix:**
   promoted the existing, already-tested `02_severity/010_severity_by_road_user_type.sql` query
   to a real view (`analytics.v_severity_by_road_user_type`,
   `sql/analytics/02_severity/030_v_severity_by_road_user_type.sql`) and imported it as a 12th
   table. This is exactly the brief's own escape hatch ("if Power BI would require substantial
   transformations that belong in SQL, create a new SQL view instead") — the alternative
   (dropping the vehicle-occupants-only category from the dashboard) would have narrowed the
   analytical story to work around an implementation inconvenience, which the brief also
   explicitly prohibits ("do not silently change the analytical story").
2. **`staging.ingestion_log` was required by `POWER_BI_SPEC.md` §8 (the Page 4 "data as of"
   table) but missing from its own §1.1 import list.** An internal inconsistency in the Phase 4
   spec document itself, not a data problem. **Fix:** added as the model's 13th (12th
   analytics + this one staging) imported table — it's the only table sourced from `staging`
   rather than `analytics`, which the TMDL generator handles via an explicit per-table schema
   lookup, not a special case bolted on afterward.
3. **`dim_date`, imported per the approved spec as "the official Date table," has no
   relationship to anything in the current model and is therefore currently inert.** Every
   imported view is pre-aggregated in SQL (by year, month, season, hour, neighbourhood,
   intersection) — none carries a row-level date column to relate `dim_date` to. Not fixed
   (nothing to fix — this isn't a bug, `dim_date` just has no current job), but called out
   explicitly in `powerbi/BUILD_GUIDE.md` and `powerbi/README.md` rather than left for a
   reviewer to discover and wonder whether it was an oversight. It's imported and ready for a
   future daily-grain view, not decorative.

**Also corrected in passing:** `docs/ANALYTICAL_FINDINGS.md`, `docs/DASHBOARD_STORY.md`, and
`README.md` all cited West Humber-Clairville's density rank as "#120 of ~148" — the "~148" was
an unchecked estimate from Phase 4. Re-querying `analytics.v_neighbourhood_ksi` during Phase 5
confirmed all 158 neighbourhoods have ≥1 KSI collision and appear in the view (the inner join
never silently drops empty ones) — corrected to the exact figure, "#120 of 158," in all three
files.

---

## 2026-08-23 — Phase 5: map visuals and the heatmap matrix built as ranked-table placeholders, not attempted as hand-authored map/matrix JSON

**Decision:** every KPI card, line chart, bar chart, table, and text panel across all 4 pages
(32 of 35 visuals) is real, schema-valid PBIR JSON with correct field bindings. The 2
geography-dependent visuals (neighbourhood choropleth, intersection bubble map) and the Page 3
heatmap are represented as ranked/plain data tables instead, with exact manual-conversion steps
in `powerbi/BUILD_GUIDE.md`.

**Rationale, by visual:**
- **Neighbourhood Shape Map** — structurally cannot be made functional by any JSON, correct or
  not: a Shape Map's boundary file (TopoJSON, keyed to `area_name`) is an external asset that
  must be uploaded interactively in Power BI Desktop. This was already known and documented as
  a manual one-time step in `docs/POWER_BI_SPEC.md` §9.2 before Phase 5 began, not a new finding.
- **Intersection bubble map** — the data is fully ready (`latitude`/`longitude` were added to
  `v_intersection_risk` in Phase 4 for exactly this purpose) and the core Map visual doesn't
  need an external asset, but its exact field-well JSON shape was assessed as too
  version-sensitive to hand-author with confidence and no way to verify by opening Desktop
  (previous entry). Risking a malformed visual.json here would have been worse than a clearly
  labeled placeholder with a 30-second documented fix.
- **Page 3 heatmap** — same reasoning as the bubble map: the Matrix visual's conditional
  background-color formatting is an interactive Format-pane feature, not naturally expressed as
  static field bindings alone.

**What this means concretely:** the PBIP, opened as-is, shows real numbers everywhere
immediately, including at the exact table/chart the map or heatmap would occupy — nothing is
silently broken or blank, and `powerbi/README.md`'s confidence table states this plainly rather
than presenting the placeholder tables as if they were the final design.
