# Build Guide — Finishing the PBIP in Power BI Desktop

This project ships a real Power BI Project (PBIP/TMDL) — see [`README.md`](README.md) for what
that means and how confident each part is. This guide covers the handful of steps that
**cannot** be done via a static project file and need a few minutes in Power BI Desktop:
three visuals that are genuinely interactive-only (two maps + one heatmap conversion), plus
one one-click model setting.

Everything else — every KPI card, every line/bar chart, every table, all 18 DAX measures, both
relationships, all 4 pages — is already built and field-bound. This guide is the finishing
pass, not a from-scratch build.

## 1. Open the project

`File > Open > Browse` and select `TorontoMobilityIntelligence.pbip`. Power BI Desktop needs
**PBIP support** enabled: `File > Options and settings > Options > Preview features` → check
"Power BI Project (.pbip) save option" and "Store semantic model using TMDL format" if not
already on, then restart Desktop.

On first open, Desktop will ask for the PostgreSQL connection — enter your Postgres server
(`localhost:5433` for this project's local dev setup, from `docker-compose.yml`) and
credentials for the `tmi` user (`.env`). The server/database are model **parameters**
(`PGServer`, `PGDatabase`) — to point at a different environment later, use
`Transform Data > Edit Parameters`, not by editing any file.

If Desktop reports any issue opening the TMDL/PBIR files, that's useful signal, not a dead
end — these files were hand-authored against the documented schema and validated
structurally (every visual's field bindings were cross-checked against the semantic model —
see `docs/DECISION_LOG.md`'s Phase 5 entry), but were **not** verified by actually opening
Desktop (unavailable in the environment this was built in — same entry explains why). Desktop
is typically forgiving and can often repair minor issues on load; if something doesn't load,
the semantic model (Tables pane, relationships, measures) is the part to check first — it's
the part with the highest confidence behind it.

## 2. Mark `dim_date` as the Date Table (30 seconds)

Right-click `dim_date` in the Fields pane → **Mark as date table** → select `date_key`.
Not required for anything currently in the report (no imported view has row-level dates to
relate to it — every view is pre-aggregated in SQL, by design), but it's a standard, expected
setting on a table named `dim_date` and keeps the model conventional if a future daily-grain
view is added.

## 3. The two map visuals

Every other geographic visual in this report is a ranked table (a deliberate, documented
substitution — see `docs/DECISION_LOG.md`) because a real choropleth needs an externally
uploaded boundary file no JSON can supply. Converting each table to its intended map:

### 3a. Page 2 — Neighbourhood choropleth (replaces the "Raw Count vs. Density Ranking" table's map counterpart)

1. Insert a new **Shape Map** visual (Visualizations pane → Shape Map; enable it once via
   `File > Options > Preview features > Shape map visual` if not present).
2. **Location**: `v_neighbourhood_ksi[area_name]`. **Color saturation**: `v_neighbourhood_ksi[ksi_collision_count]`
   (or `ksi_density_per_km2` — consider a field parameter toggle between the two, per
   `docs/POWER_BI_SPEC.md` §3.1, so the raw-count/density contrast stays interactive).
3. Format pane → **Shape** → **Map settings** → upload a custom map. You need a **TopoJSON**
   file of Toronto's 158 neighbourhoods, keyed by `AREA_NAME`, matching `v_neighbourhood_ksi[area_name]`
   exactly. Generate it once from the Neighbourhoods GeoJSON (same CKAN resource documented in
   `docs/DATASET_RESEARCH.md`) via a converter such as mapshaper.org (`File > Import` the
   GeoJSON, `File > Export > TopoJSON`). This is a one-time asset — save it alongside this
   project once created.

### 3b. Page 1 & Page 2 — Intersection hotspot map

This one is simpler: `v_intersection_risk` already carries `latitude`/`longitude` (added
specifically for this in Phase 4 — see that phase's decision log entry).

1. Insert a **Map** (or ArcGIS Maps for Power BI) visual.
2. **Location** is not used; instead set **Latitude** = `v_intersection_risk[latitude]`,
   **Longitude** = `v_intersection_risk[longitude]`.
3. **Size** = `v_intersection_risk[matched_ksi_collision_count]`. **Legend/Color** =
   `v_intersection_risk[fatal_collision_count]` (use a sequential color scale, not a
   traffic-light red/green — see `docs/POWER_BI_SPEC.md` §6 for the color system).
4. No external asset needed — this one just requires interactively dragging the two coordinate
   fields into the Latitude/Longitude wells, which Power BI's field-binding JSON schema for
   this visual type was assessed as too version-sensitive to hand-author reliably (see
   `docs/DECISION_LOG.md`).

## 4. Page 3 — Hour × Weekday heatmap

The "Hour x Weekday KSI Collision Count" table on Page 3 has the right data (168 rows,
`day_name`, `hour_of_day`, `ksi_collision_count`) but a table doesn't read as a heatmap.
Convert it:

1. Insert a **Matrix** visual. **Rows** = `v_collision_hour_weekday[day_name]`. **Columns** =
   `v_collision_hour_weekday[hour_of_day]`. **Values** = `v_collision_hour_weekday[ksi_collision_count]`.
2. Format pane → **Cell elements** → turn on **Background color**, bind to the same value
   field, and set the color scale to a single-hue sequential ramp (light → dark blue — matches
   the HTML prototype's heatmap and `docs/POWER_BI_SPEC.md`'s "sequential, never diverging"
   rule). Turn off conditional formatting's default diverging (red/yellow/green) preset
   explicitly — it is the default and is the wrong choice here (no color-only meaning, and
   collision counts have no "good/bad" polarity to diverge around).
3. Sort rows by `day_of_week` (not alphabetically) via the matrix's sort control, so Monday
   leads and Sunday/Saturday sit at the ends as expected.

## 5. General polish (not required, but expected)

Every visual currently uses the default Power BI formatting beyond what's explicitly set (a
handful of title/legend/label toggles). The custom theme
(`TorontoMobilityIntelligence.Report/StaticResources/RegisteredResources/TorontoMobilityTheme.json`)
is wired into `report.json` and should apply automatically — spot-check it did (Format pane →
report-level → Themes). Visual sizing/positions were generated on a consistent grid but are a
starting point, not a final pixel-perfect layout — nudge as needed once real content is on
screen. Caption/warning textboxes (Page 2's exposure-metric callout, Page 4's warning box) are
plain textboxes — feel free to restyle, but do not shorten or remove their content; see
`docs/POWER_BI_SPEC.md` §8 for why each one is there.
