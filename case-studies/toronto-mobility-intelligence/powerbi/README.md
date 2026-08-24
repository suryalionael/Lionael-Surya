# Power BI Project

`TorontoMobilityIntelligence.pbip` — a real [Power BI Project (PBIP)](https://learn.microsoft.com/power-bi/developer/projects/projects-overview)
in the modern, git-friendly TMDL format. Open `TorontoMobilityIntelligence.pbip` in Power BI
Desktop (with the PBIP/TMDL preview features enabled — see [`BUILD_GUIDE.md`](BUILD_GUIDE.md)).

## What's here, and how confident each part is

| Part | Status | Confidence |
|---|---|---|
| `TorontoMobilityIntelligence.SemanticModel/` — 12 tables, 2 relationships, 18 DAX measures | Complete | High — every table's columns match the live PostgreSQL views exactly; every measure's formula mirrors an already-tested SQL formula from `sql/analytics/`; structurally validated (all 35 visual field-bindings, both relationships, and every `model.tmdl` reference resolve against the model — see `docs/DECISION_LOG.md`) |
| `TorontoMobilityIntelligence.Report/` — 4 pages, 35 visuals (KPI cards, line/bar charts, tables, methodology text) | Complete | High for field bindings and page structure; **not verified by opening Desktop** (unavailable in the build environment — a Parallels Windows VM with an expired license — see `docs/DECISION_LOG.md`) |
| 2 map visuals (neighbourhood choropleth, intersection bubble map) | Placeholder tables, not maps | Needs ~10 minutes in Desktop — see `BUILD_GUIDE.md` §3. Not a JSON-authoring gap: a Shape Map's boundary file is an external asset no static file can supply |
| Page 3 heatmap | Placeholder table, not a Matrix+conditional-formatting heatmap | Needs ~2 minutes in Desktop — see `BUILD_GUIDE.md` §4 |
| Custom theme | Wired in, not visually verified | `StaticResources/RegisteredResources/TorontoMobilityTheme.json` |

**Why a "confidence" table instead of just claiming it's done:** this project's whole
discipline has been not overclaiming what the data or the pipeline can support — the same
standard applies to this file's own claims about itself. See `docs/DECISION_LOG.md`'s Phase 5
entry for the full account of what was and wasn't possible to verify, and why.

## Data source

Every table is Import-mode, sourced directly from the PostgreSQL `analytics` schema via the
`PostgreSQL.Database(PGServer, PGDatabase)` connector — never from a CSV, never from `staging`
or `clean`. `PGServer`/`PGDatabase` are Power BI parameters (edit via `Transform Data > Edit
Parameters`, no file editing needed). Full architecture: `docs/POWER_BI_SPEC.md` §1.

## Also see

- [`docs/POWER_BI_SPEC.md`](../docs/POWER_BI_SPEC.md) — the approved design this implements
- [`docs/DASHBOARD_STORY.md`](../docs/DASHBOARD_STORY.md) — the narrative behind the page order
- [`BUILD_GUIDE.md`](BUILD_GUIDE.md) — the manual finishing steps
- [`../dashboard/prototype.html`](../dashboard/prototype.html) — a live, interactive HTML
  mockup of all 4 pages (real embedded data, not a Power BI artifact) for design review without
  needing Power BI Desktop at all
