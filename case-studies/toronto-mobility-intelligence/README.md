# Toronto Mobility Intelligence

A reproducible PostgreSQL + PostGIS analytics platform turning 20 years of Toronto's official collision data into public-sector-ready findings — from raw Open Data to a Power BI dashboard, with every claim traceable back to a SQL query.

## Overview

Toronto's Killed-or-Seriously-Injured (KSI) collision data can show *where* severe collisions occurred, but a raw collision count on its own doesn't tell you where risk is actually concentrated — a large, high-traffic neighbourhood will rack up more collisions than a small one almost by construction, independent of how dangerous it actually is. The analytical goal of this project was to build a data platform that could answer *what, where, when,* and *who* for Toronto's mobility-safety data honestly: normalizing raw counts where a fair denominator exists, being explicit about where it doesn't, and never overstating what the data can support.

## What I Built

```
Toronto Open Data (CKAN API)
   → PostgreSQL + PostGIS (staging → clean → analytics)
   → Python ETL with schema-drift detection and full data-quality validation
   → 20-meter spatial nearest-neighbor matching (collision → intersection)
   → 19 curated analytical SQL views/queries
   → Power BI (PBIP/TMDL project) + an interactive HTML dashboard prototype
```

Four official City of Toronto Open Data datasets — Motor Vehicle Collisions (KSI), Traffic Volumes (TMC), Traffic Signals, and Neighbourhoods — flow through a three-layer PostgreSQL warehouse (`staging` → `clean` → `analytics`) into a documented star schema, then into a curated SQL analytics layer that a 4-page Power BI dashboard consumes directly. No step skips the layer below it: the dashboard never touches raw data, and no business logic is duplicated in DAX that isn't already correct in SQL.

## Key Findings

- **Fatal share of KSI collisions has risen even as raw collision counts have fallen.** Under 12% of KSI collisions were fatal in 2006–2012; that rose into a 13–22% range for nearly every year from 2013 onward, peaking at 21.48% in 2021 — two different trends moving in different directions.
- **Pedestrians and cyclists are the majority of KSI collisions in every single year, 2006–2026** — never below 49%, as high as 64% — despite being a minority of total road users citywide.
- **Winter has the fewest KSI collisions of any season, but the highest fatal share** (15.00%, vs. 13–14% for the other three seasons) — fewer collisions overall, but disproportionately severe when they occur.
- **Raw collision counts are actively misleading without normalization.** West Humber-Clairville ranks #1 citywide by raw KSI count (235) but falls to #120 of 158 once normalized by land area — it's simply one of the city's largest neighbourhoods, not an outlier for risk.
- **Pedestrian-involved collisions are disproportionately fatal.** 17.54% of pedestrian-involved KSI collisions are fatal, against a 14.00% citywide average; cyclist-involved collisions are the *least* likely to be fatal, at 5.86%.

Full write-up, evidence, and stated limitations for every finding: [`docs/ANALYTICAL_FINDINGS.md`](docs/ANALYTICAL_FINDINGS.md).

## Technical Highlights

**Stack:** PostgreSQL · PostGIS · SQL · Python · Docker · Power BI · pytest

- 20,691 KSI collision records ingested and validated (2006–2026)
- 7,587 geocoded collisions evaluated for spatial matching against 2,550 signalized intersections
- 3,392 collisions matched within a 20m radius — a **44.71%** match rate, empirically derived (not guessed) from the real distance distribution and cross-validated against the source data's own location fields
- **91 passing automated tests** — cast-function edge cases, spatial-matching boundary conditions, deduplication, grain invariants, and KPI-to-SQL reconciliation
- Zero raw-CSV shortcuts: the dashboard, the analytics layer, and every test all read from the same governed PostgreSQL `analytics` schema

## Methodology

- **Three-layer warehouse:** `staging` (1:1 raw mirror) → `clean` (typed, deduplicated, geometry built, every excluded/flagged row logged with a reason — never silently dropped) → `analytics` (star schema: `fact_collisions`, `fact_traffic_volume`, `dim_intersection`, `dim_neighbourhood`, `dim_date`).
- **Spatial matching:** each collision is matched to the nearest signalized intersection within a 20-meter radius — a threshold derived from the actual distance distribution between geocoded collisions and signals (a sharp elbow at 10–15m), not an arbitrary round number, and cross-validated against the source data's own `traffictl`/`accloc` fields.
- **Collision ↔ intersection bridge table:** the match result lives in its own table (`bridge_collision_intersection`) rather than overwriting the collision record, preserving match status, distance, and the radius used for full auditability — unmatched collisions (the majority — mostly midblock or unsignalized locations) are kept, not discarded.
- **Analytical SQL layer:** 19 files across 7 topics (temporal, severity, road users, neighbourhoods, intersections, exposure, data quality), 9 of them persisted as PostgreSQL views — the same views Power BI imports directly.
- **Power BI:** a real Power BI Project (TMDL semantic model + PBIR report) with 18 DAX measures that mirror the SQL formulas exactly, so no metric is defined twice.

## Important Limitations

- **KSI is severity-filtered.** It captures only collisions where someone was killed or seriously injured — not all collisions — so every finding describes *severe outcomes*, not overall collision volume.
- **The traffic-exposure metric is cross-sectional, not a historical rate.** Toronto's traffic-volume counts aren't temporally aligned with collision history, so "collisions per 10,000 movements" compares intersections to each other *right now* — it is never a year-specific or trend statistic.
- **~55% of KSI collisions aren't matched to a signalized intersection.** This is expected (most are legitimately midblock or unsignalized), not a data-quality gap, but it means intersection-level findings cover a minority of the citywide total.
- **Raw neighbourhood collision counts are not risk.** Land area varies enormously across Toronto's 158 neighbourhoods; every raw-count claim in this project is paired with a density-normalized figure.
- **Recent `road_class` completeness has dropped** (from under 3% missing to 28–62% missing in 2024–2026) — most likely KSI's own documented verification lag rather than a pipeline defect, flagged for re-confirmation on a future data refresh rather than treated as settled.

Full methodology and all seven documented limitations: [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) and the dashboard's own Methodology page.

## Dashboard

A 4-page dashboard (Overview → Where → When & Who → Methodology) is implemented two ways, both consuming the same PostgreSQL analytics layer:

- **[`powerbi/`](powerbi/)** — a real, importable Power BI Project (PBIP/TMDL format).
- **[`dashboard/prototype.html`](dashboard/prototype.html)** — an interactive HTML build of all 4 pages with real embedded data; open directly in any browser, no server required.

## Reproduce

Requires Docker and Python 3 — no local PostgreSQL install needed.

```bash
cp .env.example .env
make up && make schema && make ingest && make transform && make warehouse && make views
make validate   # data-quality suite
make test        # 91 tests
```

Full command reference and the Power BI setup/build guide: [`docs/`](docs/) and [`powerbi/BUILD_GUIDE.md`](powerbi/BUILD_GUIDE.md).

## Project Structure

```
docs/            research, data model, analytical questions, findings, decision log
sql/             staging -> clean -> analytics DDL, ETL transformations, curated analytics
etl/             CKAN download + staging load, with schema-drift detection
tests/           pytest: pipeline, spatial matching, grain, KPI reconciliation (91 tests)
powerbi/         Power BI Project (PBIP/TMDL)
dashboard/       interactive HTML dashboard prototype
```

## Data Source

[City of Toronto Open Data Portal](https://open.toronto.ca/) — official CKAN API, four datasets:
[Motor Vehicle Collisions (KSI)](https://open.toronto.ca/dataset/motor-vehicle-collisions-involving-killed-or-seriously-injured-persons/),
[Traffic Volumes](https://open.toronto.ca/dataset/traffic-volumes-at-intersections-for-all-modes/),
[Traffic Signals Tabular](https://open.toronto.ca/dataset/traffic-signals-tabular/), and
[Neighbourhoods](https://open.toronto.ca/dataset/neighbourhoods/).

---

Back to [case studies](../) · [main portfolio](../../README.md).
