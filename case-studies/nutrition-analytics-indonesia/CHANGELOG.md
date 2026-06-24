# Changelog

All notable changes to this project are documented in this file. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

Nothing yet. Phase 1 (cleaning) has not started.

## [0.1.0] — Phase 0: Data Foundation, Governance & Real Dataset Acquisition

### Added
- Repository scaffold (`config/`, `data/`, `docs/`, `notebooks/`, `src/`, `tests/`,
  `reports/`, `dashboard/`) matching the project's required layout.
- Per-dataset YAML data contracts (`docs/data_contracts/`) and a generic validator
  (`src/validation/contracts.py`) enforced before any fetch is marked successful.
- Province reference layer (`src/reference/`) standardizing all province names
  against a live BPS statistical variable's region list (38 provinces).
- Config-driven BPS ingestion (`config/datasets.yml` + `src/ingestion/
  fetch_bps_dataset.py`) covering poverty, IPM, population, education, and
  expenditure, with real, queried (not guessed) variable ids.
- Dedicated ingestion scripts for stunting (`fetch_stunting_ssgi.py`, manual
  Tableau crosstab export) and province boundaries (`fetch_geo_boundaries.py`,
  GADM by default, BIG as an optional manual upgrade).
- `src/ingestion/run_all.py` orchestrator running all ingestion steps unattended.
- `src/ingestion/discover_bps_vars.py` for finding and confirming real BPS
  variable ids without guessing.
- Checksummed, append-only manifest (`data/raw/_manifest.jsonl`) and generated
  `docs/data_inventory.md`.
- `docs/known_limitations.md` documenting every structural limitation and the
  alternatives investigated and rejected for each.
- CI: `.github/workflows/tests.yml` (pytest on every push/PR) and
  `.github/workflows/validate.yml` (contract validation).
- Test suite (`tests/`, 18 tests, no real network calls): BPS client error
  handling, manifest schema, data contract validation, province standardization.
- `Makefile` (`install`, `fetch`, `validate`, `inventory`, `test`).

### Fixed
- `discover_bps_vars.py` returning 0 results for every search: BPS's var-list
  endpoint paginates at a fixed 10 results/page regardless of `per_page`; the
  original script never paginated past page 1. Fixed by looping all pages.
- BPS dynamic-table parsing returning 0 rows against real data: the original
  parser split composite `datacontent` keys by substring position, which doesn't
  work (digit widths vary per dataset, undocumented). Fixed by constructing
  expected keys from known dimension values instead.
- Province reference layer sourced from BPS's `/domain/type/prov/` metadata
  endpoint, which returns a stale 34-province scheme missing the 2022 Papua
  splits. Fixed by sourcing from a live statistical variable's region list.
- `run_validation.py` failed to load `.geojson` files (only handled `.csv`/`.json`).
- `run_all.py` always attempted the (confirmed-broken) automated stunting scrape
  by default; now looks for a manual export at the conventional path first.

### Removed
- `TableauScraper` from `requirements.txt` — unmaintained, confirmed broken
  against the dashboard's current frontend. Automated-scrape code path remains,
  imported lazily, not a default dependency.

### Known limitations
See `docs/known_limitations.md`: GADM province-vintage gap (34 vs. 38), stunting's
lack of a scriptable source, and the education dataset's single-age-band scope
decision.
