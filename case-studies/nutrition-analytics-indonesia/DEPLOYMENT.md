# Deployment

The dashboard reads only from the committed snapshot in `dashboard/data/`
(built by `dashboard/prepare_data.py` from real, already-validated pipeline
output). This is a deliberate design choice: **viewing the dashboard never
requires a `BPS_API_KEY`, a BPS WebAPI call, or repeating the manual stunting
export** — those are only needed to *regenerate* the underlying analysis, not
to view its results. `data/raw/` and `data/processed/` stay gitignored, per
this project's standing reproducibility rules (always re-fetched/recomputed,
never committed); `dashboard/data/` is the one deliberate, documented exception.

## Local deployment

```bash
git clone <repo-url>
cd nutrition-analytics-indonesia
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run dashboard/Home.py
```

Opens at `http://localhost:8501`. No API keys, no data fetching, no pipeline
run required — `dashboard/data/` ships with the repository.

## Streamlit Community Cloud deployment

1. Push this repository to GitHub (public or private with Streamlit Cloud
   access granted).
2. At [share.streamlit.io](https://share.streamlit.io), create a new app:
   - **Repository:** this repo
   - **Branch:** `main`
   - **Main file path:** `dashboard/Home.py`
3. No secrets need to be configured — the dashboard does not call any external
   API or require `BPS_API_KEY`.
4. Streamlit Cloud installs from `requirements.txt` automatically. Note its
   size: this project's full dependency list includes `geopandas`,
   `scikit-learn`, and other heavier packages needed for the *analysis*
   pipeline, not just the dashboard — install time will be a few minutes on
   first deploy.

## Reproducing the full analysis (not required to view the dashboard)

Only needed if you want to regenerate `dashboard/data/` from scratch — e.g.
after a methodology change or a new year's data:

```bash
make install
cp .env.example .env
# Sign up free at https://webapi.bps.go.id/, paste the App ID into .env as BPS_API_KEY
make fetch                          # 6 of 7 datasets, fully scripted
# Manually export the stunting crosstab (docs/known_limitations.md §3) to
# data/external/stunting_tableau_crosstab_2024.xlsx, then:
python -m src.ingestion.fetch_stunting_ssgi --manual-xlsx data/external/stunting_tableau_crosstab_2024.xlsx
make clean-data                     # build the merged analytical table
make rankings                       # build data/processed/npi_rankings.csv
make fetch-boundaries                # ~500MB raw download, real distinct 38-province geometry
make spatial                        # build data/processed/npi_spatial.geojson + spatial diagnostics
python -m dashboard.prepare_data    # refresh dashboard/data/ from the real pipeline output
python -m dashboard.generate_diagrams  # regenerate reports/portfolio_assets/*.png if needed
make test                           # 67 tests, no network calls
```

Full step-by-step detail, including why each manual step exists, is in
[README.md](README.md) and [docs/known_limitations.md](docs/known_limitations.md).

## What's committed vs. regenerated

| Committed (in git) | Regenerated (gitignored) |
|---|---|
| `dashboard/data/` — presentation snapshot | `data/raw/` — every fetched source file |
| `reports/maps/`, `reports/portfolio_assets/` — generated figures | `data/processed/` — merged tables, rankings, spatial dataset |
| `src/`, `tests/`, `docs/`, `config/` — all code and documentation | `.env` — your local API key (never committed) |

## Known deployment constraints

- The full analysis pipeline's dependencies (`geopandas`, `libpysal`, `esda`,
  `scikit-learn`) are heavier than a typical Streamlit app needs just to serve
  pre-computed data. If deployment speed becomes a concern, a future
  `dashboard/requirements.txt` scoped to only `streamlit`, `pandas`,
  `geopandas`, and `plotly` (the dashboard's actual runtime dependencies) would
  install faster — not done in this phase, to avoid maintaining two
  dependency lists that can drift.
- `dashboard/data/npi_spatial.geojson` is a coarser geometry simplification
  (tolerance 0.01°) than the analysis-grade file in `data/processed/`
  (tolerance 0.001°) — appropriate for a web map, not for re-running spatial
  statistics against.
