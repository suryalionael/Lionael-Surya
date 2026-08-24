# Dashboard Prototype

`prototype.html` — a self-contained, interactive HTML mockup of all 4 approved dashboard pages
(Overview, Where, When & Who, Methodology), built for design review without requiring Power BI
Desktop. Open it directly in any browser — no server, no dependencies.

**This is a design-review prototype, not the production deliverable.** The real, importable
Power BI Project is in [`../powerbi/`](../powerbi/). This file exists because Power BI Desktop
is Windows-only and wasn't available to verify visually during the build (see
`docs/DECISION_LOG.md`'s Phase 5 entry) — this prototype is how the dashboard's actual visual
design, data, and interaction were verified instead.

**The data is real, not illustrative.** Every number is a live snapshot pulled directly from
the project's PostgreSQL `analytics` schema on 2026-08-23 (the same views the Power BI project
consumes), embedded as static JSON — reconciled against fresh SQL queries in
`tests/test_phase5_reconciliation.py`. It will not update itself; re-run the export described
in `docs/DECISION_LOG.md` to refresh it against a later pipeline run.

All of Phase 4's approved design is preserved: the KPI cards, the raw-count-vs-density
neighbourhood contrast (Page 2), the hour × weekday heatmap (Page 3), the four-page structure,
the point-of-use captions on the relative-exposure table, and the full methodology page with
its warning box. See [`../docs/DASHBOARD_STORY.md`](../docs/DASHBOARD_STORY.md) for the
narrative and [`../docs/POWER_BI_SPEC.md`](../docs/POWER_BI_SPEC.md) for the per-visual spec
this prototype implements.
